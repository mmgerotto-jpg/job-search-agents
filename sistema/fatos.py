#!/usr/bin/env python3
"""
fatos.py — loads fatos.yaml for generators to IMPORT, instead of retyping.

    import fatos as FT
    FT.F.northwind.carteira               # "4 to 6 mid-size retail clients"
    FT.periodo("northwind")               # "March 2022 - August 2025"
    FT.cargo("northwind")                 # "Senior Analyst"  (canonical for a resume)
    FT.linha_idiomas()                    # "Portuguese (native), English (fluent)"

If the yaml is corrected, every future build comes out corrected.

On import, the module CHECKS what it can check by itself (dates in order, banned-string regexes compiling,
optional sums you declare) and raises FatosInconsistentes if the yaml stops adding up. Failing loudly is the point.

Which yaml: the FATOS_YAML variable, else sistema/fatos.yaml, else sistema/fatos.example.yaml.

    python3 fatos.py                 # checks and prints a summary
    python3 fatos.py northwind.carteira   # prints a value by dotted path
"""
import os
import re
import sys

import yaml

AQUI = os.path.dirname(os.path.abspath(__file__))


def _caminho_padrao():
    if os.environ.get("FATOS_YAML"):
        return os.environ["FATOS_YAML"]
    proprio = os.path.join(AQUI, "fatos.yaml")
    return proprio if os.path.exists(proprio) else os.path.join(AQUI, "fatos.example.yaml")


CAMINHO_YAML = _caminho_padrao()

MESES_EN = ["January", "February", "March", "April", "May", "June", "July",
            "August", "September", "October", "November", "December"]


class FatosInconsistentes(Exception):
    pass


class Node:
    """Dict with dot access. A missing key raises AttributeError, never returns empty:
    a generator that asks for a fact that does not exist must break, not print 'None'."""

    def __init__(self, dados):
        object.__setattr__(self, "_d", dados)

    def __getattr__(self, nome):
        try:
            return _envolver(self._d[nome])
        except KeyError:
            raise AttributeError(f"fatos.yaml has no '{nome}' (keys: {', '.join(self._d)})") from None

    def __getitem__(self, chave):
        return _envolver(self._d[chave])

    def __contains__(self, chave):
        return chave in self._d

    def __iter__(self):
        return iter(self._d)

    def items(self):
        return ((k, _envolver(v)) for k, v in self._d.items())

    def bruto(self):
        return self._d


def _envolver(v):
    if isinstance(v, dict):
        return Node(v)
    if isinstance(v, list):
        return [_envolver(x) for x in v]
    return v


def carregar(caminho=CAMINHO_YAML):
    with open(caminho, encoding="utf-8") as f:
        return yaml.safe_load(f)


BRUTO = carregar()
F = Node(BRUTO)


# ---------------------------------------------------------------------------
# Dates, titles, contact: what the generators need
# ---------------------------------------------------------------------------
def _ym(s):
    ano, mes = s.split("-")
    return int(ano), int(mes)


def mes_ano_en(s):
    a, m = _ym(s)
    return f"{MESES_EN[m - 1]} {a}"


def mm_aaaa(s):
    a, m = _ym(s)
    return f"{m:02d}/{a}"


def periodo(chave, sep=" - "):
    """'March 2022 - August 2025'. Month precision, always."""
    e = BRUTO["emprego"][chave]
    return f"{mes_ano_en(e['inicio'])}{sep}{mes_ano_en(e['fim'])}"


def cargo(chave):
    """Canonical title for a resume."""
    return BRUTO["emprego"][chave]["cargo_curriculo"]


def cargos(chave):
    """All titles, in chronological order (for a form with progression)."""
    return list(BRUTO["emprego"][chave]["cargos"])


def empresa(chave):
    return BRUTO["emprego"][chave]["empresa"]


def nome_curto(chave):
    e = BRUTO["emprego"][chave]
    return e.get("empresa_curta", e["empresa"])


def linha_idiomas(sep=", ", completa=False):
    """Default: the short line. Pass completa=True only when the role asks for the weakest language."""
    chave = "linha_en" if completa else "linha_en_padrao"
    return BRUTO["identidade"]["idiomas"][chave].replace(", ", sep)


def linha_contato(ats=False):
    c = BRUTO["identidade"]["contato"]
    tel = c["telefone_ats"] if ats else c["telefone"]
    return f"{c['email']} · {tel} · {c['linkedin']}"


def educacao():
    return BRUTO["identidade"]["formacao"]["frase_en"]


def instituicao():
    return BRUTO["identidade"]["formacao"]["instituicao"]


