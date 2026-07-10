"""Build submission PPTX and PDF artifacts from markdown sources.

The script converts the curated markdown files under ``submission/raw`` into
deliverables for submission. It intentionally avoids network access and keeps
the rendering simple so the generated files can be reproduced locally.
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_AUTO_SIZE
from pptx.util import Inches, Pt
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "submission" / "raw"
OUT_DIR = ROOT / "submission"

PPT_SOURCE = RAW_DIR / "PRESENTATION_10_15_SLIDES.md"
PDF_SOURCES = {
    ROOT / "docs" / "guidance.md": OUT_DIR / "GUIDANCE_UPDATED.pdf",
    RAW_DIR / "AGENT_ARCHITECTURE.md": OUT_DIR / "AI_AGENT_ARCHITECTURE_UPDATED.pdf",
    RAW_DIR / "DEMO_SCENARIO.md": OUT_DIR / "DEMO_SCENARIO_UPDATED.pdf",
    RAW_DIR / "REFERENCES.md": OUT_DIR / "REFERENCES_UPDATED.pdf",
    RAW_DIR / "FINAL_REPORT.md": OUT_DIR / "FINAL_REPORT_UPDATED.pdf",
}
PPT_OUT = OUT_DIR / "FINAL_PRESENTATION_UPDATED.pptx"

FONT_CANDIDATES = [
    Path(r"C:\Windows\Fonts\malgun.ttf"),
    Path(r"C:\Windows\Fonts\NotoSansKR-VF.ttf"),
]
BOLD_FONT_CANDIDATES = [
    Path(r"C:\Windows\Fonts\malgunbd.ttf"),
    Path(r"C:\Windows\Fonts\malgun.ttf"),
    Path(r"C:\Windows\Fonts\NotoSansKR-VF.ttf"),
]


@dataclass
class SlideSpec:
    """Parsed slide content from the presentation markdown."""

    title: str
    bullets: list[str]
    note: str = ""


def read_markdown(path: Path) -> str:
    """Read a markdown file as UTF-8, normalizing common line endings."""

    return path.read_text(encoding="utf-8-sig").replace("\r\n", "\n")


def register_korean_fonts() -> tuple[str, str]:
    """Register Korean-capable fonts for ReportLab and return regular/bold names."""

    regular_path = next((path for path in FONT_CANDIDATES if path.exists()), None)
    bold_path = next((path for path in BOLD_FONT_CANDIDATES if path.exists()), regular_path)
    if not regular_path:
        raise FileNotFoundError("No Korean font found in C:\\Windows\\Fonts.")

    regular_name = "SubmissionKorean"
    bold_name = "SubmissionKoreanBold"
    pdfmetrics.registerFont(TTFont(regular_name, str(regular_path)))
    pdfmetrics.registerFont(TTFont(bold_name, str(bold_path)))
    return regular_name, bold_name


def clean_inline(text: str) -> str:
    """Convert lightweight Markdown inline syntax to readable plain text."""

    text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 (\2)", text)
    text = text.replace("**", "").replace("__", "").replace("`", "")
    return text.strip()


def parse_slides(markdown: str, max_slides: int = 15) -> list[SlideSpec]:
    """Parse slide headings and body text from the presentation markdown."""

    lines = markdown.splitlines()
    slides: list[SlideSpec] = []
    current: SlideSpec | None = None
    note_mode = False

    for raw_line in lines:
        line = raw_line.strip()
        match = re.match(r"^##\s+Slide\s+\d+\.\s*(.+)$", line, re.IGNORECASE)
        if match:
            if current:
                slides.append(current)
            current = SlideSpec(title=clean_inline(match.group(1)), bullets=[])
            note_mode = False
            continue

        if current is None:
            continue
        if not line or line == "---":
            continue
        if line.startswith("선택 부록 메모") or line.startswith("Optional appendix note"):
            note_mode = True
            continue
        if line.startswith("#"):
            continue

        cleaned = clean_inline(re.sub(r"^[-*]\s+", "", line))
        if not cleaned:
            continue
        if note_mode:
            current.note = f"{current.note} {cleaned}".strip()
        else:
            current.bullets.append(cleaned)

    if current:
        slides.append(current)
    return slides[:max_slides]


def set_run_font(paragraph, font_name: str, size: int, color: RGBColor | None = None) -> None:
    """Apply font settings to all runs in a PowerPoint paragraph."""

    for run in paragraph.runs:
        run.font.name = font_name
        run.font.size = Pt(size)
        if color:
            run.font.color.rgb = color


def add_textbox(slide, left, top, width, height, text: str, font_size: int, color: RGBColor):
    """Add a PowerPoint textbox with Korean font settings."""

    shape = slide.shapes.add_textbox(left, top, width, height)
    frame = shape.text_frame
    frame.clear()
    frame.word_wrap = True
    frame.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
    paragraph = frame.paragraphs[0]
    paragraph.text = text
    paragraph.font.name = "Malgun Gothic"
    paragraph.font.size = Pt(font_size)
    paragraph.font.color.rgb = color
    return shape


def build_presentation() -> Path:
    """Create a 15-slide-or-less PowerPoint deck from the presentation markdown."""

    slides = parse_slides(read_markdown(PPT_SOURCE), max_slides=15)
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]
    navy = RGBColor(28, 45, 74)
    accent = RGBColor(32, 125, 140)
    body = RGBColor(45, 51, 60)
    muted = RGBColor(103, 111, 124)

    for index, spec in enumerate(slides, start=1):
        slide = prs.slides.add_slide(blank)
        slide.background.fill.solid()
        slide.background.fill.fore_color.rgb = RGBColor(250, 251, 253)
        slide.shapes.add_shape(1, Inches(0), Inches(0), Inches(13.333), Inches(0.18)).fill.solid()
        slide.shapes[-1].fill.fore_color.rgb = accent
        title = spec.title or f"Slide {index}"

        if index == 1:
            add_textbox(slide, Inches(0.75), Inches(1.15), Inches(11.9), Inches(1.2), title, 34, navy)
            subtitle = "\n".join(spec.bullets[:3])
            add_textbox(slide, Inches(0.8), Inches(2.55), Inches(11.4), Inches(1.5), subtitle, 20, body)
            add_textbox(
                slide,
                Inches(0.8),
                Inches(6.75),
                Inches(11.8),
                Inches(0.35),
                "Submission deck generated from submission/raw/PRESENTATION_10_15_SLIDES.md",
                9,
                muted,
            )
            continue

        add_textbox(slide, Inches(0.55), Inches(0.45), Inches(11.8), Inches(0.6), title, 22, navy)
        content = slide.shapes.add_textbox(Inches(0.8), Inches(1.3), Inches(11.75), Inches(4.95))
        frame = content.text_frame
        frame.clear()
        frame.word_wrap = True
        frame.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE

        bullet_count = min(len(spec.bullets), 7)
        font_size = 18 if bullet_count <= 5 else 15
        for bullet_index, bullet in enumerate(spec.bullets[:7]):
            paragraph = frame.paragraphs[0] if bullet_index == 0 else frame.add_paragraph()
            paragraph.text = bullet
            paragraph.level = 0
            paragraph.space_after = Pt(8)
            paragraph.font.name = "Malgun Gothic"
            paragraph.font.size = Pt(font_size)
            paragraph.font.color.rgb = body

        if spec.note:
            note = spec.note[:260] + ("..." if len(spec.note) > 260 else "")
            add_textbox(slide, Inches(0.8), Inches(6.35), Inches(10.8), Inches(0.55), note, 9, muted)
        add_textbox(slide, Inches(12.0), Inches(6.85), Inches(0.7), Inches(0.25), str(index), 9, muted)

    prs.save(PPT_OUT)
    return PPT_OUT


def build_styles(regular_font: str, bold_font: str):
    """Create ReportLab styles for Korean markdown PDF rendering."""

    styles = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "SubmissionTitle",
            parent=styles["Title"],
            fontName=bold_font,
            fontSize=20,
            leading=26,
            alignment=TA_CENTER,
            spaceAfter=12,
            wordWrap="CJK",
        ),
        "h1": ParagraphStyle(
            "SubmissionH1",
            parent=styles["Heading1"],
            fontName=bold_font,
            fontSize=17,
            leading=22,
            spaceBefore=12,
            spaceAfter=8,
            wordWrap="CJK",
        ),
        "h2": ParagraphStyle(
            "SubmissionH2",
            parent=styles["Heading2"],
            fontName=bold_font,
            fontSize=14,
            leading=19,
            spaceBefore=10,
            spaceAfter=6,
            wordWrap="CJK",
        ),
        "h3": ParagraphStyle(
            "SubmissionH3",
            parent=styles["Heading3"],
            fontName=bold_font,
            fontSize=12,
            leading=16,
            spaceBefore=8,
            spaceAfter=4,
            wordWrap="CJK",
        ),
        "body": ParagraphStyle(
            "SubmissionBody",
            parent=styles["BodyText"],
            fontName=regular_font,
            fontSize=9.5,
            leading=14,
            spaceAfter=4,
            alignment=TA_LEFT,
            wordWrap="CJK",
        ),
        "bullet": ParagraphStyle(
            "SubmissionBullet",
            parent=styles["BodyText"],
            fontName=regular_font,
            fontSize=9.5,
            leading=14,
            leftIndent=12,
            firstLineIndent=-8,
            spaceAfter=3,
            wordWrap="CJK",
        ),
        "small": ParagraphStyle(
            "SubmissionSmall",
            parent=styles["BodyText"],
            fontName=regular_font,
            fontSize=7.5,
            leading=10,
            spaceAfter=2,
            wordWrap="CJK",
        ),
        "code": ParagraphStyle(
            "SubmissionCode",
            parent=styles["Code"],
            fontName=regular_font,
            fontSize=7.2,
            leading=9,
            backColor=colors.HexColor("#F4F6F8"),
            borderColor=colors.HexColor("#DDE3EA"),
            borderWidth=0.25,
            borderPadding=4,
            wordWrap="CJK",
        ),
    }


def flush_code_block(flowables: list, code_lines: list[str], styles: dict) -> None:
    """Append a formatted code block to a PDF story."""

    if not code_lines:
        return
    code_text = "\n".join(code_lines)
    flowables.append(Preformatted(html.escape(code_text), styles["code"], maxLineLength=92))
    flowables.append(Spacer(1, 3))
    code_lines.clear()


def markdown_to_flowables(markdown: str, styles: dict) -> list:
    """Convert a limited Markdown subset into ReportLab flowables."""

    flowables: list = []
    in_code = False
    code_lines: list[str] = []
    title_used = False

    for raw_line in markdown.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if stripped.startswith("```"):
            if in_code:
                flush_code_block(flowables, code_lines, styles)
                in_code = False
            else:
                in_code = True
            continue
        if in_code:
            code_lines.append(line)
            continue
        if not stripped:
            flowables.append(Spacer(1, 3))
            continue
        if stripped == "---":
            flowables.append(Spacer(1, 5))
            continue
        if stripped.startswith("|") and stripped.endswith("|"):
            flowables.append(Paragraph(html.escape(clean_inline(stripped)), styles["small"]))
            continue

        heading = re.match(r"^(#{1,4})\s+(.+)$", stripped)
        if heading:
            level = len(heading.group(1))
            text = html.escape(clean_inline(heading.group(2)))
            if level == 1 and not title_used:
                flowables.append(Paragraph(text, styles["title"]))
                title_used = True
            elif level == 1:
                flowables.append(PageBreak())
                flowables.append(Paragraph(text, styles["h1"]))
            elif level == 2:
                flowables.append(Paragraph(text, styles["h2"]))
            else:
                flowables.append(Paragraph(text, styles["h3"]))
            continue

        bullet = re.match(r"^([-*]|\d+[.)])\s+(.+)$", stripped)
        if bullet:
            flowables.append(Paragraph(f"- {html.escape(clean_inline(bullet.group(2)))}", styles["bullet"]))
            continue

        blockquote = re.match(r"^>\s*(.+)$", stripped)
        if blockquote:
            flowables.append(Paragraph(html.escape(clean_inline(blockquote.group(1))), styles["small"]))
            continue

        flowables.append(Paragraph(html.escape(clean_inline(stripped)), styles["body"]))

    flush_code_block(flowables, code_lines, styles)
    return flowables


def draw_page_number(canvas, doc) -> None:
    """Draw a consistent footer on each PDF page."""

    canvas.saveState()
    canvas.setFont("SubmissionKorean", 7)
    canvas.setFillColor(colors.HexColor("#6B7280"))
    canvas.drawRightString(A4[0] - 16 * mm, 10 * mm, f"{doc.page}")
    canvas.restoreState()


def build_pdf(source: Path, output: Path, styles: dict) -> Path:
    """Build one PDF artifact from a markdown source file."""

    doc = SimpleDocTemplate(
        str(output),
        pagesize=A4,
        rightMargin=16 * mm,
        leftMargin=16 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        title=source.stem,
    )
    story = markdown_to_flowables(read_markdown(source), styles)
    doc.build(story, onFirstPage=draw_page_number, onLaterPages=draw_page_number)
    return output


def main() -> None:
    """Generate all requested submission artifacts."""

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    regular_font, bold_font = register_korean_fonts()
    styles = build_styles(regular_font, bold_font)
    outputs = [build_presentation()]
    for source, output in PDF_SOURCES.items():
        outputs.append(build_pdf(source, output, styles))
    for output in outputs:
        print(f"created: {output.relative_to(ROOT)} ({output.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
