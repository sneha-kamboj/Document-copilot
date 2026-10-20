from dataclasses import dataclass

from ingest.html_parser import Block

MAX_CHARS = 3200
OVERLAP_CHARS = 300
CHARS_PER_TOKEN = 4


@dataclass
class Chunk:
    index: int
    text: str
    page: int
    section: str | None
    is_table: bool

    @property
    def token_count(self) -> int:
        return max(1, len(self.text) // CHARS_PER_TOKEN)


def _split_table(md: str, max_chars: int) -> list[str]:
    if len(md) <= max_chars:
        return [md]
    lines = md.split("\n")
    header, rows = lines[:2], lines[2:]
    parts, cur = [], list(header)
    for row in rows:
        if len("\n".join(cur + [row])) > max_chars and len(cur) > 2:
            parts.append("\n".join(cur))
            cur = list(header)
        cur.append(row)
    parts.append("\n".join(cur))
    return parts


def chunk_blocks(blocks: list[Block], doc_label: str) -> list[Chunk]:
    chunks: list[Chunk] = []
    section: str | None = None
    buf: list[str] = []
    buf_page = 1

    def flush() -> None:
        nonlocal buf
        text = "\n\n".join(buf).strip()
        if text:
            chunks.append(Chunk(len(chunks), f"[{doc_label} | {section or 'Preamble'}]\n{text}", buf_page, section, False))

        tail = text[-OVERLAP_CHARS:] if text else ""
        buf = [tail] if tail else []

    for b in blocks:
        if b.kind == "heading":
            flush()
            buf = []
            section = b.text[:500]
            buf_page = b.page
            continue
        if b.kind == "table":
            flush()
            buf = []
            for part in _split_table(b.text, MAX_CHARS):
                chunks.append(Chunk(len(chunks), f"[{doc_label} | {section or 'Preamble'} | table]\n{part}", b.page, section, True))
            buf_page = b.page
            continue
        if not buf:
            buf_page = b.page
        if sum(len(x) for x in buf) + len(b.text) > MAX_CHARS and buf:
            flush()
            buf_page = b.page
        # very long single paragraph: hard split
        text = b.text
        while len(text) > MAX_CHARS:
            buf.append(text[:MAX_CHARS])
            flush()
            text = text[MAX_CHARS - OVERLAP_CHARS :]
        buf.append(text)
    flush()
    return [c for c in chunks if len(c.text.strip()) > 80]
