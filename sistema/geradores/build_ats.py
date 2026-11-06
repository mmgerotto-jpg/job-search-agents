#!/usr/bin/env python3
"""
ATS-plain resume renderer — for Workday, Taleo, iCIMS and other parsers.

Design rules (each one exists because a parser has broken on the alternative):
  * No tab stops. Dates live on their own line, never right-aligned across a tab.
  * Company on its own line, first. Title on the next line. Dates on the third.
  * No em/en dashes, no smart quotes, no parenthetical descriptors on the company line.
  * No bold-inside-line markup, no tables, no columns, no headers/footers.
  * Plain "-" bullets, one line each.
  * Section headings are single plain words in caps: SUMMARY / EXPERIENCE / SKILLS / EDUCATION.

Usage: python3 build_ats.py <module_name> <output_basename>
  e.g. python3 build_ats.py build_acme Candidate_Resume_ATS
The source module must expose SUMMARY, SKILLS and EXPERIENCE (and optionally EARLIER).
"""
import os, re, sys, importlib
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import fatos as FT   # single source of facts: sistema/fatos.yaml
from docx import Document
from docx.shared import Pt, Mm

OUT = os.environ.get("JOBSEARCH_OUT", "/tmp/docs")
F = "Arial"

# The parenthetical descriptor comes off the COMPANY LINE, because the parser
# swallows "(Enterprise AI)" into the name and the Employer field turns to garbage.
# But it cannot simply vanish: on an international resume the human reader
# who opens the PDF after the parser has no idea what the lesser-known
# companies are. So the descriptor comes back as the FIRST BULLET, where it is free text and
# no parser tries to interpret it.
DESCRIPTOR = re.compile(r"\s*\(([^)]*)\)\s*$")


def clean(t):
    t = t.replace("**", "")
    for a, b in [("—", "-"), ("–", "-"), ("’", "'"), ("“", '"'),
                 ("”", '"'), ("·", "-"), ("~", "approx. ")]:
        t = t.replace(a, b)
    return re.sub(r"\s+", " ", t).strip()


def split_jobline(raw):
    """'**Title** - **Company** (descriptor)' -> ('Title', 'Company', 'descriptor')"""
    t = clean(raw)
    parts = t.split(" - ", 1)
    title = parts[0].strip()
    if len(parts) < 2:
        return title, "", ""
    m = DESCRIPTOR.search(parts[1])
    desc = m.group(1).strip() if m else ""
    company = DESCRIPTOR.sub("", parts[1]).strip()
    return title, company, desc


def line(doc, text, bold=False, size=10, after=2, before=0):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(after)
    p.paragraph_format.space_before = Pt(before)
    r = p.add_run(text)
    r.bold = bold
    r.font.name = F
    r.font.size = Pt(size)
    return p


def build(mod_name, basename):
    m = importlib.import_module(mod_name)
    doc = Document()
    st = doc.styles["Normal"]
    st.font.name = F
    st.font.size = Pt(9.5)
    st.paragraph_format.space_after = Pt(2)
    for s in doc.sections:
        s.page_width, s.page_height = Mm(210), Mm(297)
        s.top_margin = s.bottom_margin = Mm(13)
        s.left_margin = s.right_margin = Mm(18)

    # EVERY header line gets a label. Without a label the parser guesses from the
    # format, and guesses wrong:
    #   * a bare "Lisbon, Portugal" becomes a legal name (Given="Lisbon", Family="Portugal")
    #   * a phone "12345-6789" has the exact format of a US ZIP+4 and becomes a ZIP code
    # The hyphen in the phone number also goes, so it does not match NNNNN-NNNN.
    line(doc, FT.F.identidade.nome_curriculo, bold=True, size=16, after=2)
    line(doc, "Email: " + FT.F.identidade.contato.email, after=1)
    line(doc, "Phone: " + FT.F.identidade.contato.telefone_ats, after=1)
    line(doc, "LinkedIn: " + FT.F.identidade.contato.linkedin, after=1)
    loc = clean(getattr(m, "LOCATION_LINE", ""))
    if loc:
        line(doc, "Location: " + loc, after=6)

    line(doc, "SUMMARY", bold=True, size=11, after=3, before=6)
    line(doc, clean(m.SUMMARY), after=8)

    line(doc, "EXPERIENCE", bold=True, size=11, after=3, before=6)
    for raw_title, dates, bullets in m.EXPERIENCE:
        title, company, desc = split_jobline(raw_title)
        line(doc, company, bold=True, after=1, before=5)   # company first, on its own line
        line(doc, title, after=1)                          # then title
        line(doc, clean(dates), after=2)                   # then dates, own line
        if desc:
            line(doc, "- " + desc + ".", after=1)          # descritor como primeiro bullet
        for b in bullets:
            line(doc, "- " + clean(b), after=1)

    # A module may set EARLIER = [] to suppress the section entirely. Some parsers
    # (iCIMS) cap the number of imported roles and fill oldest-first, so a footnote
    # list of early jobs can crowd out the recent ones that matter.
    earlier = getattr(m, "EARLIER", [])  # rule: no Earlier section; all experiences go in EXPERIENCE
    if earlier:
        line(doc, "EARLIER EXPERIENCE", bold=True, size=11, after=3, before=8)
        for e in earlier:
            line(doc, "- " + clean(e), after=1)

    line(doc, "SKILLS", bold=True, size=11, after=3, before=8)
    for s in m.SKILLS:
        line(doc, "- " + clean(s), after=1)

    line(doc, "EDUCATION", bold=True, size=11, after=3, before=8)
    line(doc, FT.instituicao(), bold=True, after=1)
    line(doc, FT.educacao(), after=2)
    line(doc, "Languages: " + getattr(m, "IDIOMAS", FT.linha_idiomas()), after=0)

    # Some forms require a SINGLE file and ask for the letter to be merged
    # into the resume. The letter goes AFTER, on a new page. If it comes first, the parser
    # reads the letter as if it were the experience and the result is garbage.
    letter = getattr(m, "LETTER_BODY", None)
    if letter:
        doc.add_page_break()
        line(doc, "COVER LETTER", bold=True, size=11, after=6)
        if getattr(m, "LETTER_SUBJECT", None):
            line(doc, clean(m.LETTER_SUBJECT), after=6)
        line(doc, getattr(m, "LETTER_GREETING", "Dear Hiring Team,"), after=6)
        for p in letter:
            line(doc, clean(p), after=6)
        line(doc, "Sincerely,", after=2)
        line(doc, FT.F.identidade.nome_curriculo, after=0)

    path = os.path.join(OUT, basename + ".docx")
    doc.save(path)
    print("wrote", path)


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
