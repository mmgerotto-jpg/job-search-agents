#!/usr/bin/env python3
"""
checar_fatos.py — sweeps folder(s) looking for the banned strings from fatos.yaml.

    python3 checar_fatos.py <folder|file> [...]
        [--relatorio out.md]       writes a markdown report
        [--numeros]                also flags a number with a unit that does not exist in fatos.yaml
        [--mentions]               also lists mentions in internal documents and docstrings
        [--desde YYYY-MM-DD]       only files modified from that date (recent regression)
        [--json]

Exits 1 if it finds a BLOCK in outgoing material (PDF, docx, email, letter, a string emitted by a generator).

What counts as what — and why it matters:

  material    .pdf, .docx, and .md whose NAME matches materiais.padroes_materiais (Email.md, Carta_*.md...),
              plus literal strings that a .py EMITS. Applies the rules with scope "todos" and "materiais".
              It is what goes out. Blocks.

  internal    other .md/.txt/.csv. Only the rules with scope "todos", and only as a MENTION: a history
              quotes "ten years of experience" precisely to explain the error. Does not block.

  quotation   docstring or comment of a .py. Same: a generator may describe the corrected error
              in its own docstring. Does not block. (And, by the builder's rule, reasoning should not
              live there; it should go in Notas.md.)

Structural checks on PDF/docx (they do not come from the yaml):
  * literal asterisk — add_runs only splits on `**`; a single asterisk passes and shows on paper.
"""
import ast
import io
import json
import os
import re
import subprocess
import sys
import tokenize

import fatos as FT

D = FT.BRUTO
PADROES_MATERIAIS = [p.lower() for p in D["materiais"]["padroes_materiais"]]
REGRAS = [{**b, "_re": re.compile(b["padrao"], re.IGNORECASE)} for b in D.get("banidas", [])]
PERMITIDOS = FT.numeros_permitidos()

IGNORAR_DIRS = {".git", "__pycache__", "node_modules", ".claude", ".venv", "relatorios"}
# The yaml and the generated md quote the banned strings by definition.
IGNORAR_ARQUIVOS = {"fatos.yaml", "FATOS.md", ".DS_Store"}
EXTENSOES = {".md", ".txt", ".csv", ".py", ".docx", ".pdf"}


# ---------------------------------------------------------------------------
# Reading
# ---------------------------------------------------------------------------
def texto_pdf(caminho):
    try:
        r = subprocess.run(["pdftotext", caminho, "-"], capture_output=True, text=True, timeout=60)
        return r.stdout
    except (OSError, subprocess.TimeoutExpired):
        return ""


def texto_docx(caminho):
    try:
        from docx import Document
        d = Document(caminho)
    except Exception:
        return ""
    partes = [p.text for p in d.paragraphs]
    for t in d.tables:
        for row in t.rows:
            for cel in row.cells:
                partes.append(cel.text)
    for s in d.sections:
        for bloco in (s.header, s.footer):
            partes += [p.text for p in bloco.paragraphs]
    return "\n".join(partes)


