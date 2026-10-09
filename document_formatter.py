from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Optional

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.shared import Inches, Pt
from fpdf import FPDF
from PIL import Image

from backend.utils.text_utils import pdf_safe_text, sanitize_text, split_terms

BASE_DIR = Path(__file__).resolve().parents[2]
DEFAULT_LOGO = BASE_DIR / "assets" / "logo.png"


def _set_docx_font(document: Document, font_name: str) -> None:
    styles = document.styles
    for style_name in ["Normal", "Title", "Heading 1", "Heading 2", "Heading 3"]:
        try:
            style = styles[style_name]
            style.font.name = font_name
            style.font.size = Pt(11 if style_name == "Normal" else 16)
        except KeyError:
            pass


def _add_logo_docx(document: Document, logo_bytes: Optional[bytes]) -> None:
    source = BytesIO(logo_bytes) if logo_bytes else (DEFAULT_LOGO.open("rb") if DEFAULT_LOGO.exists() else None)
    if source:
        paragraph = document.add_paragraph()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = paragraph.add_run()
        run.add_picture(source, width=Inches(1.1))
        if hasattr(source, "close") and not isinstance(source, BytesIO):
            source.close()


def format_docx(text: str, doc_type: str, logo_bytes: Optional[bytes] = None, font_name: str = "Times New Roman") -> bytes:
    document = Document()
    section = document.sections[0]
    section.top_margin = Inches(0.7)
    section.bottom_margin = Inches(0.7)
    section.left_margin = Inches(0.8)
    section.right_margin = Inches(0.8)
    _set_docx_font(document, font_name)
    _add_logo_docx(document, logo_bytes)

    title = document.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run(sanitize_text(doc_type).upper())
    run.bold = True
    run.font.size = Pt(18)

    subtitle = document.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    srun = subtitle.add_run("AI-ASSISTED DRAFT - REVIEW BEFORE USE")
    srun.italic = True
    srun.font.size = Pt(9)

    for raw in sanitize_text(text).splitlines():
        line = raw.strip()
        if not line:
            document.add_paragraph()
            continue
        if line.endswith(":") or (len(line) < 90 and line.isupper()):
            p = document.add_paragraph()
            r = p.add_run(line)
            r.bold = True
        elif line.startswith(('-', '*', '•')):
            document.add_paragraph(line.lstrip("-*• "), style="List Bullet")
        else:
            document.add_paragraph(line)

    # Terms table: useful when terms are semicolon/newline separated in the request.
    terms = []
    for line in sanitize_text(text).splitlines():
        if line.startswith(("- ", "* ", "• ")):
            terms.append(line[2:].strip())
    if terms:
        document.add_heading("Key Terms", level=2)
        table = document.add_table(rows=1, cols=2)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.style = "Table Grid"
        hdr = table.rows[0].cells
        hdr[0].text = "No."
        hdr[1].text = "Term"
        for i, term in enumerate(terms, 1):
            cells = table.add_row().cells
            cells[0].text = str(i)
            cells[1].text = term
            for cell in cells:
                cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER

    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer.add_run("LegalEase - AI-assisted draft. Review before signing or relying on this document.").font.size = Pt(8)

    out = BytesIO()
    document.save(out)
    return out.getvalue()


class LegalEasePDF(FPDF):
    def __init__(self, doc_type: str, logo_bytes: Optional[bytes] = None):
        super().__init__()
        self.doc_type = pdf_safe_text(doc_type)
        self.logo_bytes = logo_bytes
        self.logo_path: Optional[str] = None

    def header(self):
        if self.logo_path:
            try:
                self.image(self.logo_path, x=(self.w - 22) / 2, y=8, w=22)
            except Exception:
                pass
            self.set_y(31)
        else:
            self.set_y(10)
        self.set_font("Helvetica", "B", 13)
        self.cell(0, 8, self.doc_type.upper(), align="C")
        self.ln(9)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 7)
        self.cell(0, 8, "LegalEase - AI-assisted draft | Review before use", align="C")


def format_pdf(text: str, doc_type: str, logo_bytes: Optional[bytes] = None) -> bytes:
    pdf = LegalEasePDF(doc_type, logo_bytes)
    temp_logo = None
    if logo_bytes:
        try:
            image = Image.open(BytesIO(logo_bytes)).convert("RGB")
            temp_logo = BytesIO()
            image.save(temp_logo, format="PNG")
            temp_logo.seek(0)
            # fpdf2 accepts file paths most consistently; write to a temporary file.
            import tempfile
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            tmp.write(temp_logo.read())
            tmp.close()
            pdf.logo_path = tmp.name
        except Exception:
            pdf.logo_path = None

    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()
    pdf.set_font("Helvetica", "", 10)

    for raw in sanitize_text(text).splitlines():
        line = raw.strip()
        if not line:
            pdf.ln(3)
            continue
        safe = pdf_safe_text(line)
        if line.endswith(":") or (len(line) < 90 and line.isupper()):
            pdf.set_font("Helvetica", "B", 10)
            pdf.multi_cell(pdf.epw, 6, safe)
            pdf.set_font("Helvetica", "", 10)
        elif line.startswith(('-', '*', '•')):
            pdf.multi_cell(pdf.epw, 5.5, "- " + pdf_safe_text(line.lstrip("-*• ")))
        else:
            pdf.multi_cell(pdf.epw, 5.5, safe)

    data = bytes(pdf.output())
    if temp_logo:
        try:
            Path(pdf.logo_path).unlink(missing_ok=True)
        except Exception:
            pass
    return data
