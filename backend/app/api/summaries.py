from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response

from app.core.auth import CurrentUser, get_current_user
from app.core.db import db_for
from app.schemas.summaries import SummaryCreate
from app.services.pdf_export import build_summary_pdf
from app.services.summarize import summarize_document

router = APIRouter()


@router.post("/documents/{document_id}/summaries")
def create_summary(
    document_id: str,
    body: SummaryCreate,
    user: Annotated[CurrentUser, Depends(get_current_user)],
):
    db = db_for(user)
    rows = db.get(
        "documents",
        {
            "id": f"eq.{document_id}",
            "user_id": f"eq.{user.user_id}",
            "select": "*",
        },
    )
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")
    document = rows[0]
    if document.get("status") != "ready" or not document.get("extracted_text"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=document.get("error_message") or "This document has no text to summarize.",
        )

    result = summarize_document(document["extracted_text"], body.mode)
    saved = db.upsert(
        "summaries",
        {
            "document_id": document_id,
            "user_id": user.user_id,
            "mode": body.mode,
            "summary_text": result["summary"],
            "key_points": result["key_points"],
            "model": result["model"],
        },
    )
    return saved


@router.get("/summaries/{summary_id}/pdf")
def download_summary_pdf(
    summary_id: str,
    user: Annotated[CurrentUser, Depends(get_current_user)],
):
    db = db_for(user)
    rows = db.get(
        "summaries",
        {
            "id": f"eq.{summary_id}",
            "user_id": f"eq.{user.user_id}",
            "select": "*,documents(original_filename)",
        },
    )
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Summary not found.")
    summary = rows[0]
    nested = summary.get("documents") or {}
    filename = nested.get("original_filename") if isinstance(nested, dict) else "document"
    key_points = summary.get("key_points") or []
    if isinstance(key_points, str):
        key_points = [key_points]
    pdf_bytes = build_summary_pdf(
        filename=filename or "document",
        created_at=str(summary.get("created_at") or ""),
        mode=str(summary.get("mode") or ""),
        summary=str(summary.get("summary_text") or ""),
        key_points=[str(item) for item in key_points],
    )
    download_name = f"{(filename or 'summary').rsplit('.', 1)[0]}-{summary.get('mode')}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{download_name}"'},
    )
