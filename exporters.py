import io
import re
import unicodedata
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from fpdf import FPDF

def sanitize_text(text: str) -> str:
    text = text.replace("\u2018", "'").replace("\u2019", "'").replace("\u201c", '"').replace("\u201d", '"')
    text = text.replace("\u2013", "-").replace("\u2014", "-").replace("\u2022", "-")
    return text.strip()

def _ascii_safe(text: str) -> str:
    text = sanitize_text(text)
    return unicodedata.normalize("NFKD", text).encode("latin-1", "replace").decode("latin-1")

def format_txt(text: str) -> bytes:
    return sanitize_text(text).encode("utf-8")

def format_docx(text: str, doc_type: str, logo_bytes: bytes | None = None) -> bytes:
    doc = Document()
    section = doc.sections[0]
    section.top_margin = Inches(0.75)
    section.bottom_margin = Inches(0.75)
    section.left_margin = Inches(0.85)
    section.right_margin = Inches(0.85)

    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(11)
    normal.font.color.rgb = RGBColor(35, 35, 35)

    if logo_bytes:
        try:
            doc.add_picture(io.BytesIO(logo_bytes), width=Inches(1.4))
            doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
        except Exception:
            pass

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run(doc_type.upper())
    run.bold = True
    run.font.name = "Times New Roman"
    run.font.size = Pt(16)

    for raw_line in sanitize_text(text).splitlines():
        line = raw_line.strip()
        if not line:
            doc.add_paragraph()
            continue
        is_heading = (len(line) < 90 and (
            line.isupper() or re.match(r"^(?:\d+(?:\.\d+)*[.)]?|SECTION\s+\d+|ARTICLE\s+[IVX]+)\s+\S", line, re.I)
        ))
        paragraph = doc.add_paragraph()
        if is_heading:
            run = paragraph.add_run(line)
            run.bold = True
            run.font.size = Pt(12)
        else:
            paragraph.add_run(line)

    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer.add_run("LegalEase | AI-assisted draft — obtain qualified legal review before signing").italic = True
    output = io.BytesIO()
    doc.save(output)
    return output.getvalue()

def format_pdf(text: str, doc_type: str, logo_bytes: bytes | None = None) -> bytes:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()
    pdf.set_margins(20, 18, 20)

    if logo_bytes:
        # FPDF needs a file path for images; use a temporary file safely.
        import tempfile, os
        suffix = ".png"
        try:
            from PIL import Image
            im = Image.open(io.BytesIO(logo_bytes))
            suffix = ".jpg" if im.format == "JPEG" else ".png"
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                tmp.write(logo_bytes)
                logo_path = tmp.name
            pdf.image(logo_path, x=85, y=12, w=40)
            pdf.ln(30)
        except Exception:
            pass
        finally:
            try:
                os.unlink(logo_path)
            except Exception:
                pass

    pdf.set_font("Times", "B", 16)
    pdf.multi_cell(0, 9, _ascii_safe(doc_type.upper()), align="C")
    pdf.ln(4)
    for line in sanitize_text(text).splitlines():
        line = line.strip()
        if not line:
            pdf.ln(3)
            continue
        is_heading = len(line) < 90 and (line.isupper() or re.match(r"^(?:\d+(?:\.\d+)*[.)]?|SECTION\s+\d+|ARTICLE\s+[IVX]+)\s+\S", line, re.I))
        pdf.set_font("Times", "B" if is_heading else "", 11 if is_heading else 10)
        pdf.multi_cell(0, 6, _ascii_safe(line))
    for page in range(1, pdf.page_no() + 1):
        pdf.page = page
        pdf.set_y(-14)
        pdf.set_font("Times", "I", 8)
        pdf.cell(0, 8, "LegalEase | AI-assisted draft - legal review recommended", align="C")
    return bytes(pdf.output())
