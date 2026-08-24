from pathlib import Path

import fitz
from fastapi import HTTPException, status

from app.utils.text import normalize_text


def extract_pdf_text(path: Path) -> tuple[str, int]:
    try:
        document = fitz.open(path)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The PDF could not be opened. It may be corrupted.",
        ) from exc

    try:
        page_count = document.page_count
        parts: list[str] = []
        for page in document:
            parts.append(page.get_text("text") or "")
        return normalize_text("\n\n".join(parts)), page_count
    finally:
        document.close()
