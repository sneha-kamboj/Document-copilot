import json
from datetime import date
from pathlib import Path

from sqlalchemy import select

from app.database.models import SourceDocument
from app.database.database import SessionLocal
from ingest.html_parser import blocks_to_markdown, parse_html

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
MANIFEST = DATA_DIR / "downloads" / "manifest.json"


def main() -> None:
    manifest = json.loads(MANIFEST.read_text())
    with SessionLocal() as db:
        for entry in manifest:
            filing_date = date.fromisoformat(entry["filing_date"])
            exists = db.scalar(
                select(SourceDocument.id).where(
                    SourceDocument.ticker == entry["ticker"],
                    SourceDocument.form_type == entry["form_type"],
                    SourceDocument.filing_date == filing_date,
                )
            )
            if exists:
                print(f"skip   {entry['ticker']} {entry['filing_date']} (already loaded)")
                continue
            html_path = DATA_DIR / "downloads" / entry["local_path"]
            blocks, pages = parse_html(html_path.read_text(encoding="utf-8", errors="ignore"))
            db.add(
                SourceDocument(
                    ticker=entry["ticker"],
                    company_name=entry["company_name"],
                    form_type=entry["form_type"],
                    fiscal_year=entry["fiscal_year"],
                    filing_date=filing_date,
                    source_url=entry["source_url"],
                    page_count=pages,
                    markdown=blocks_to_markdown(blocks),
                )
            )
            db.commit()
            print(f"loaded {entry['ticker']} FY{entry['fiscal_year']} ({pages} pages, {len(blocks)} blocks)")


if __name__ == "__main__":
    main()
