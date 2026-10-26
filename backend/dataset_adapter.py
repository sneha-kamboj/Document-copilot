import ast
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class DatasetQuestion:
    doc_id: str
    question: str
    answer: str
    evidence_pages: list[int]
    evidence_sources: list[str]
    answer_format: str


class DatasetAdapter:
    def __init__(
        self,
        questions_path: str | Path,
        documents_dir: str | Path,
    ):
        self.questions_path = Path(questions_path)
        self.documents_dir = Path(documents_dir)

    @staticmethod
    def _parse_list(value) -> list:
        """Convert list-like strings into actual Python lists."""
        if isinstance(value, list):
            return value

        if not value:
            return []

        try:
            result = ast.literal_eval(value)
            return result if isinstance(result, list) else []
        except (ValueError, SyntaxError):
            return []

    def load_questions(self, limit: int | None = None) -> list[DatasetQuestion]:
        """Load questions and their reference metadata."""
        if not self.questions_path.is_file():
            raise FileNotFoundError(
                f"Questions file not found: {self.questions_path.resolve()}"
            )

        with self.questions_path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if isinstance(data, dict):
            data = data.get("data", data.get("questions", [data]))

        if not isinstance(data, list):
            raise ValueError("Expected a JSON list of question records.")

        questions = []

        for item in data:
            questions.append(
                DatasetQuestion(
                    doc_id=item["doc_id"],
                    question=item["question"],
                    answer=str(item["answer"]),
                    evidence_pages=self._parse_list(
                        item.get("evidence_pages", [])
                    ),
                    evidence_sources=self._parse_list(
                        item.get("evidence_sources", [])
                    ),
                    answer_format=item.get("answer_format", "String"),
                )
            )

            if limit is not None and len(questions) >= limit:
                break

        return questions

    def load_docs(self, limit: int | None = None) -> list[dict]:
        """Find PDF documents and return their IDs and paths."""
        if not self.documents_dir.is_dir():
            raise FileNotFoundError(
                f"Documents directory not found: "
                f"{self.documents_dir.resolve()}"
            )

        documents = sorted(self.documents_dir.rglob("*.pdf"))

        if limit is not None:
            documents = documents[:limit]

        return [
            {
                "doc_id": pdf.name,
                "path": pdf,
            }
            for pdf in documents
        ]
