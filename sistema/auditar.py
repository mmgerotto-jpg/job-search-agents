#!/usr/bin/env python3
"""
auditar.py — the gate. Takes the folder of ONE application, returns PASS or BLOCKED.

    python3 auditar.py "applications/Acme - Senior Operations Manager"
        [--gravar]      writes Auditoria.md in the folder
        [--json]

Mechanical on purpose: it does not judge style, it verifies invariants. Exits 0 (PASS) or 1 (BLOCKED).

What BLOCKS:
  1. any banned string from fatos.yaml with severity "bloqueia" in outgoing material
     (cannot be waived: if the rule is wrong, fix the yaml, not the material)
  2. a literal asterisk in a PDF/docx
  3. page counts off target (resume 2, letter 1; ATS unlimited)
  4. checar_texto.py failing: AI vocabulary, cliche, dash/curly quote, repeated construction,
     repeated opening, duplicated passage between letter and email
     (can be accepted case by case, with a reason, in `auditoria_aceites.txt` in the folder:
      one line per accept, `warning excerpt | reason`)
  5. a required file missing (Resume.docx, Resume.pdf, Resume_ATS.docx, Notas.md)
  6. a generated FATOS.md out of date with fatos.yaml

What only WARNS (shows in the report, does not fail):
  a number with a unit that is not in fatos.yaml · rules with severity "alerta" (3x ROI, C-level...)
  · a build_*.py that does not import fatos.py · a docx without a PDF to check pages
  · QUICK READ: thesis outside page 1, summary above 80 words, bullet opening with a preamble
    (never blocks — the order of the experiences is the human's decision, case by case. Put a `tese.txt`
     in the role folder, one term per line, with what the role buys; without the file the page-1 check is skipped)
"""
import datetime
import glob
import json
import os
import re
import subprocess
import sys

import fatos as FT
import checar_fatos as CF

AQUI = os.path.dirname(os.path.abspath(__file__))
PAGINAS = FT.BRUTO["materiais"]["paginas"]
ITEM_TEXTO = ("ai vocabulary", "cliches", "dash/curly quote", "constructions", "repeated openings")


def paginas(pdf):
    try:
        r = subprocess.run(["pdfinfo", pdf], capture_output=True, text=True, timeout=30)
        m = re.search(r"^Pages:\s+(\d+)", r.stdout, re.M)
        return int(m.group(1)) if m else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def rodar_texto(*arquivos):
    r = subprocess.run([sys.executable, os.path.join(AQUI, "checar_texto.py"), *arquivos],
                       capture_output=True, text=True, timeout=90, cwd=AQUI)
    return r.stdout


def problemas_texto(saida, ritmo):
    """Reads checar_texto.py output. `ritmo=False` ignores burstiness (a resume bullet is not prose)."""
    achados = []
    for linha in saida.splitlines():
        if " : " in linha or ":" in linha:
            rot, _, val = linha.partition(":")
            rot_n, val = rot.strip().lower(), val.strip()
            if rot_n.startswith(ITEM_TEXTO) and val and val != "clean":
                achados.append(f"{rot.strip()}: {val}")
            elif rot_n.startswith("passages in common") and val and val != "clean":
                achados.append(f"{rot.strip()}: {val}")
        s = linha.strip()
        if ritmo and s.startswith("! ") and any(k in s for k in ("low deviation", "no short sentence", "no long sentence")):
            achados.append(s[2:].strip())
    return achados


def ler_aceites(pasta):
    caminho = os.path.join(pasta, "auditoria_aceites.txt")
    aceites = []
    if os.path.exists(caminho):
        for l in open(caminho, encoding="utf-8"):
            l = l.strip()
            if l and not l.startswith("#") and "|" in l:
                trecho, motivo = [x.strip() for x in l.split("|", 1)]
                aceites.append((trecho.lower(), motivo))
    return aceites


def achar(pasta, padrao):
    return sorted(glob.glob(os.path.join(pasta, padrao)))


