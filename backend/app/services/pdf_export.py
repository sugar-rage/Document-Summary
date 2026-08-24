from io import BytesIO

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import ListFlowable, ListItem, Paragraph, SimpleDocTemplate, Spacer


def build_summary_pdf(
    *,
    filename: str,
    created_at: str,
    mode: str,
    summary: str,
    key_points: list[str],
) -> bytes:
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.85 * inch,
        rightMargin=0.85 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        title="Document Summary Assistant",
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleCustom",
        parent=styles["Title"],
        fontSize=16,
        spaceAfter=12,
    )
    heading = ParagraphStyle(
        "HeadingCustom",
        parent=styles["Heading2"],
        fontSize=12,
        spaceBefore=10,
        spaceAfter=6,
    )
    body = ParagraphStyle(
        "BodyCustom",
        parent=styles["BodyText"],
        fontSize=10,
        leading=14,
        spaceAfter=8,
    )
    meta = ParagraphStyle(
        "MetaCustom",
        parent=styles["BodyText"],
        fontSize=10,
        leading=13,
        spaceAfter=4,
    )

    def esc(value: str) -> str:
        return (
            (value or "")
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\n", "<br/>")
        )

    story = [
        Paragraph("Document Summary Assistant", title_style),
        Paragraph(f"<b>Original file:</b> {esc(filename)}", meta),
        Paragraph(f"<b>Date:</b> {esc(created_at)}", meta),
        Paragraph(f"<b>Summary length:</b> {esc(mode.title())}", meta),
        Spacer(1, 8),
        Paragraph("Summary", heading),
        Paragraph(esc(summary) or "No summary.", body),
        Paragraph("Key points", heading),
    ]
    items = [
        ListItem(Paragraph(esc(point), body))
        for point in key_points
        if point.strip()
    ]
    if items:
        story.append(ListFlowable(items, bulletType="bullet", leftIndent=16))
    else:
        story.append(Paragraph("No key points.", body))

    document.build(story)
    return buffer.getvalue()
