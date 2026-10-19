"""estado.json: o que já foi visto, para não re-triar. Chave = fonte#id; a semântica pega repost em agregador."""
import json
import os
from datetime import date, timedelta

CAMINHO = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "estado.json")


def carregar(caminho=CAMINHO):
    if not os.path.exists(caminho):
        return {"vagas": {}, "semantica": {}}
    with open(caminho, encoding="utf-8") as f:
        return json.load(f)


def salvar(estado, caminho=CAMINHO, dias_retencao=90):
    corte = (date.today() - timedelta(days=dias_retencao)).isoformat()
    estado["vagas"] = {k: v for k, v in estado["vagas"].items() if v.get("visto_em", "9999") >= corte}
    vivas = {v.get("chave_semantica") for v in estado["vagas"].values()}
    estado["semantica"] = {k: v for k, v in estado.get("semantica", {}).items() if k in vivas}
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(estado, f, ensure_ascii=False, indent=1, sort_keys=True)


def situacao(estado, v):
    """'nova' | 'mudou' | 'vista' | 'repost' (mesma empresa+título já vista em outra fonte)."""
    ant = estado["vagas"].get(v.chave)
    if ant:
        return "vista" if ant.get("hash") == v.hash else "mudou"
    outra = estado.get("semantica", {}).get(v.chave_semantica)
    # repost = a mesma empresa+título vindo de OUTRA fonte. Irmãs da mesma fonte (uma vaga por país) são vagas distintas.
    if outra and outra != v.chave and outra.split("#")[0] != v.fonte:
        return "repost"
    return "nova"


def registrar(estado, v, r, triada=False, pendente=False, no_notion=True):
    hoje = date.today().isoformat()
    ant = estado["vagas"].get(v.chave, {})
    estado["vagas"][v.chave] = {
        "empresa": v.empresa, "titulo": v.titulo, "link": v.link, "hash": v.hash,
        "chave_semantica": v.chave_semantica, "prioridade": r.prioridade, "score": r.score,
        "regra": r.regra, "motivo": r.motivo, "trilha": r.trilha,
        "primeiro_visto": ant.get("primeiro_visto", hoje), "visto_em": hoje,
        "triada": triada or ant.get("triada", False), "pendente_triagem": pendente,
        "no_notion": no_notion and (ant.get("no_notion", True) if ant.get("hash") == v.hash else True) if no_notion else False,
        "notion_page": ant.get("notion_page", ""), "veredito": ant.get("veredito", ""),
    }
    estado.setdefault("semantica", {}).setdefault(v.chave_semantica, v.chave)