def numeros_permitidos():
    """Every numeric value that appears in some value of the yaml (outside banidas, changelog, pendencias, meta, materiais).
    The VALUE is compared, not the unit."""
    ignorar = {"banidas", "changelog", "pendencias", "meta", "materiais"}
    achados = set()

    def somar(texto):
        for m in QTD_GERAL.finditer(texto):
            n = _norm_num(m.group(0))
            achados.add(n)
            achados.add(re.sub(r"^(?:us\$|r\$|€)", "", n))     # also without the currency

    def andar(v):
        if isinstance(v, dict):
            for x in v.values():
                andar(x)
        elif isinstance(v, list):
            for x in v:
                andar(x)
        elif isinstance(v, (int, float)) and not isinstance(v, bool):
            somar(str(v))
        elif isinstance(v, str):
            somar(v)

    for k, v in BRUTO.items():
        if k not in ignorar:
            andar(v)
    for extra in BRUTO.get("numeros_extras_permitidos", []):
        somar(extra)
    return achados


_MOEDA_NUM_SUF = r"(?:US\$|R\$|€)?\s?\d+(?:[.,]\d+)*\s?(?:[kKmMbB]\b|%|x\b)?"
QTD_GERAL = re.compile(_MOEDA_NUM_SUF)

# What the auditor CHECKS in material: a quantity with a unit (money, %, k/M, x, or number + noun).
# A bare year, phone number and date are left out. Add nouns from your domain.
TOKEN_NUM = re.compile(
    r"(?:US\$|R\$|€)\s?\d[\d.,]*\s?[kKmMbB]?\b"
    r"|\d[\d.,]*\s?%"
    r"|\b\d[\d.,]*\s?[kKM]\b"
    r"|\b\d+(?:\.\d+)?\s?x\b"
    r"|\b\d[\d.,]*\s+(?:months?|weeks?|"
    r"products?|features?|agents?|"
    r"clients?|accounts?|SKUs?|orders|years?)\b",
    re.IGNORECASE,
)


def _norm_num(tok):
    """'US$ 2,500' -> 'us$2500' ; '1.5M' -> '1.5m' ; '70 %' -> '70%'."""
    m = re.search(r"(US\$|R\$|€)?\s?(\d+(?:[.,]\d+)*)\s?([kKmMbB]\b|%|x\b)?", tok)
    if not m:
        return tok.lower().strip()
    moeda, num, suf = m.groups()
    if re.fullmatch(r"\d{1,3}(?:[.,]\d{3})+", num):        # thousands separator
        num = re.sub(r"[.,]", "", num)
    else:
        num = num.replace(",", ".")
        if "." in num:
            num = num.rstrip("0").rstrip(".")
    return ((moeda or "") + num + (suf or "")).lower()


# ---------------------------------------------------------------------------
# Checks: fail loudly if the yaml stops adding up
# ---------------------------------------------------------------------------
def conferir():
    problemas = []

    # well-formed dates, in order
    for chave, e in BRUTO["emprego"].items():
        try:
            if _ym(e["inicio"]) > _ym(e["fim"]):
                problemas.append(f"emprego.{chave}: start after end")
        except Exception:
            problemas.append(f"emprego.{chave}: date not in YYYY-MM format")
        if e["cargo_curriculo"] not in e["cargos"]:
            problemas.append(f"emprego.{chave}: cargo_curriculo is not in the list of cargos")

    # banned strings compile and have a valid scope and severity
    for b in BRUTO.get("banidas", []):
        try:
            re.compile(b["padrao"], re.IGNORECASE)
        except re.error as ex:
            problemas.append(f"banidas.{b['id']}: invalid regex ({ex})")
        if b["escopo"] not in ("todos", "materiais") or b["severidade"] not in ("bloqueia", "alerta"):
            problemas.append(f"banidas.{b['id']}: invalid scope/severity")

    # sums YOU want to lock: add them here (e.g. the sum of months in a block == declared years)
    # if sum(BRUTO["consultoria"]["meses"].values()) != 73: problemas.append("...")

    if problemas:
        raise FatosInconsistentes("\n  - " + "\n  - ".join(problemas))


conferir()


def _caminho(caminho):
    v = F
    for parte in caminho.split("."):
        v = getattr(v, parte) if isinstance(v, Node) else v[int(parte)]
    return v


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):  # Windows consoles default to cp1252; accents and arrows would crash
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(encoding="utf-8")
    if len(sys.argv) > 1:
        v = _caminho(sys.argv[1])
        print(v.bruto() if isinstance(v, Node) else v)
    else:
        print(f"fatos.yaml OK ({CAMINHO_YAML})")
        for k in BRUTO["emprego"]:
            print(f"  {empresa(k)}: {cargo(k)} ({' → '.join(cargos(k))}), {periodo(k)}")
        print(f"  allowed numbers: {len(numeros_permitidos())} tokens")
        for p in BRUTO.get("pendencias", []):
            print(f"  ⚠️ pending [{p['id']}]: {' '.join(p['texto'].split())[:110]}")
