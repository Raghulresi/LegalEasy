import io
import re

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt


def sanitize_text(text: str) -> str:
    replacements = {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2013": "-",
        "\u2014": "-",
        "\u00a0": " ",
        "\u2022": "-",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text.replace("\r\n", "\n").replace("\r", "\n").strip()


def get_lines(text):
    return [line.strip() for line in sanitize_text(text).split("\n") if line.strip()]


def format_txt(text):
    return sanitize_text(text).encode("utf-8")


def format_docx(text, doc_type, logo_bytes=None):
    document = Document()
    section = document.sections[0]
    section.top_margin = Inches(0.7)
    section.bottom_margin = Inches(0.7)
    section.left_margin = Inches(0.8)
    section.right_margin = Inches(0.8)

    normal_style = document.styles["Normal"]
    normal_style.font.name = "Times New Roman"
    normal_style.font.size = Pt(11)

    if logo_bytes:
        try:
            paragraph = document.add_paragraph()
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            paragraph.add_run().add_picture(io.BytesIO(logo_bytes), width=Inches(1.4))
        except Exception:
            pass

    title = document.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title.add_run(doc_type.upper())
    title_run.bold = True
    title_run.font.name = "Times New Roman"
    title_run.font.size = Pt(16)

    for line in get_lines(text):
        if re.match(r"^(\d+\.|ARTICLE\s+\w+|SECTION\s+\w+)", line, re.IGNORECASE):
            paragraph = document.add_paragraph()
            run = paragraph.add_run(line)
            run.bold = True
        elif line.startswith(("-", "*", "•")):
            paragraph = document.add_paragraph(style="List Bullet")
            paragraph.add_run(line.lstrip("-*• ").strip())
        else:
            paragraph = document.add_paragraph(line)
        paragraph.paragraph_format.space_after = Pt(6)

    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer.add_run("Generated with LegalEase - AI-assisted draft. Review before use.")

    output = io.BytesIO()
    document.save(output)
    return output.getvalue()


def format_pdf(text, doc_type, logo_bytes=None):
    from fpdf import FPDF

    class LegalEasePDF(FPDF):
        def __init__(self, document_type):
            super().__init__()
            self.doc_type = document_type
            self.set_auto_page_break(auto=True, margin=18)

        def header(self):
            self.set_font("Helvetica", "B", 13)
            self.cell(0, 8, self.doc_type.upper(), align="C")
            self.ln(10)

        def footer(self):
            self.set_y(-14)
            self.set_font("Helvetica", "", 8)
            self.cell(
                0, 8, "LegalEase - AI-assisted draft. Review before use.", align="C"
            )

    pdf = LegalEasePDF(doc_type)
    pdf.add_page()
    pdf.set_font("Helvetica", "", 11)

    for line in get_lines(text):
        if re.match(r"^(\d+\.|ARTICLE\s+\w+|SECTION\s+\w+)", line, re.IGNORECASE):
            pdf.set_font("Helvetica", "B", 11)
            pdf.multi_cell(0, 6, line)
            pdf.set_font("Helvetica", "", 11)
        elif line.startswith(("-", "*", "•")):
            pdf.multi_cell(0, 6, "- " + line.lstrip("-*• ").strip())
        else:
            pdf.multi_cell(0, 6, line)
        pdf.ln(2)

    return bytes(pdf.output())