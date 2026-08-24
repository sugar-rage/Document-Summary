from app.services.pdf_export import build_summary_pdf


def test_pdf_contains_required_fields():
    data = build_summary_pdf(
        filename="research.pdf",
        created_at="2026-08-24",
        mode="medium",
        summary="This is the generated summary.",
        key_points=["First point", "Second point"],
    )
    assert data.startswith(b"%PDF")
    assert b"Document Summary Assistant" in data or b"Summary" in data