def auditar(pasta):
    pasta = os.path.abspath(pasta)
    B, A, OK, ACEITOS = [], [], [], []      # blocks, warnings, what passed, what was accepted

    if not os.path.isdir(pasta):
        return {"pasta": pasta, "veredito": "BLOCKED", "bloqueios": [f"folder does not exist: {pasta}"],
                "alertas": [], "ok": [], "aceitos": []}

    todos = os.listdir(pasta)
    resumes = [f for f in todos if re.match(r".*Resume.*\.(pdf|docx)$", f, re.I) and "and_Letter" not in f]
    ats = [f for f in resumes if "ATS" in f]
    formatados = [f for f in resumes if "ATS" not in f]
    cartas_pdf = [f for f in todos if re.match(r".*Cover_Letter.*\.pdf$", f, re.I)]
    combinados = [f for f in todos if re.match(r".*Resume_and_Letter.*\.pdf$", f, re.I)]
    email = os.path.join(pasta, "Email.md")

    # 5. required files. Entregaveis.md (defined by the human before building) can waive the ATS version.
    ent = os.path.join(pasta, "Entregaveis.md")
    sem_ats = os.path.exists(ent) and re.search(r"^\s*-?\s*ats\s*:\s*no", open(ent, encoding="utf-8").read(), re.I | re.M)
    obrigatorios = [("formatted resume .docx", any(f.endswith(".docx") for f in formatados)),
                    ("formatted resume .pdf", any(f.endswith(".pdf") for f in formatados)),
                    ("Notas.md", "Notas.md" in todos)]
    if not sem_ats:
        obrigatorios.insert(2, ("ATS resume .docx", any(f.endswith(".docx") for f in ats)))
    for obrig, cond in obrigatorios:
        (OK if cond else B).append(f"present: {obrig}" if cond else f"required file missing: {obrig}")

    # 6. FATOS.md up to date
    r = subprocess.run([sys.executable, os.path.join(AQUI, "render_fatos.py"), "--check"],
                       capture_output=True, text=True, cwd=AQUI)
    (OK if r.returncode == 0 else B).append("FATOS.md is up to date with fatos.yaml" if r.returncode == 0
                                            else "FATOS.md differs from fatos.yaml (run render_fatos.py)")

    # 1 and 2. facts + asterisk + number — over the whole folder, once
    achados, _ = CF.varrer([pasta], usar_numeros=True)
    grupos = {}                                  # (regra, match) -> {"a": achado, "arqs": [...]}
    for a in achados:
        if a["severidade"] not in ("bloqueia", "alerta"):
            continue
        g = grupos.setdefault((a["regra"], a["match"]), {"a": a, "arqs": []})
        nome = os.path.basename(a["arquivo"])
        if nome not in g["arqs"]:
            g["arqs"].append(nome)
    for (regra, _), g in grupos.items():
        a = g["a"]
        onde = ", ".join(g["arqs"][:4]) + (f" (+{len(g['arqs']) - 4})" if len(g["arqs"]) > 4 else "")
        msg = f"[{regra}] “…{a['trecho']}…” — {a['motivo']}  \n  ↳ {onde}"
        (B if a["severidade"] == "bloqueia" else A).append(msg)
    if not any(a["severidade"] == "bloqueia" for a in achados):
        OK.append("no banned string or literal asterisk in outgoing material")

    # 3. pages
    if not (formatados or ats):
        pass
    for f in sorted(formatados + ats + cartas_pdf + combinados):
        if not f.lower().endswith(".pdf"):
            continue
        alvo = (PAGINAS["carta"] if "Cover_Letter" in f
                else PAGINAS["resume"] + PAGINAS["carta"] if f in combinados
                else PAGINAS["ats"] if "ATS" in f else PAGINAS["resume"])
        n = paginas(os.path.join(pasta, f))
        if alvo is None:
            OK.append(f"pages: {f} has {n} (ATS has no limit)")
        elif n is None:
            A.append(f"could not count pages of {f}")
        elif n > alvo:
            B.append(f"pages off target: {f} has {n}, maximum {alvo}")
        else:
            OK.append(f"pages ok: {f} ({n}/{alvo})")
    for f in [x for x in formatados + ats if x.endswith(".docx")]:
        if f[:-5] + ".pdf" not in todos:
            A.append(f"{f} has no matching PDF: pages not checked")

    # 3b. rule: no "Earlier" section in the resume
    for f in sorted(formatados + ats):
        if f.lower().endswith(".pdf"):
            r_ = subprocess.run(["pdftotext", os.path.join(pasta, f), "-"], capture_output=True, text=True)
            if re.search(r"^\s*earlier( experience)?\s*$", r_.stdout or "", re.I | re.M):
                B.append(f"Earlier section in the resume: {f} (rule: all experiences under Experience; EARLIER = [] in the builder)")

    # 3c. rule: the date of a position never breaks onto two lines
    for f in sorted(formatados):
        if f.lower().endswith(".pdf"):
            r_ = subprocess.run(["pdftotext", "-layout", os.path.join(pasta, f), "-"], capture_output=True, text=True)
            if re.search(r"\b[A-Z][a-z]{2} \d{4} -\s*$", r_.stdout or "", re.M):
                B.append(f"date broken across two lines in a position: {f} (the company descriptor goes on the second line; shorten the title)")

    # 4. checar_texto (text check)
    aceites = ler_aceites(pasta)

    def registrar_texto(rotulo, itens):
        for it in itens:
            it = it.replace(pasta + os.sep, "")
            hit = next((m for t, m in aceites if t in it.lower()), None)
            if hit:
                ACEITOS.append(f"{rotulo}: {it}  ⇐ accepted: {hit}")
            else:
                B.append(f"text ({rotulo}): {it}")

    for c in cartas_pdf:
        outros = [email] if os.path.exists(email) else []
        registrar_texto(c + (" x Email.md" if outros else ""),
                        problemas_texto(rodar_texto(os.path.join(pasta, c), *outros), ritmo=True))
    if os.path.exists(email) and not cartas_pdf:
        registrar_texto("Email.md", problemas_texto(rodar_texto(email), ritmo=True))
    for f in formatados:
        if f.endswith(".pdf"):
            registrar_texto(f, problemas_texto(rodar_texto(os.path.join(pasta, f)), ritmo=False))
    if not any(b.startswith("text (") for b in B):
        OK.append("checar_texto.py has no warnings (or they were accepted with a reason)")

    # QUICK READ — warns only. See checar_cv.py.
    tese_f = os.path.join(pasta, "tese.txt")
    tese = ([l.strip() for l in open(tese_f, encoding="utf-8") if l.strip() and not l.startswith("#")]
            if os.path.exists(tese_f) else [])
    if not tese:
        A.append("no tese.txt in the folder: cannot check whether the package thesis reaches page 1")
    for f in [x for x in formatados if x.endswith(".pdf")]:
        r = subprocess.run([sys.executable, os.path.join(AQUI, "checar_cv.py"),
                            os.path.join(pasta, f), *tese], capture_output=True, text=True, timeout=60)
        for l in r.stdout.splitlines():
            if l.strip().startswith("! "):
                A.append(f"quick read ({f}): {l.strip()[2:]}")
            elif l.strip().startswith("ok:"):
                OK.append(f"quick read ok: {f}")

    # did the builder import fatos.py? (warning: the rule is the builder's, not the material's)
    scripts = [p for p in glob.glob(os.path.join(pasta, "**", "build_*.py"), recursive=True)]
    for s in scripts:
        src = open(s, encoding="utf-8").read()
        if not re.search(r"^\s*(?:import\s+fatos|from\s+fatos\s+import)", src, re.M):
            A.append(f"{os.path.relpath(s, pasta)} does not import fatos.py: facts may have been typed by hand")

    return {"pasta": pasta, "veredito": "BLOCKED" if B else "PASS",
            "bloqueios": B, "alertas": A, "ok": OK, "aceitos": ACEITOS}


