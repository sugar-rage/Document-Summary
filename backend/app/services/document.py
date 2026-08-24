from pathlib import Path

from app.core.config import settings
from app.services.extract import extract_pdf_text
from app.services.ocr import ocr_image, ocr_pdf
from app.utils.text import is_meaningful_text, normalize_text


def process_file(path: Path, content_type: str) -> tuple[str, str, int]:
    """Return (text, extraction_method, page_count)."""
    if content_type.startswith("image/"):
        text = ocr_image(path)
        return text, "ocr", 1

    text, page_count = extract_pdf_text(path)
    if is_meaningful_text(text, page_count):
        return _clip(text), "pymupdf", page_count

    try:
        ocr_text, page_count = ocr_pdf(path)
        if is_meaningful_text(ocr_text, page_count) or (
            ocr_text and len(ocr_text) > len(text)
        ):
            method = "hybrid" if text else "ocr"
            combined = ocr_text if len(ocr_text) >= len(text) else text
            return _clip(combined), method, page_count
    except Exception as exc:
        # If OCR fails or Tesseract is unavailable, but we have some extracted text from PyMuPDF
        if text and text.strip():
            return _clip(text), "pymupdf", page_count
        # If no text at all and OCR failed/unavailable, re-raise the exception
        raise exc

    if text:
        return _clip(text), "pymupdf", page_count
    return "", "ocr", page_count


def _clip(text: str) -> str:
    text = normalize_text(text)
    if len(text) > settings.max_extracted_chars:
        return text[: settings.max_extracted_chars]
    return text
