"""Carrega e valida criterios.yaml. Falha alto: regex inválida ou chave faltando derruba a rodada antes de gastar nada."""
import os
import re
import yaml

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ESCOPOS = {"titulo", "descricao", "local", "empresa", "tipo", "tudo"}


class CriteriosInvalidos(Exception):
    pass


def _rx(padrao, onde):
    try:
        return re.compile(padrao)
    except re.error as e:
        raise CriteriosInvalidos(f"regex inválida em {onde}: {padrao!r} ({e})")


def _regra(r, onde):
    for k in ("id", "padrao"):
        if k not in r:
            raise CriteriosInvalidos(f"{onde}: falta '{k}'")
    onde = f"{onde}/{r['id']}"
    if r.get("escopo", "tudo") not in ESCOPOS:
        raise CriteriosInvalidos(f"{onde}: escopo inválido {r.get('escopo')!r} (use {sorted(ESCOPOS)})")
    r = dict(r)
    r.setdefault("escopo", "tudo")
    r.setdefault("min_ocorrencias", 1)
    r.setdefault("janela", 120)
    for k in ("padrao", "excecao", "excecao_global", "so_se_local", "excecao_local"):
        if r.get(k):
            r[k + "_rx"] = _rx(r[k], f"{onde}.{k}")
    return r


def carregar(caminho=None):
    caminho = caminho or os.path.join(RAIZ, "criterios.yaml")
    if not os.path.exists(caminho):
        caminho = os.path.join(RAIZ, "criterios.example.yaml")   # repositorio publico: so o exemplo
    with open(caminho, encoding="utf-8") as f:
        c = yaml.safe_load(f)
    for k in ("limiares", "trilhas", "geografia", "eliminatorios", "penalidades", "bonus"):
        if k not in c:
            raise CriteriosInvalidos(f"criterios.yaml: falta a seção '{k}'")
    for k in ("alta", "media", "max_triagens_por_rodada", "max_idade_dias"):
        if k not in c["limiares"]:
            raise CriteriosInvalidos(f"limiares: falta '{k}'")
    if c["limiares"]["alta"] <= c["limiares"]["media"]:
        raise CriteriosInvalidos("limiares: 'alta' precisa ser maior que 'media'")
    for t, d in c["trilhas"].items():
        if not d.get("titulos"):
            raise CriteriosInvalidos(f"trilha {t}: sem títulos")
        d["_rx"] = [_rx(r"(?<![a-z])" + re.escape(x) + r"(?![a-z])", f"trilha {t}/{x}") for x in d["titulos"]]
    n = c.get("nivel_alvo", {})
    n["_rx"] = [_rx(r"\b" + re.escape(x) + r"\b", "nivel_alvo") for x in n.get("titulos", [])]
    c["nivel_alvo"] = n
    for x in c.get("sinais_descricao", {}).get("termos", []):
        _rx(x, "sinais_descricao")
    c["_sinais_rx"] = [re.compile(x) for x in c.get("sinais_descricao", {}).get("termos", [])]
    g = c["geografia"]
    for k in ("aceita_forte", "aceita_fraca", "bloqueia"):
        g[k]["_rx"] = _rx(g[k]["padrao"], f"geografia.{k}")
    e = g.get("eua_remoto")
    if e:
        for k in ("eua", "remoto", "texto", "local_explicito"):
            if k not in e:
                raise CriteriosInvalidos(f"geografia.eua_remoto: falta '{k}'")
        _rx(e["eua"], "geografia.eua_remoto.eua")
        _rx(e["remoto"], "geografia.eua_remoto.remoto")
        e["_rx"] = _rx(f"(?:{e['eua']}).{{0,40}}(?:{e['remoto']})|(?:{e['remoto']}).{{0,40}}(?:{e['eua']})", "geografia.eua_remoto")
        e["_rx_texto"] = _rx(e["texto"], "geografia.eua_remoto.texto")
        e["_rx_foco"] = _rx(e.get("foco_titulos", "(?!x)x"), "geografia.eua_remoto.foco_titulos")
        e["_rx_explicito"] = _rx(e["local_explicito"], "geografia.eua_remoto.local_explicito")
    ids = set()
    c["eliminatorios"] = [_regra(r, "eliminatorios") for r in c["eliminatorios"]]
    c["penalidades"] = [_regra(r, "penalidades") for r in c["penalidades"]]
    for r in c["eliminatorios"] + c["penalidades"]:
        if r["id"] in ids:
            raise CriteriosInvalidos(f"id repetido: {r['id']}")
        ids.add(r["id"])
    return c


def carregar_watchlist(caminho=None):
    caminho = caminho or os.path.join(RAIZ, "watchlist.yaml")
    if not os.path.exists(caminho):
        caminho = os.path.join(RAIZ, "watchlist.example.yaml")
    with open(caminho, encoding="utf-8") as f:
        w = yaml.safe_load(f) or {}
    for e in w.get("empresas", []):
        if e.get("ats") not in ("greenhouse", "ashby", "lever"):
            raise CriteriosInvalidos(f"watchlist: {e.get('nome')}: ats inválido {e.get('ats')!r}")
        if not e.get("slug"):
            raise CriteriosInvalidos(f"watchlist: {e.get('nome')}: falta slug")
    return w