def segmentos_py(caminho):
    """[(text, class, line)] — separates what the script EMITS from docstring or comment."""
    try:
        src = open(caminho, encoding="utf-8").read()
        arvore = ast.parse(src)
    except (OSError, SyntaxError, UnicodeDecodeError):
        return []
    doc_ids = set()
    for no in ast.walk(arvore):
        if isinstance(no, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and no.body:
            p = no.body[0]
            if isinstance(p, ast.Expr) and isinstance(p.value, ast.Constant) and isinstance(p.value.value, str):
                doc_ids.add(id(p.value))
    saida = []
    for no in ast.walk(arvore):
        if isinstance(no, ast.Constant) and isinstance(no.value, str):
            classe = "docstring" if id(no) in doc_ids else "emitted"
            saida.append((no.value, classe, no.lineno))
    try:
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            if tok.type == tokenize.COMMENT:
                saida.append((tok.string, "comment", tok.start[0]))
    except (tokenize.TokenError, IndentationError):
        pass
    return saida


def eh_material_por_nome(nome):
    n = nome.lower()
    return any(p in n for p in PADROES_MATERIAIS)


def itens(caminho):
    """Yields (text, class, base_line) for a file."""
    ext = os.path.splitext(caminho)[1].lower()
    nome = os.path.basename(caminho)
    if ext == ".pdf":
        yield texto_pdf(caminho), "material", 0
    elif ext == ".docx":
        yield texto_docx(caminho), "material", 0
    elif ext == ".py":
        for t, c, ln in segmentos_py(caminho):
            yield t, c, ln - 1
    else:
        try:
            t = open(caminho, encoding="utf-8").read()
        except (OSError, UnicodeDecodeError):
            return
        yield t, ("material" if eh_material_por_nome(nome) else "internal"), 0


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------
def trecho(texto, ini, fim, margem=45):
    a, b = max(0, ini - margem), min(len(texto), fim + margem)
    return re.sub(r"\s+", " ", texto[a:b]).strip()


def linha_de(texto, pos, base):
    return base + texto.count("\n", 0, pos) + 1


def achar(texto, classe, base, caminho, usar_numeros):
    achados = []
    sai = classe in ("material", "emitted")
    ext = os.path.splitext(caminho)[1].lower()

    for r in REGRAS:
        if r["escopo"] == "materiais" and not sai:
            continue
        for m in r["_re"].finditer(texto):
            if r.get("nao_se_antes") and re.search(r["nao_se_antes"], texto[max(0, m.start() - 80):m.start()], re.I):
                continue
            achados.append({
                "arquivo": caminho, "classe": classe, "regra": r["id"],
                "severidade": r["severidade"] if sai else "mention",
                "motivo": r["motivo"], "trecho": trecho(texto, m.start(), m.end()),
                "match": re.sub(r"\s+", " ", m.group(0)).lower(),
                "linha": linha_de(texto, m.start(), base),
            })

    # literal asterisk: only in PDF/docx (in .md, ** is legitimate markup)
    if ext in (".pdf", ".docx"):
        for m in re.finditer(r"\*", texto):
            achados.append({
                "arquivo": caminho, "classe": classe, "regra": "literal_asterisk", "severidade": "bloqueia",
                "motivo": "Literal asterisk on paper. add_runs only splits on '**'; a single asterisk passes and prints.",
                "trecho": trecho(texto, m.start(), m.end()), "match": "*", "linha": 0,
            })
            break  # one per file is enough

    if usar_numeros and sai:
        vistos = set()
        for m in FT.TOKEN_NUM.finditer(texto):
            n = FT._norm_num(m.group(0))
            if n in PERMITIDOS or n in vistos:
                continue
            vistos.add(n)
            achados.append({
                "arquivo": caminho, "classe": classe, "regra": "number_not_in_facts", "severidade": "alerta",
                "motivo": "A number with a unit that does not exist in fatos.yaml. If it is a fact, it goes in the yaml; if not, it leaves the material.",
                "trecho": trecho(texto, m.start(), m.end()), "match": n,
                "linha": linha_de(texto, m.start(), base),
            })
    return achados


def varrer(caminhos, usar_numeros=False, desde=None):
    achados, arquivos = [], 0
    for raiz in caminhos:
        if os.path.isfile(raiz):
            lista = [raiz]
        else:
            lista = []
            for d, subs, fs in os.walk(raiz):
                subs[:] = [s for s in subs if s not in IGNORAR_DIRS]
                for f in fs:
                    if f in IGNORAR_ARQUIVOS or f.startswith("~$") or f.startswith("."):
                        continue
                    if os.path.splitext(f)[1].lower() in EXTENSOES:
                        lista.append(os.path.join(d, f))
        for c in sorted(lista):
            if desde and os.path.getmtime(c) < desde:
                continue
            arquivos += 1
            for texto, classe, base in itens(c):
                achados += achar(texto, classe, base, c, usar_numeros)
    return achados, arquivos


def bloqueios(achados):
    return [a for a in achados if a["severidade"] == "bloqueia"]


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------
def rel(caminho, base):
    try:
        return os.path.relpath(caminho, base)
    except ValueError:
        return caminho


def formatar(achados, arquivos, base, mencoes=False):
    out = []
    add = out.append
    bl = [a for a in achados if a["severidade"] == "bloqueia"]
    al = [a for a in achados if a["severidade"] == "alerta"]
    me = [a for a in achados if a["severidade"] == "mention"]

    add(f"# checar_fatos — {arquivos} files swept\n")
    add(f"- ❌ **BLOCKED** (outgoing material): **{len(bl)}**")
    add(f"- ⚠️ **WARNING** (outgoing material): **{len(al)}**")
    add(f"- ℹ️ mentions in internal documents / docstrings / comments: {len(me)} (do not block)\n")

    def bloco(titulo, lista):
        if not lista:
            return
        add(f"## {titulo}\n")
        por_arquivo = {}
        for a in lista:
            por_arquivo.setdefault(a["arquivo"], []).append(a)
        for arq, xs in por_arquivo.items():
            mt = ""
            try:
                import datetime
                mt = datetime.datetime.fromtimestamp(os.path.getmtime(arq)).strftime("%Y-%m-%d")
            except OSError:
                pass
            add(f"### `{rel(arq, base)}` *(modified {mt})*")
            vistos = set()
            for a in xs:
                k = (a["regra"], a["trecho"])
                if k in vistos:
                    continue
                vistos.add(k)
                ln = f" l.{a['linha']}" if a["linha"] else ""
                add(f"- **{a['regra']}**{ln} — “…{a['trecho']}…”")
                add(f"  - {a['motivo']}")
            add("")

    bloco("❌ BLOCKED", bl)
    bloco("⚠️ WARNING", al)
    if mencoes:
        bloco("ℹ️ Internal mentions (they quote the string to explain the error)", me)
    elif me:
        add("## ℹ️ Internal mentions\n")
        por = {}
        for a in me:
            por.setdefault(rel(a["arquivo"], base), set()).add(a["regra"])
        for arq, rs in sorted(por.items()):
            add(f"- `{arq}`: {', '.join(sorted(rs))}")
        add("\n*(use `--mentions` to see the excerpts)*\n")
    if not (bl or al):
        add("✅ No block or warning in outgoing material.\n")
    return "\n".join(out)


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    flags = [a for a in argv if a.startswith("--")]
    relatorio = None
    if "--relatorio" in flags:
        i = argv.index("--relatorio")
        relatorio = argv[i + 1]
        args = [a for a in args if a != relatorio]
    if not args:
        print(__doc__)
        return 2
    desde = None
    if "--desde" in flags:
        import datetime
        i = argv.index("--desde")
        desde = datetime.datetime.strptime(argv[i + 1], "%Y-%m-%d").timestamp()
        args = [a for a in args if a != argv[i + 1]]
    achados, n = varrer(args, usar_numeros="--numeros" in flags, desde=desde)
    base = os.path.commonpath([os.path.abspath(a) for a in args]) if len(args) > 1 else os.path.abspath(args[0])
    if os.path.isfile(base):
        base = os.path.dirname(base)

    if "--json" in flags:
        print(json.dumps(achados, ensure_ascii=False, indent=2))
    else:
        texto = formatar(achados, n, base, mencoes="--mentions" in flags)
        print(texto)
        if relatorio:
            os.makedirs(os.path.dirname(os.path.abspath(relatorio)), exist_ok=True)
            with open(relatorio, "w", encoding="utf-8") as f:
                f.write(texto + "\n")
            print(f"\nreport: {relatorio}")
    return 1 if bloqueios(achados) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
