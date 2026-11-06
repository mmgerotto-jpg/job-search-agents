#!/usr/bin/env python3
"""Acme - Senior Operations Manager. Example of the pattern: no fact typed, everything comes from fatos.py. The reasoning goes in Notas.md."""
import os, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
SIS = os.path.join(AQUI, "..", "..", "..", "sistema")
sys.path[:0] = [SIS, os.path.join(SIS, "geradores")]
import fatos as FT
import build_docs as B

N = FT.F.northwind
CITIZEN = FT.F.identidade.cidadania_en + "  |  " + FT.F.identidade.disponibilidade_en + "  |  " + FT.linha_idiomas()
LOCATION_LINE = "Lisbon, Portugal"

SUMMARY = (
    "Operations leader with more than a decade of experience across consulting and analytics. Proficient in running "
    f"client operations at scale: {N.carteira}, {N.agentes} automated agents in production, and the data work behind "
    "each rollout.")

SKILLS = [
    "**Operations:** client portfolio management, rollout planning, KPI reporting",
    "**Data and integration:** SQL, dashboards, working with each client's IT team",
]

EXPERIENCE = [
    (f"**{FT.cargo('northwind')}** - **{FT.empresa('northwind')}** (retail analytics)", FT.periodo("northwind"), [
        f"**Ran a portfolio of {N.carteira}**, with combined revenues {N.receita_clientes}.",
        f"**Took {N.agentes} automated agents into production**; {N.formulacao_erp}, so each integration was designed with the client's IT team.",
    ]),
    (f"**{FT.cargo('contoso')}** - **{FT.nome_curto('contoso')}**", FT.periodo("contoso"), [
        "Led workstreams on operating-model projects for retail and logistics clients.",
    ]),
]
EARLIER = []


def build():
    doc = B.base_doc()
    B.header_block(doc, CITIZEN)
    B.heading(doc, "Summary", before=4)
    B.para(doc, SUMMARY, after=4)
    B.heading(doc, "Experience")
    for title, dates, bullets in EXPERIENCE:
        B.jobline(doc, title, dates)
        for b in bullets:
            B.bullet(doc, b)
    B.heading(doc, "Skills")
    for s in SKILLS:
        B.bullet(doc, s)
    B.heading(doc, "Education")
    B.para(doc, f"**{FT.instituicao()}** - {FT.educacao()}.", after=0)
    doc.save(os.path.join(B.OUT, "Candidate_Resume_EN.docx"))
    print("ok")


if __name__ == "__main__":
    build()
