from ingest.pdf_parser import load_documents


blocks = load_documents("data/eval/05-03-18-political-release.pdf")


for block in blocks:
	print(f"Page: {block.page} | Type: {block.kind}")
	print(block.text[:300])
	print("-" * 40)