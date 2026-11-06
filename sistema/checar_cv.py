#!/usr/bin/env python3
"""
Resume quick-read auditor.

Usage: python3 checar_cv.py CV.pdf term1 term2 term3 ...

The terms are the package's THESIS: what the role buys in you. For an
agribusiness role they might be agriculture, commodities, agribusiness,
sugarcane, coffee. For a fraud-tech role: claims, fraud, underwriting,
decisioning.

Three behaviors that checar_texto.py did not cover, because they are about
READING and not writing:

  - a scan of ~8 seconds, ~80 words (target 80, tolerance 100)
  - F-pattern scanning: the first three lines and the left third weigh most
  - almost nobody gets to page 2

The script REPORTS, it does not fix. The order of the experiences is the
human's decision, case by case. The preferred lever is the SUMMARY: if it
carries the thesis, it is on page 1 without touching the chronology.
"""
import re, subprocess, sys

ALVO_SUMMARY = 80          # words that fit in an 8s scan: the aim
TETO_SUMMARY = 100         # going a little over is fine. Above this, warn.
PREAMBULOS = ("worked", "responsible", "helped", "was", "participated",
              "involved", "assisted", "supported", "contributed", "tasked")


def txt(pdf, p1=False):
    cmd = ["pdftotext"] + (["-f", "1", "-l", "1"] if p1 else []) + [pdf, "-"]
    return subprocess.run(cmd, capture_output=True, text=True).stdout


def main():
    if len(sys.argv) < 2:
        print(__doc__); return 1
    pdf, tese = sys.argv[1], [t.lower() for t in sys.argv[2:]]
    todo, pag1 = txt(pdf), txt(pdf, p1=True)
    n_pag = int(re.search(r"Pages:\s+(\d+)",
                subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout).group(1))

    alertas = []
    print(f"pages             : {n_pag}")

    # 1. Is the thesis on page 1?
    if tese:
        faltam = [t for t in tese if t not in pag1.lower()]
        achou = [t for t in tese if t in pag1.lower()]
        print(f"thesis on page 1  : {len(achou)}/{len(tese)}" +
              (f"  ⚠️ missing: {', '.join(faltam)}" if faltam else "  ✅"))
        if faltam:
            alertas.append("thesis term appears only on page 2. Almost nobody gets there. "
                           "Prefer moving it into the SUMMARY, which sits at the top, instead of reordering "
                           "the experiences - the order is a case-by-case decision.")

    # 2. Summary length
    m = re.search(r"SUMMARY(.*?)(?:EXPERIENCE|SKILLS|EDUCATION)", pag1, re.S | re.I)
    if m:
        n = len(m.group(1).split())
        marca = "✅" if n <= ALVO_SUMMARY else ("~ above target, within tolerance"
                                                if n <= TETO_SUMMARY else "⚠️")
        print(f"summary           : {n} words (target {ALVO_SUMMARY}, ceiling {TETO_SUMMARY})  {marca}")
        if n > TETO_SUMMARY:
            alertas.append(f"summary with {n} words. An 8-second scan reads ~{ALVO_SUMMARY}, "
                           f"and the tolerance goes up to {TETO_SUMMARY}. It is the hottest block on the page - "
                           "cut down to what decides, without removing the thesis.")

    # 3. Weak bullet openings (left third of the F)
    fracos = [l.strip() for l in todo.split("\n")
              if l.strip() and l.strip().split()[0].lower().strip(",.") in PREAMBULOS]
    print(f"bullets with preamble: {len(fracos)}" + ("  ✅" if not fracos else ""))
    for f in fracos[:5]:
        print(f"    ! {f[:70]}...")
    if fracos:
        alertas.append("bullet opening with a preamble. The first 2-4 words are what "
                       "the eye catches in the F scan - put the result there.")

    print()
    for a in alertas:
        print("  ! " + a)
    if not alertas:
        print("  ok: survives a quick scan.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
