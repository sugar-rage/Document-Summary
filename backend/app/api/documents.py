import tempfile
import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import Response

from app.core.auth import CurrentUser, get_current_user
from app.core.config import settings
from app.core.db import db_for
from app.services.document import process_file
from app.services.storage import storage_for
from app.services.validate import FileValidationError, http_error, validate_upload

router = APIRouter()


def _owned_document(db, user: CurrentUser, document_id: str) -> dict:
    rows = db.get(
        "documents",
        {
            "id": f"eq.{document_id}",
            "user_id": f"eq.{user.user_id}",
            "select": "*,summaries(*)",
        },
    )
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")
    return rows[0]


@router.post("")
def upload_document(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    file: Annotated[UploadFile, File()],
):
    db = db_for(user)
    raw = file.file.read()
    try:
        validated = validate_upload(
            file.filename, file.content_type, raw, settings.max_upload_bytes
        )
    except FileValidationError as exc:
        raise http_error(exc) from exc

    suffix = validated.extension
    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(validated.data)
            tmp_path = Path(tmp.name)

        text, method, page_count = process_file(tmp_path, validated.content_type)
        if not text:
            row = db.insert(
                "documents",
                {
                    "user_id": user.user_id,
                    "original_filename": validated.filename,
                    "content_type": validated.content_type,
                    "file_size_bytes": validated.size,
                    "extraction_method": method,
                    "extracted_text": "",
                    "page_count": page_count,
                    "status": "failed",
                    "error_message": "No extractable text was found.",
                },
            )
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No extractable text was found in this file.",
            )

        storage = storage_for(user)
        storage_rel_path = f"{user.user_id}/{uuid.uuid4().hex}{suffix}"
        storage.upload_file(storage_rel_path, validated.data, validated.content_type)

        row = db.insert(
            "documents",
            {
                "user_id": user.user_id,
                "original_filename": validated.filename,
                "content_type": validated.content_type,
                "file_size_bytes": validated.size,
                "storage_path": storage_rel_path,
                "extraction_method": method,
                "extracted_text": text,
                "page_count": page_count,
                "status": "ready",
                "error_message": None,
            },
        )
        return row
    finally:
        if tmp_path and tmp_path.exists():
            tmp_path.unlink(missing_ok=True)


@router.get("")
def list_documents(user: Annotated[CurrentUser, Depends(get_current_user)]):
    db = db_for(user)
    return db.get(
        "documents",
        {
            "user_id": f"eq.{user.user_id}",
            "select": "id,original_filename,content_type,file_size_bytes,storage_path,extraction_method,page_count,status,error_message,created_at,updated_at,summaries(id,mode,created_at,model)",
            "order": "created_at.desc",
        },
    )


@router.get("/{document_id}")
def get_document(
    document_id: str,
    user: Annotated[CurrentUser, Depends(get_current_user)],
):
    return _owned_document(db_for(user), user, document_id)


@router.get("/{document_id}/file")
def get_document_file(
    document_id: str,
    user: Annotated[CurrentUser, Depends(get_current_user)],
):
    db = db_for(user)
    doc = _owned_document(db, user, document_id)
    storage_path = doc.get("storage_path")
    if not storage_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Original document file is not available.",
        )

    storage = storage_for(user)
    file_bytes = storage.download_file(storage_path)

    filename = doc.get("original_filename") or "document.pdf"
    content_type = doc.get("content_type") or "application/pdf"
    return Response(
        content=file_bytes,
        media_type=content_type,
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )


@router.delete("/{document_id}")
def delete_document(
    document_id: str,
    user: Annotated[CurrentUser, Depends(get_current_user)],
):
    db = db_for(user)
    doc = _owned_document(db, user, document_id)
    db.delete("documents", {"id": f"eq.{document_id}", "user_id": f"eq.{user.user_id}"})
    storage_path = doc.get("storage_path")
    if storage_path:
        storage = storage_for(user)
        storage.delete_file(storage_path)
    return {"ok": True}