def formatar(r):
    L = []
    nome = os.path.basename(r["pasta"])
    L.append(f"# Audit — {nome}\n")
    L.append(f"*{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}*\n")
    L.append(("## ✅ PASS" if r["veredito"] == "PASS" else "## ❌ BLOCKED") + "\n")
    if r["bloqueios"]:
        L.append("### Failed\n")
        L += [f"- ❌ {b}" for b in r["bloqueios"]] + [""]
    if r["alertas"]:
        L.append("### Warnings (do not fail)\n")
        L += [f"- ⚠️ {a}" for a in r["alertas"]] + [""]
    if r["aceitos"]:
        L.append("### Accepted with a reason\n")
        L += [f"- ☑️ {a}" for a in r["aceitos"]] + [""]
    L.append("### Passed\n")
    L += [f"- ✅ {o}" for o in r["ok"]]
    if r["veredito"] == "PASS":
        L.append("\n*Mechanical gate cleared. Sending is still the human's.*")
    else:
        L.append("\n*Back to the builder. Fix the material (or the yaml, if the rule is wrong) and run again.*")
    return "\n".join(L) + "\n"


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    if not args:
        print(__doc__)
        return 2
    r = auditar(args[0])
    if "--json" in argv:
        print(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        texto = formatar(r)
        print(texto)
        if "--gravar" in argv:
            with open(os.path.join(r["pasta"], "Auditoria.md"), "w", encoding="utf-8") as f:
                f.write(texto)
    return 0 if r["veredito"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
