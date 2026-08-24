from __future__ import annotations

from dataclasses import dataclass

from fastapi import HTTPException, status

ALLOWED_TYPES = {
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
}

SIGNATURES = {
    "application/pdf": (b"%PDF",),
    "image/png": (b"\x89PNG\r\n\x1a\n",),
    "image/jpeg": (b"\xff\xd8\xff",),
}


class FileValidationError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


@dataclass
class ValidatedFile:
    filename: str
    content_type: str
    size: int
    data: bytes
    extension: str


def _extension(filename: str) -> str:
    name = filename.lower().strip()
    if "." not in name:
        return ""
    return "." + name.rsplit(".", 1)[-1]


def validate_upload(
    filename: str | None,
    declared_type: str | None,
    data: bytes,
    max_bytes: int,
) -> ValidatedFile:
    if not filename or not filename.strip():
        raise FileValidationError("A file name is required.")

    ext = _extension(filename)
    if ext not in ALLOWED_TYPES:
        raise FileValidationError(
            "Unsupported file type. Upload a PDF, PNG, JPG, or JPEG.",
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        )

    if not data:
        raise FileValidationError("The file is empty.")

    size = len(data)
    if size > max_bytes:
        raise FileValidationError(
            f"File is too large. Maximum size is {max_bytes // (1024 * 1024)} MB.",
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        )

    expected = ALLOWED_TYPES[ext]
    if declared_type:
        declared = declared_type.split(";")[0].strip().lower()
        if declared not in {"application/octet-stream", ""} and declared != expected:
            # Some browsers send empty or generic types; only reject clear mismatches.
            if declared in ALLOWED_TYPES.values() and declared != expected:
                raise FileValidationError(
                    "File extension does not match the file contents type.",
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                )

    matched = False
    for content_type, prefixes in SIGNATURES.items():
        if any(data.startswith(prefix) for prefix in prefixes):
            if content_type != expected:
                raise FileValidationError(
                    "File content does not match the file extension.",
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                )
            matched = True
            break
    if not matched:
        raise FileValidationError(
            "Could not recognize this as a valid PDF or image.",
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        )

    return ValidatedFile(
        filename=filename.strip(),
        content_type=expected,
        size=size,
        data=data,
        extension=ext,
    )


def http_error(exc: FileValidationError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail=exc.message)
