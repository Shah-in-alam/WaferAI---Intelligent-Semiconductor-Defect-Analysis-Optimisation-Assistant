from __future__ import annotations

from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import BinaryIO, Union

from PIL import Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image as RLImage,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from .analyzer import DefectAnalysis


def build_pdf_report(
    output: Union[str, Path, BinaryIO],
    original: Image.Image,
    gradcam: Image.Image,
    defect_info: dict,
    analysis: DefectAnalysis,
) -> Union[Path, BinaryIO]:
    """Write a styled PDF report.

    `output` can be a filesystem path (str or Path) or any writable binary
    stream (e.g. BytesIO) — useful for serving the PDF inline without ever
    touching disk.
    """
    target: Union[str, BinaryIO]
    if isinstance(output, (str, Path)):
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        target = str(output_path)
    else:
        target = output

    doc = SimpleDocTemplate(
        target,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle", parent=styles["Title"], fontSize=20, textColor=colors.HexColor("#1F4E79")
    )
    h2_style = ParagraphStyle(
        "H2", parent=styles["Heading2"], textColor=colors.HexColor("#1F4E79")
    )

    story = []
    story.append(Paragraph("WaferAI — Defect Analysis Report", title_style))
    story.append(Spacer(1, 0.4 * cm))
    story.append(
        Paragraph(
            datetime.now().strftime("Generated %Y-%m-%d %H:%M:%S"),
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 0.6 * cm))

    summary_data = [
        ["Defect type", analysis.defect_type],
        ["Severity", analysis.severity],
        ["Estimated yield loss", analysis.estimated_yield_loss],
        ["Model confidence", f"{defect_info.get('model_confidence', 0):.1f}%"],
        ["Primary location", defect_info.get("location", "—")],
        ["Defect density", f"{defect_info.get('defect_density', 0)}%"],
    ]
    table = Table(summary_data, colWidths=[5 * cm, 10 * cm])
    table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#EAF2FA")),
            ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#1F4E79")),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("PADDING", (0, 0), (-1, -1), 6),
        ])
    )
    story.append(table)
    story.append(Spacer(1, 0.6 * cm))

    story.append(Paragraph("Wafer image and model attention", h2_style))
    img_table = Table(
        [[_image_flowable(original, 7 * cm), _image_flowable(gradcam, 7 * cm)]],
        colWidths=[8 * cm, 8 * cm],
    )
    story.append(img_table)
    story.append(Spacer(1, 0.6 * cm))

    story.append(Paragraph("Likely root causes", h2_style))
    for cause in analysis.root_causes:
        story.append(Paragraph(f"• {cause}", styles["Normal"]))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Immediate actions", h2_style))
    for action in analysis.immediate_actions:
        story.append(Paragraph(f"• {action}", styles["Normal"]))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Process improvements", h2_style))
    for improvement in analysis.process_improvements:
        story.append(Paragraph(f"• {improvement}", styles["Normal"]))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Quality impact", h2_style))
    story.append(Paragraph(analysis.quality_impact, styles["Normal"]))

    doc.build(story)
    return output if not isinstance(output, (str, Path)) else Path(output)


def _image_flowable(image: Image.Image, target_width: float) -> RLImage:
    buf = BytesIO()
    image.save(buf, format="PNG")
    buf.seek(0)
    ratio = image.size[1] / image.size[0]
    return RLImage(buf, width=target_width, height=target_width * ratio)
