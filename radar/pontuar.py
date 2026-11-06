"""Knockouts + score -> priority, always with the REASON. Zero LLM."""
import re
from dataclasses import dataclass, field
from .modelo import norm

PRIORIDADES = ("DESCARTAR", "IGNORAR", "BAIXA", "MEDIA", "ALTA")


@dataclass
class Resultado:
    prioridade: str
    score: int = 0
    trilha: str = ""
    motivo: str = ""              # the knockout that fired, or why it ended up where it did
    regra: str = ""
    pontos: list = field(default_factory=list)   # [(points, why)]
    geografia: str = ""           # forte | fraca | eua | neutra | bloqueada


def _texto(v, escopo):
    t = {"titulo": norm(v.titulo), "descricao": norm(v.descricao), "local": norm(v.local),
         "empresa": norm(v.empresa), "tipo": norm(v.tipo)}
    if escopo == "tudo":
        return " | ".join((t["titulo"], t["local"], t["descricao"]))
    return t[escopo]


def casa_regra(r, v, trilha=""):
    """Returns the excerpt that fired the rule, or None."""
    if r.get("so_trilha") and trilha not in r["so_trilha"]:
        return None
    local = norm(v.local)
    if r.get("so_se_local_rx") and not r["so_se_local_rx"].search(local):
        return None
    if r.get("excecao_local_rx") and r["excecao_local_rx"].search(local):
        return None
    texto = _texto(v, r["escopo"])
    if r.get("excecao_global_rx") and r["excecao_global_rx"].search(texto):
        return None
    achados = []
    for m in r["padrao_rx"].finditer(texto):
        if r.get("excecao_rx"):
            ini, fim = max(0, m.start() - r["janela"]), m.end() + r["janela"]
            if r["excecao_rx"].search(texto[ini:fim]):
                continue
        achados.append(m)
    if len(achados) < r["min_ocorrencias"]:
        return None
    m = achados[0]
    return texto[max(0, m.start() - 30): m.end() + 30].strip()


def achar_trilha(c, titulo):
    t = norm(titulo)
    for nome in ("A", "B", "C"):
        for rx in c["trilhas"][nome]["_rx"]:
            if rx.search(t):
                return nome
    return ""


def geografia(c, v):
    g, loc = c["geografia"], norm(v.local)
    forte = bool(g["aceita_forte"]["_rx"].search(loc)) if loc else False
    e = g.get("eua_remoto")
    if e and loc and not forte and e["_rx"].search(loc):
        return "eua"        # remote US: MEDIA with a warning (visa to check later); on-site US falls under "bloqueia"
    if g["bloqueia"]["_rx"].search(loc) and not forte:
        return "bloqueada"
    if forte:
        return "forte"
    if g["aceita_fraca"]["_rx"].search(loc):
        return "fraca"
    return "neutra"


def avaliar(c, v):
    trilha = achar_trilha(c, v.titulo)
    if not trilha:
        return Resultado("IGNORAR", motivo="title outside the tracks")

    # A track match only counts if the title knockout does not knock it down afterwards.
    for r in c["eliminatorios"]:
        trecho = casa_regra(r, v, trilha)
        if trecho is not None:
            return Resultado("DESCARTAR", trilha=trilha, regra=r["id"],
                             motivo=f"{r['motivo']}: “{trecho}”")

    geo = geografia(c, v)
    e = c["geografia"].get("eua_remoto")
    if e and geo in ("forte", "neutra") and not e["_rx_explicito"].search(norm(v.local)) and e["_rx_texto"].search(_texto(v, "tudo")):
        geo = "eua"         # ambiguous location ("Remote"), but the text requires being/working in the US
    if geo == "bloqueada":
        return Resultado("DESCARTAR", trilha=trilha, regra="geografia",
                         motivo=f"Geography outside the plan: “{v.local}”", geografia=geo)

    pts = [(c["trilhas"][trilha]["pontos"], f"track {trilha}")]
    n = c["nivel_alvo"]
    if any(rx.search(norm(v.titulo)) for rx in n["_rx"]):
        pts.append((n["pontos"], "Staff/Principal/Lead level"))
    if geo == "forte":
        pts.append((c["geografia"]["aceita_forte"]["pontos"], "strong geography"))
    elif geo == "eua":
        pts.append((e["pontos"], "remote US: visa/work authorization to check later"))

    desc = norm(v.descricao)
    sinais = [rx for rx in c["_sinais_rx"] if rx.search(desc)]
    if sinais:
        pts.append((min(len(sinais), c["sinais_descricao"]["teto"]), f"{len(sinais)} signals in the description"))

    emp = norm(v.empresa) + " " + norm(v.fundo)
    for chave, rotulo in (("fundos_parceiros", "partner fund"), ("alumni", "alumni company"),
                          ("ecossistema_golfo", "regional ecosystem")):
        b = c["bonus"][chave]
        if any(re.search(r"\b" + re.escape(norm(x)) + r"\b", emp) for x in b["empresas"]):
            pts.append((b["pontos"], rotulo))
            break

    for r in c["penalidades"]:
        trecho = casa_regra(r, v, trilha)
        if trecho is not None:
            pts.append((r["pontos"], r["motivo"]))

    score = sum(p for p, _ in pts)
    lim = c["limiares"]
    if score >= lim["alta"] and geo == "forte":
        pr = "ALTA"
    elif score >= lim["media"] and geo == "neutra":
        pr = "BAIXA"        # unrecognized location (e.g. Tokyo, Sydney): does not go to Notion
    elif score >= lim["media"]:
        pr = "MEDIA"
    else:
        pr = "BAIXA"
    if geo == "eua" and pr in ("MEDIA", "ALTA"):
        motivo = "remote US: visa/work authorization to check later"
    elif pr == "BAIXA" and geo == "neutra" and score >= lim["media"]:
        motivo = "MEDIA score, but the location is not in the plan's regions"
    elif pr == "MEDIA" and score >= lim["alta"] and geo != "forte":
        motivo = "ALTA score, but geography " + ("weak (Europe only with a human channel)" if geo == "fraca" else "not confirmed")
    else:
        motivo = ""
    return Resultado(pr, score=score, trilha=trilha, pontos=pts, geografia=geo, motivo=motivo)
