#!/usr/bin/env python3
"""docx helpers for resume and letter. No content: the text comes from build_<role>.py, the facts from fatos.py."""
import re, os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import fatos as FT   # single source of facts: sistema/fatos.yaml
from docx import Document
from docx.shared import Pt, Mm, RGBColor
from docx.enum.text import WD_TAB_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

OUT = os.environ.get("JOBSEARCH_OUT", "/tmp/docs")
F = "Arial"

def base_doc():
    doc = Document()
    st = doc.styles["Normal"]
    st.font.name = F
    st.font.size = Pt(10)
    st.paragraph_format.space_after = Pt(3)
    for s in doc.sections:
        s.page_width, s.page_height = Mm(210), Mm(297)  # A4
        s.top_margin = s.bottom_margin = Mm(18)
        s.left_margin = s.right_margin = Mm(19)
    return doc

def add_runs(p, text, size=10, italic=False, color=None):
    for i, part in enumerate(re.split(r"\*\*", text)):
        if not part:
            continue
        r = p.add_run(part)
        r.bold = (i % 2 == 1)
        r.italic = italic
        r.font.size = Pt(size)
        r.font.name = F
        if color:
            r.font.color.rgb = RGBColor(*color)
    return p

def para(doc, text, size=10, after=6, italic=False, before=0):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(after)
    p.paragraph_format.space_before = Pt(before)
    add_runs(p, text, size=size, italic=italic)
    return p

def bottom_border(p):
    pPr = p._p.get_or_add_pPr()
    pbdr = OxmlElement("w:pBdr")
    b = OxmlElement("w:bottom")
    b.set(qn("w:val"), "single"); b.set(qn("w:sz"), "6")
    b.set(qn("w:space"), "2"); b.set(qn("w:color"), "999999")
    pbdr.append(b); pPr.append(pbdr)

def heading(doc, text, before=9):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(before)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(text.upper())
    r.bold = True; r.font.size = Pt(11); r.font.name = F
    bottom_border(p)
    return p

def right_tab(p, section_width_mm=172):
    p.paragraph_format.tab_stops.add_tab_stop(Mm(section_width_mm), WD_TAB_ALIGNMENT.RIGHT)

MESES_3 = {"January": "Jan", "February": "Feb", "March": "Mar", "April": "Apr", "June": "Jun", "July": "Jul",
           "August": "Aug", "September": "Sep", "October": "Oct", "November": "Nov", "December": "Dec"}


def mes_3_letras(texto):
    """Rule: in the formatted resume the month is 3 letters; the ATS version (build_ats.py) spells it out."""
    for cheio, curto in MESES_3.items():
        texto = texto.replace(cheio, curto)
    return texto


def jobline(doc, left, dates):
    dates = mes_3_letras(dates)
    # The company descriptor "(...)" goes on a second line, so the date never breaks.
    # A location like "(Seattle, WA)" stays on the line.
    desc = None
    m = re.match(r"^(.*\*\*)\s+\((.+)\)\s*$", left)
    if m and not re.match(r"^[A-Z][A-Za-z ]+, [A-Z]{2}$", m.group(2)):
        left, desc = m.group(1), m.group(2)[0].upper() + m.group(2)[1:]
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(0 if desc else 2)
    p.paragraph_format.keep_with_next = True   # a title never sits alone at the foot of the page
    right_tab(p)
    add_runs(p, left)
    r = p.add_run("\t" + dates)
    r.bold = True; r.font.size = Pt(10); r.font.name = F
    if desc:
        p2 = doc.add_paragraph()
        p2.paragraph_format.space_after = Pt(2)
        p2.paragraph_format.keep_with_next = True
        add_runs(p2, desc, size=9, italic=True)
    return p

def bullet(doc, text, size=10):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.space_after = Pt(1.5)
    p.paragraph_format.left_indent = Pt(12)
    p.paragraph_format.first_line_indent = Pt(-12)
    add_runs(p, text, size=size)
    return p

def header_block(doc, citizen_line):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(1)
    r = p.add_run(FT.F.identidade.nome_curriculo)
    r.bold = True; r.font.size = Pt(20); r.font.name = F
    p2 = doc.add_paragraph()
    p2.paragraph_format.space_after = Pt(1)
    add_runs(p2, FT.linha_contato(), size=9)
    if citizen_line:
        p3 = doc.add_paragraph()
        p3.paragraph_format.space_after = Pt(6)
        add_runs(p3, citizen_line, size=9, italic=True)
