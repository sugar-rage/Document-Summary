import shutil
from io import BytesIO
from pathlib import Path

import fitz
import pytesseract
from fastapi import HTTPException, status
from PIL import Image, UnidentifiedImageError

from app.core.config import settings
from app.utils.text import normalize_text


def is_tesseract_available() -> bool:
    """Check if tesseract executable is available in the system PATH."""
    return shutil.which("tesseract") is not None or shutil.which("tesseract.exe") is not None


def ocr_image(path: Path) -> str:
    if not is_tesseract_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OCR is not available. Tesseract OCR is not installed or not found on PATH in the server environment.",
        )

    try:
        with Image.open(path) as image:
            image = image.convert("RGB")
            text = pytesseract.image_to_string(image, lang="eng")
    except UnidentifiedImageError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The image could not be opened. It may be corrupted.",
        ) from exc
    except pytesseract.TesseractNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OCR is not available. Tesseract OCR is not installed or not found on PATH in the server environment.",
        ) from exc
    except pytesseract.TesseractError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="OCR failed while reading the image.",
        ) from exc
    return normalize_text(text)


def ocr_pdf(path: Path, max_pages: int | None = None) -> tuple[str, int]:
    if not is_tesseract_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OCR is not available. Tesseract OCR is not installed or not found on PATH in the server environment.",
        )

    max_pages = max_pages or settings.max_pdf_pages
    try:
        document = fitz.open(path)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The PDF could not be opened. It may be corrupted.",
        ) from exc

    parts: list[str] = []
    try:
        page_count = document.page_count
        limit = min(page_count, max_pages)
        for index in range(limit):
            page = document.load_page(index)
            pixmap = page.get_pixmap(dpi=150)
            png_bytes = pixmap.tobytes("png")
            with Image.open(BytesIO(png_bytes)) as image:
                try:
                    text = pytesseract.image_to_string(image.convert("RGB"), lang="eng")
                except pytesseract.TesseractNotFoundError as exc:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail="OCR is not available. Tesseract OCR is not installed or not found on PATH in the server environment.",
                    ) from exc
                except pytesseract.TesseractError as exc:
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail="OCR failed while reading a PDF page.",
                    ) from exc
                parts.append(text)
        return normalize_text("\n\n".join(parts)), page_count
    finally:
        document.close()

