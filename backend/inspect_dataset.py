import json
from collections import Counter

from huggingface_hub import HfApi, hf_hub_download


DATASET_ID = "yubo2333/MMLongBench-Doc"


def main():
	api = HfApi()


	info = api.dataset_info(DATASET_ID)
	print("ID      :", info.id)
	card = info.card_data.to_dict() if info.card_data else {}
	print("LICENSE :", card.get("license", "Not found in project"))
	print("TAGS    :", info.tags)


	files = api.list_repo_files(DATASET_ID, repo_type="dataset")
	print("\nFILES:")
	for f in files:
		print("  ", f)


	readme_path = hf_hub_download(DATASET_ID, "README.md", repo_type="dataset")
	print("\nREADME saved at:", readme_path)


	json_files = [f for f in files if f.endswith(".json") or f.endswith(".jsonl")]
	if not json_files:
		print("\n No json file Found")
		return

	path = hf_hub_download(DATASET_ID, json_files[0], repo_type="dataset")
	with open(path, encoding="utf-8") as fh:
		if path.endswith(".jsonl"):
			data = [json.loads(line) for line in fh if line.strip()]
		else:
			data = json.load(fh)

	print(f"\nQUESTIONS FILE: {json_files[0]}  ({len(data)} records)")
	print("FIELDS :", list(data[0].keys()))

	print("\nSAMPLE RECORD:")
	print(json.dumps(data[0], indent=2, ensure_ascii=False)[:1500])


	for key in ("answer_format", "evidence_sources", "doc_type"):
		if key in data[0]:
			print(f"\n{key} counts:")
			counter = Counter(str(d.get(key)) for d in data)
			for k, v in counter.most_common(10):
				print(f"   {k}: {v}")

	if "doc_id" in data[0]:
		print("\nUnique docs:", len({d["doc_id"] for d in data}))


if __name__ == "__main__":
	main()
