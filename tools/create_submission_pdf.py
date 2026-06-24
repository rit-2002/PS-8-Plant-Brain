from pathlib import Path
import re

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "PS8_Hackathon_Submission.md"
OUTPUT = ROOT / "docs" / "PS8_Hackathon_Submission.pdf"


def clean(text: str) -> str:
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return text


def draw_header_footer(canvas, doc):
    canvas.saveState()
    width, height = A4
    canvas.setFillColor(colors.HexColor("#17202A"))
    canvas.rect(0, height - 0.42 * inch, width, 0.42 * inch, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 8)
    canvas.drawString(0.58 * inch, height - 0.27 * inch, "Plant Brain - PS-08 Hackathon Submission")
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(width - 0.58 * inch, height - 0.27 * inch, f"Page {doc.page}")
    canvas.setStrokeColor(colors.HexColor("#E8A23A"))
    canvas.setLineWidth(1.3)
    canvas.line(0, height - 0.43 * inch, width, height - 0.43 * inch)
    canvas.restoreState()


def build_styles():
    base = getSampleStyleSheet()
    base.add(
        ParagraphStyle(
            "SubmitTitle",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=28,
            leading=34,
            textColor=colors.HexColor("#17202A"),
            alignment=TA_CENTER,
            spaceAfter=18,
        )
    )
    base.add(
        ParagraphStyle(
            "SubmitSubtitle",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=12,
            leading=17,
            textColor=colors.HexColor("#4A5568"),
            alignment=TA_CENTER,
            spaceAfter=26,
        )
    )
    base.add(
        ParagraphStyle(
            "SubmitSection",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=19,
            textColor=colors.HexColor("#1B2631"),
            spaceBefore=12,
            spaceAfter=7,
        )
    )
    base.add(
        ParagraphStyle(
            "SubmitBody",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9.3,
            leading=13.2,
            textColor=colors.HexColor("#1F2933"),
            spaceAfter=6,
        )
    )
    base.add(
        ParagraphStyle(
            "SubmitBullet",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9.1,
            leading=12.8,
            leftIndent=14,
            firstLineIndent=-8,
            textColor=colors.HexColor("#1F2933"),
            spaceAfter=4,
        )
    )
    base.add(
        ParagraphStyle(
            "SubmitCode",
            parent=base["Code"],
            fontName="Courier",
            fontSize=8.2,
            leading=10.5,
            backColor=colors.HexColor("#F3F5F7"),
            borderPadding=5,
            spaceBefore=4,
            spaceAfter=6,
        )
    )
    return base


def architecture_table(styles):
    rows = [
        ["Document Sources", "sample_docs: work orders, SOPs, inspections, incidents, audits, CSV/TSV/PDF"],
        ["Ingestion", "FastAPI loads supported files and refreshes the indexed corpus"],
        ["Entity Extraction", "Equipment tags, document references, regulations, dates, and personnel"],
        ["Knowledge Graph", "NetworkX links documents to shared industrial entities"],
        ["Retrieval", "TF-IDF chunk retrieval for natural-language questions"],
        ["Copilot and Intelligence", "Cited answers, confidence, compliance gaps, maintenance RCA, lessons learned"],
        ["Frontend", "Graph visualization, chat UI, source documents, and intelligence panels"],
    ]
    table = Table(
        [[Paragraph(f"<b>{clean(a)}</b>", styles["SubmitBody"]), Paragraph(clean(b), styles["SubmitBody"])] for a, b in rows],
        colWidths=[1.75 * inch, 4.95 * inch],
        hAlign="LEFT",
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F8E8CF")),
                ("BACKGROUND", (1, 0), (1, -1), colors.HexColor("#F7F9FB")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CAD1D8")),
                ("INNERGRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#DDE3EA")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def parse_markdown(text: str, styles):
    story = []
    in_code = False
    code_lines = []
    skip_title = True

    for raw in text.splitlines():
        line = raw.rstrip()
        if line.strip().startswith("```"):
            in_code = not in_code
            if not in_code and code_lines:
                story.append(Paragraph(clean("\n".join(code_lines)).replace("\n", "<br/>"), styles["SubmitCode"]))
                code_lines = []
            continue
        if in_code:
            code_lines.append(line)
            continue
        if not line.strip():
            story.append(Spacer(1, 4))
            continue
        if line.startswith("# "):
            if skip_title:
                skip_title = False
                continue
            story.append(PageBreak())
            story.append(Paragraph(clean(line[2:]), styles["SubmitSection"]))
            continue
        if line.startswith("## "):
            title = line[3:].strip()
            if title == "Architecture":
                story.append(Paragraph(clean(title), styles["SubmitSection"]))
                story.append(architecture_table(styles))
                story.append(Spacer(1, 8))
            else:
                story.append(Paragraph(clean(title), styles["SubmitSection"]))
            continue
        if re.match(r"^\d+\.\s+", line):
            story.append(Paragraph(clean(line), styles["SubmitBullet"]))
            continue
        if line.startswith("- "):
            story.append(Paragraph("&bull; " + clean(line[2:]), styles["SubmitBullet"]))
            continue
        if line.endswith(":") and len(line) < 80:
            story.append(Paragraph(f"<b>{clean(line)}</b>", styles["SubmitBody"]))
            continue
        story.append(Paragraph(clean(line), styles["SubmitBody"]))
    return story


def build_pdf():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    styles = build_styles()
    doc = BaseDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        rightMargin=0.58 * inch,
        leftMargin=0.58 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.55 * inch,
        title="Plant Brain - PS-08 Hackathon Submission",
        author="Plant Brain Team",
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="normal")
    doc.addPageTemplates([PageTemplate(id="default", frames=[frame], onPage=draw_header_footer)])

    story = [
        Spacer(1, 1.15 * inch),
        Paragraph("Plant Brain", styles["SubmitTitle"]),
        Paragraph("AI for Industrial Knowledge Intelligence", styles["SubmitSubtitle"]),
        Paragraph("PS-08: Unified Asset & Operations Brain", styles["SubmitSubtitle"]),
        Spacer(1, 0.35 * inch),
        architecture_table(styles),
        Spacer(1, 0.35 * inch),
        Paragraph(
            "Working prototype for industrial document ingestion, knowledge graph intelligence, RAG-style cited answers, compliance gap detection, maintenance RCA, and lessons-learned discovery.",
            styles["SubmitSubtitle"],
        ),
        PageBreak(),
    ]

    story.extend(parse_markdown(SOURCE.read_text(encoding="utf-8"), styles))
    doc.build(story)
    print(OUTPUT)


if __name__ == "__main__":
    build_pdf()
