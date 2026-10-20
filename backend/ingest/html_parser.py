import re
from dataclasses import dataclass

from bs4 import BeautifulSoup, NavigableString, Tag

BLOCK_TAGS = {"p", "div", "li", "h1", "h2", "h3", "h4", "h5", "h6", "table", "hr", "br"}
HEADING_TAGS = {"h1": 1, "h2": 2, "h3": 3, "h4": 4, "h5": 5, "h6": 6}
PAGE_BREAK = re.compile(r"page-break-(after|before)\s*:\s*always|break-(after|before)\s*:\s*page", re.IGNORECASE)


@dataclass
class Block:
    kind: str
    text: str
    page: int
    level: int = 0


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()


def _table_to_markdown(table: Tag) -> str:
    rows: list[list[str]] = []
    for tr in table.find_all("tr"):
        cells = [_clean(td.get_text(" ")) for td in tr.find_all(["td", "th"])]
        merged: list[str] = []
        for i, cell in enumerate(cells):
            if i == 0:
                merged.append(cell)
            elif cell in ("", "$"):
                continue
            elif cell in (")", "%", ")%") and merged or merged and merged[-1].endswith("("):
                merged[-1] += cell
            else:
                merged.append(cell)
        if not any(merged):
            continue
        if merged:
            rows.append(merged)
    if not rows:
        return ""
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]

    keep = [i for i in range(width) if any(r[i] for r in rows)]
    rows = [[r[i] for i in keep] for r in rows]
    header, body = rows[0], rows[1:]
    lines = ["| " + " | ".join(header) + " |", "| " + " | ".join(["---"] * len(header)) + " |"]
    lines += ["| " + " | ".join(r) + " |" for r in body]
    return "\n".join(lines)


def _has_page_break(tag: Tag) -> bool:
    return bool(PAGE_BREAK.search(tag.get("style", "") or ""))


def _is_heading_like(tag: Tag, text: str) -> bool:

    if len(text) > 120 or len(text) < 3:
        return False
    if re.match(r"^(part\s+[ivx]+|item\s+\d+[a-c]?\.?)\b", text, re.IGNORECASE):
        return True
    bold = tag.find(style=re.compile(r"font-weight\s*:\s*(bold|[6-9]00)", re.IGNORECASE)) or tag.find(["b", "strong"])
    return bool(bold) and len(_clean(bold.get_text(" "))) >= len(text) * 0.9 and not text.endswith(".")


def parse_html(html: str) -> tuple[list[Block], int]:
    soup = BeautifulSoup(html, "lxml")
    for t in soup(["script", "style", "head"]):
        t.decompose()
    # iXBRL hidden header block
    for t in soup.find_all(style=re.compile(r"display\s*:\s*none", re.IGNORECASE)):
        t.decompose()

    root = soup.body or soup
    blocks: list[Block] = []
    page = 1

    def walk(node: Tag) -> None:
        nonlocal page
        for child in node.children:
            if isinstance(child, NavigableString):
                continue
            if not isinstance(child, Tag):
                continue
            if _has_page_break(child):
                if child.name == "hr" or not child.get_text(strip=True):
                    page += 1
                    continue
            if child.name == "table":
                md = _table_to_markdown(child)
                if md:
                    blocks.append(Block("table", md, page))
                continue
            if child.name in HEADING_TAGS:
                text = _clean(child.get_text(" "))
                if text:
                    blocks.append(Block("heading", text, page, HEADING_TAGS[child.name]))
                continue
            has_block_children = any(
                isinstance(c, Tag) and (c.name in BLOCK_TAGS) for c in child.descendants
            )
            if has_block_children and child.name in {"div", "body", "html", "section", "ul", "ol", "font", "span"}:
                walk(child)
            else:
                text = _clean(child.get_text(" "))
                if text:
                    if _is_heading_like(child, text):
                        blocks.append(Block("heading", text, page, 2))
                    elif re.fullmatch(r"\d{1,3}", text):
                        continue  # bare page number
                    else:
                        blocks.append(Block("paragraph", text, page))
            if _has_page_break(child):
                page += 1

    walk(root)
    return blocks, page


def blocks_to_markdown(blocks: list[Block]) -> str:
    out: list[str] = []
    current_page = 0
    for b in blocks:
        if b.page != current_page:
            current_page = b.page
            out.append(f"<!-- page {current_page} -->")
        if b.kind == "heading":
            out.append("#" * max(1, min(b.level, 4)) + " " + b.text)
        else:
            out.append(b.text)
    return "\n\n".join(out)
