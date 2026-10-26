import argparse
import json
import logging
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import fitz

logger = logging.getLogger(__name__)



@dataclass
class TextBlock:
	text: str
	bbox: List[float]  
	block_no: int


@dataclass
class ImageInfo:
	image_index: int
	xref: int
	file_path: str
	ext: str
	width: int
	height: int
	bbox: Optional[List[float]]


@dataclass
class PageData:
	page_number: int
	page_label: Optional[str]
	printed_page_number: Optional[int]
	width: float
	height: float
	text: str
	blocks: List[TextBlock] = field(default_factory=list)
	images: List[ImageInfo] = field(default_factory=list)
	ocr_used: bool = False


@dataclass
class ParsedDocument:
	source: str
	total_pages: int
	metadata: Dict[str, str]
	pages: List[PageData] = field(default_factory=list)

	def to_dict(self) -> dict:
		return asdict(self)

	def full_text(self, with_page_markers: bool = True) -> str:
		parts = []
		for p in self.pages:
			if with_page_markers:
				parts.append(f"\n--- Page {p.page_number} ---\n{p.text}")
			else:
				parts.append(p.text)
		return "\n".join(parts).strip()

	def save_json(self, path: str | Path) -> Path:
		path = Path(path)
		path.parent.mkdir(parents=True, exist_ok=True)
		path.write_text(
			json.dumps(self.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8"
		)
		return path


class PDFParser:

	_PAGE_NUM_PATTERNS = [
		re.compile(r"^\s*(?:page|pg\.?|p\.?)?\s*(\d{1,4})\s*(?:of|/)\s*\d{1,4}\s*$", re.I),
		re.compile(r"^\s*(?:page|pg\.?|p\.?)\s*(\d{1,4})\s*$", re.I),
		re.compile(r"^\s*[-–—]\s*(\d{1,4})\s*[-–—]\s*$"),
		re.compile(r"^\s*(\d{1,4})\s*$"),
	]

	def __init__(
			self,
			pdf_path: str | Path,
			output_dir: str | Path = "pdf_output",
			extract_images: bool = True,
			min_image_size: int = 50,
			use_ocr: bool = False,
			ocr_dpi: int = 300,
			ocr_lang: str = "eng",
			margin_ratio: float = 0.10,
			password: Optional[str] = None,
	):
		self.pdf_path = Path(pdf_path)
		if not self.pdf_path.exists():
			raise FileNotFoundError(f"PDF not found: {self.pdf_path}")

		self.output_dir = Path(output_dir)
		self.images_dir = self.output_dir / "images"
		self.extract_images = extract_images
		self.min_image_size = min_image_size
		self.use_ocr = use_ocr
		self.ocr_dpi = ocr_dpi
		self.ocr_lang = ocr_lang
		self.margin_ratio = margin_ratio
		self.password = password


	def parse(self) -> ParsedDocument:
		doc = fitz.open(self.pdf_path)
		try:
			if doc.needs_pass:
				if not self.password or not doc.authenticate(self.password):
					raise ValueError("PDF is encrypted and the password is missing or wrong.")

			if self.extract_images:
				self.images_dir.mkdir(parents=True, exist_ok=True)

			parsed = ParsedDocument(
				source=str(self.pdf_path),
				total_pages=doc.page_count,
				metadata={k: v for k, v in (doc.metadata or {}).items() if v},
			)

			for index in range(doc.page_count):
				try:
					parsed.pages.append(self._parse_page(doc, index))
				except Exception as exc:  # keep going if one page is broken
					logger.exception("Failed to parse page %d: %s", index + 1, exc)
					parsed.pages.append(
						PageData(
							page_number=index + 1,
							page_label=None,
							printed_page_number=None,
							width=0.0,
							height=0.0,
							text="",
						)
					)
			return parsed
		finally:
			doc.close()


	def _parse_page(self, doc: fitz.Document, index: int) -> PageData:
		page = doc[index]
		page_number = index + 1
		rect = page.rect

		blocks = self._extract_blocks(page)
		text = "\n".join(b.text for b in blocks).strip()

		ocr_used = False
		if not text and self.use_ocr:
			text = self._ocr_page(page)
			ocr_used = bool(text)

		images = self._extract_images(doc, page, page_number) if self.extract_images else []

		return PageData(
			page_number=page_number,
			page_label=self._get_page_label(page),
			printed_page_number=self._detect_printed_page_number(blocks, rect.height),
			width=round(rect.width, 2),
			height=round(rect.height, 2),
			text=text,
			blocks=blocks,
			images=images,
			ocr_used=ocr_used,
		)


	@staticmethod
	def _extract_blocks(page: fitz.Page) -> List[TextBlock]:

		raw = page.get_text("blocks", sort=True)
		blocks: List[TextBlock] = []
		for b in raw:

			if len(b) >= 7 and b[6] != 0:
				continue
			content = (b[4] or "").strip()
			if not content:
				continue
			blocks.append(
				TextBlock(
					text=content,
					bbox=[round(float(v), 2) for v in b[:4]],
					block_no=int(b[5]),
				)
			)
		return blocks

	def _ocr_page(self, page: fitz.Page) -> str:

		try:
			import io

			import pytesseract
			from PIL import Image
		except ImportError:
			logger.warning("OCR requested but pytesseract/Pillow are not installed.")
			return ""

		pix = page.get_pixmap(dpi=self.ocr_dpi)
		img = Image.open(io.BytesIO(pix.tobytes("png")))
		return pytesseract.image_to_string(img, lang=self.ocr_lang).strip()


	@staticmethod
	def _get_page_label(page: fitz.Page) -> Optional[str]:

		try:
			label = page.get_label()
			return label or None
		except Exception:
			return None

	def _detect_printed_page_number(
			self, blocks: List[TextBlock], page_height: float
	) -> Optional[int]:

		if not blocks or page_height <= 0:
			return None

		top_limit = page_height * self.margin_ratio
		bottom_limit = page_height * (1 - self.margin_ratio)

		footer = [b for b in blocks if b.bbox[1] >= bottom_limit]
		header = [b for b in blocks if b.bbox[3] <= top_limit]


		footer.sort(key=lambda b: b.bbox[1], reverse=True)
		header.sort(key=lambda b: b.bbox[1])

		for block in footer + header:
			for line in reversed(block.text.splitlines()):
				number = self._match_page_number(line)
				if number is not None:
					return number
		return None

	def _match_page_number(self, line: str) -> Optional[int]:
		line = line.strip()
		if not line or len(line) > 25:
			return None
		for pattern in self._PAGE_NUM_PATTERNS:
			m = pattern.match(line)
			if m:
				return int(m.group(1))
		return None

	def _extract_images(
			self, doc: fitz.Document, page: fitz.Page, page_number: int
	) -> List[ImageInfo]:
		results: List[ImageInfo] = []
		seen_xrefs = set()

		for img_index, img in enumerate(page.get_images(full=True)):
			xref = img[0]
			if xref in seen_xrefs:
				continue
			seen_xrefs.add(xref)

			try:
				saved = self._save_image(doc, xref, page_number, img_index)
			except Exception as exc:
				logger.warning("Page %d: could not extract image xref=%s (%s)", page_number, xref, exc)
				continue

			if saved is None:
				continue
			file_path, ext, width, height = saved

			bbox = None
			try:
				rects = page.get_image_rects(xref)
				if rects:
					bbox = [round(float(v), 2) for v in (rects[0].x0, rects[0].y0, rects[0].x1, rects[0].y1)]
			except Exception:
				pass

			results.append(
				ImageInfo(
					image_index=img_index,
					xref=xref,
					file_path=str(file_path),
					ext=ext,
					width=width,
					height=height,
					bbox=bbox,
				)
			)
		return results

	def _save_image(self, doc: fitz.Document, xref: int, page_number: int, img_index: int):

		info = doc.extract_image(xref)
		if not info:
			return None

		width, height = info.get("width", 0), info.get("height", 0)
		if width < self.min_image_size or height < self.min_image_size:
			return None

		ext = info.get("ext", "png").lower()
		stem = f"page{page_number:04d}_img{img_index:02d}"


		if ext in ("png", "jpeg", "jpg") and not info.get("smask"):
			path = self.images_dir / f"{stem}.{ext}"
			path.write_bytes(info["image"])
			return path, ext, width, height

		pix = fitz.Pixmap(doc, xref)
		if info.get("smask"):
			mask = fitz.Pixmap(doc, info["smask"])
			pix = fitz.Pixmap(pix, mask)
		if pix.colorspace and pix.colorspace.n > 3:
			pix = fitz.Pixmap(fitz.csRGB, pix)
		path = self.images_dir / f"{stem}.png"
		pix.save(path)
		return path, "png", pix.width, pix.height

def parse_pdf(pdf_path: str, output_dir: str = "pdf_output", **kwargs) -> ParsedDocument:
	"""One-liner: parse_pdf('file.pdf') -> ParsedDocument"""
	return PDFParser(pdf_path, output_dir=output_dir, **kwargs).parse()


#
def main() -> None:
	ap = argparse.ArgumentParser(description="Extract text, images and page numbers from a PDF.")
	ap.add_argument("pdf", help="Path to the PDF file")
	ap.add_argument("--out", default="pdf_output", help="Output directory (default: pdf_output)")
	ap.add_argument("--no-images", action="store_true", help="Skip image extraction")
	ap.add_argument("--min-image-size", type=int, default=50, help="Min image width/height in px")
	ap.add_argument("--ocr", action="store_true", help="OCR pages that have no text layer")
	ap.add_argument("--password", default=None, help="Password for encrypted PDFs")
	args = ap.parse_args()

	logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

	parser = PDFParser(
		args.pdf,
		output_dir=args.out,
		extract_images=not args.no_images,
		min_image_size=args.min_image_size,
		use_ocr=args.ocr,
		password=args.password,
	)
	result = parser.parse()

	out_dir = Path(args.out)
	json_path = result.save_json(out_dir / "parsed.json")
	(out_dir / "full_text.txt").write_text(result.full_text(), encoding="utf-8")

	print(f"\nParsed {result.total_pages} pages from {args.pdf}")
	print(f"{'Page':>5} {'Label':>8} {'Printed':>8} {'Chars':>8} {'Images':>7}")
	for p in result.pages:
		print(
			f"{p.page_number:>5} {str(p.page_label or '-'):>8} "
			f"{str(p.printed_page_number or '-'):>8} {len(p.text):>8} {len(p.images):>7}"
		)
	print(f"\nJSON : {json_path}")
	print(f"Text : {out_dir / 'full_text.txt'}")
	if not args.no_images:
		print(f"Images: {parser.images_dir}")


if __name__ == "__main__":
	main()
