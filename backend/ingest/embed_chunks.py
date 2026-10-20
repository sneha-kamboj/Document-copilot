import argparse

from sqlalchemy import delete, func, select

from app.database.models import DocumentChunk, SourceDocument
from app.database.database import SessionLocal
from app.retrieval.embeddings import embed_texts
from ingest.chunker import chunk_blocks
from ingest.html_parser import Block

BATCH = 64


def _markdown_to_blocks(md: str) -> list[Block]:

    blocks: list[Block] = []
    page = 1
    for part in md.split("\n\n"):
        part = part.strip()
        if not part:
            continue
        if part.startswith("<!-- page "):
            page = int(part.removeprefix("<!-- page ").removesuffix(" -->"))
        elif part.startswith("#"):
            blocks.append(Block("heading", part.lstrip("# ").strip(), page, len(part) - len(part.lstrip("#"))))
        elif part.startswith("|"):
            blocks.append(Block("table", part, page))
        else:
            blocks.append(Block("paragraph", part, page))
    return blocks


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit-docs", type=int, default=None)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    with SessionLocal() as db:
        docs = db.scalars(select(SourceDocument).order_by(SourceDocument.ticker, SourceDocument.fiscal_year)).all()
        done = 0
        for doc in docs:
            if args.limit_docs is not None and done >= args.limit_docs:
                break
            existing = db.scalar(select(func.count()).select_from(DocumentChunk).where(DocumentChunk.document_id == doc.id))
            if existing and not args.force:
                print(f"skip  {doc.ticker} FY{doc.fiscal_year} ({existing} chunks exist)")
                continue
            if existing:
                db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == doc.id))
                db.commit()

            label = f"{doc.company_name} {doc.form_type} FY{doc.fiscal_year}"
            chunks = chunk_blocks(_markdown_to_blocks(doc.markdown), label)
            print(f"embed {label}: {len(chunks)} chunks")
            for i in range(0, len(chunks), BATCH):
                batch = chunks[i : i + BATCH]
                vectors = embed_texts([c.text for c in batch])
                db.add_all(
                    DocumentChunk(
                        document_id=doc.id,
                        chunk_index=c.index,
                        page_number=c.page,
                        section=c.section,
                        is_table=c.is_table,
                        text=c.text,
                        token_count=c.token_count,
                        embedding=v,
                    )
                    for c, v in zip(batch, vectors, strict=True)
                )
                db.commit()
            done += 1
    print("done")


if __name__ == "__main__":
    main()
