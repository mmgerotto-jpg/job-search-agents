#!/usr/bin/env python3
"""
varrer.py — coleta, elimina, pontua e separa o que vai para triagem. Não chama LLM, não escreve no Notion.

  python -m radar.varrer                      rodada completa (grava estado.json e saida/)
  python -m radar.varrer --sem-estado         ensaio: não grava estado, mostra o que faria
  python -m radar.varrer --validar            só confere criterios.yaml e watchlist.yaml
  python -m radar.varrer --explicar <trecho>  mostra a decisão de uma vaga (busca por link/título/empresa na coleta atual)
  python -m radar.varrer --fonte gupy         limita a uma fonte (greenhouse, ashby, lever, agregadores, gupy)
"""
import argparse
import json
import os
import re
import sys
from datetime import date, datetime, timedelta

import yaml

from . import criterios as CR
from . import estado as ES
from .checar_vaga import analisar
from .fontes import agregadores, ats, gupy
from .modelo import norm
from .pontuar import avaliar, casa_regra

RAIZ = CR.RAIZ
SAIDA = os.path.join(RAIZ, "saida")


def coletar(wl, so=None):
    vagas, erros, contagem = [], [], {}

    def tenta(rotulo, gerador):
        n = 0
        try:
            for v in gerador():
                vagas.append(v)
                n += 1
        except Exception as e:
            erros.append(f"{rotulo}: {type(e).__name__}: {e}")
        contagem[rotulo] = n

    for e in wl.get("empresas", []):
        if so and so != e["ats"]:
            continue
        tenta(f"{e['ats']}:{e['slug']}", lambda e=e: ats.ADAPTADORES[e["ats"]](e))
    fontes = wl.get("fontes", {})
    if not so or so == "agregadores":
        for nome in fontes.get("agregadores", []):
            tenta(nome, agregadores.ADAPTADORES[nome])
    if (not so or so == "gupy") and fontes.get("gupy_termos"):
        tenta("gupy", lambda: gupy.buscar(fontes["gupy_termos"]))
    return vagas, erros, contagem


def no_funil(funil, v):
    emp, tit = norm(v.empresa), norm(v.titulo)
    for f in funil.get("em_andamento", []):
        if norm(f["empresa"]) in emp:
            if f.get("cargo") and norm(f["cargo"]) in tit:
                return "ja_aplicou"
            return "empresa_no_funil"
    return ""


def velha(v, dias):
    if not v.publicada:
        return False
    try:
        return datetime.strptime(v.publicada, "%Y-%m-%d").date() < date.today() - timedelta(days=dias)
    except ValueError:
        return False


def expirada(v):
    try:
        return bool(v.prazo) and datetime.strptime(v.prazo[:10], "%Y-%m-%d").date() < date.today()
    except ValueError:
        return False


def slug(v):
    return re.sub(r"[^a-z0-9]+", "-", norm(v.empresa + " " + v.titulo))[:70].strip("-") + "-" + v.hash[:6]


def rodada(c, wl, funil, estado, so=None, gravar_estado=True):
    vagas, erros, contagem = coletar(wl, so)
    lim = c["limiares"]
    vistas_run, saida, stats = set(), [], {"coletadas": len(vagas), "duplicadas": 0, "antigas": 0, "ignoradas": 0,
                                           "descartadas": 0, "ja_vistas": 0}
    candidatas = []
    for v in vagas:
        if v.chave in vistas_run:
            stats["duplicadas"] += 1
            continue
        vistas_run.add(v.chave)
        # vaga listada na página de carreira está aberta, por mais antiga que seja; o corte de idade é para feeds
        eh_ats = v.fonte.split(":")[0] in ("greenhouse", "ashby", "lever")
        if (not eh_ats and velha(v, lim["max_idade_dias"])) or expirada(v):
            stats["antigas"] += 1
            continue
        r = avaliar(c, v)
        if r.prioridade == "IGNORAR":
            stats["ignoradas"] += 1
            continue
        sit = ES.situacao(estado, v)
        ant = estado["vagas"].get(v.chave, {})
        # "vista" volta à fila se ficou sem triagem por causa do teto, ou se o Notion não confirmou a escrita
        volta = sit == "vista" and r.prioridade != "DESCARTAR" and (
            ant.get("pendente_triagem") or (not ant.get("no_notion", True) and r.prioridade in ("ALTA", "MEDIA")))
        if sit in ("vista", "repost") and not volta:
            stats["ja_vistas"] += 1
            if sit == "vista":
                ES.registrar(estado, v, r, triada=ant.get("triada", False), pendente=False, no_notion=ant.get("no_notion", True))
            continue
        if r.prioridade == "DESCARTAR":
            stats["descartadas"] += 1
            ES.registrar(estado, v, r)
            continue
        candidatas.append((v, r, sit))

    # armadilha para IA: roda em toda vaga que vai a Notion/triagem (é barato e é código)
    for v, r, sit in candidatas:
        ach = analisar(v.descricao_html) if len(v.descricao) > 150 else []
        fortes = [a for a in ach if a[0] == "FORTE"]
        f = no_funil(funil, v)
        item = {"chave": v.chave, "empresa": v.empresa, "titulo": v.titulo, "local": v.local, "link": v.link,
                "fonte": v.fonte, "prioridade": r.prioridade, "score": r.score, "trilha": r.trilha,
                "pontos": [f"{p:+d} {t}" for p, t in r.pontos], "motivo": r.motivo, "salario": v.salario,
                "prazo": v.prazo, "publicada": v.publicada, "fundo": v.fundo, "situacao": sit,
                "funil": f, "armadilha": "FORTE" if fortes else ("suspeita" if ach else ""),
                "armadilha_trechos": [a[3] for a in ach[:3]], "arquivo_descricao": ""}
        saida.append((v, r, item))

    saida.sort(key=lambda x: (-("ALTA" == x[1].prioridade), -x[1].score))
    # empresa que já está no funil: só o que chega a ALTA vai ao Notion (senão vira ruído: 20 países da mesma vaga)
    candidatos_notion = [(r, i) for _, r, i in saida
                         if (r.prioridade == "ALTA" or (r.prioridade in ("MEDIA", "BAIXA") and i["funil"] != "empresa_no_funil"))
                         and (r.prioridade != "BAIXA" or lim.get("notion_incluir_baixa"))]
    teto = lim.get("max_media_notion_por_rodada", 10**9)
    medias = sorted([(r, i) for r, i in candidatos_notion if r.prioridade != "ALTA"], key=lambda x: -x[0].score)
    teto_eua = lim.get("max_eua_notion_por_rodada", 10**9)
    foco = c["geografia"].get("eua_remoto", {}).get("_rx_foco")
    eua = sorted([(r, i) for r, i in medias if r.geografia == "eua"],
                 key=lambda x: (not (foco and foco.search(norm(x[1]["titulo"]))), -x[0].score))
    adiadas = {id(i) for r, i in eua[teto_eua:]}     # EUA remoto tem teto proprio (volume alto de CS)
    resto = [(r, i) for r, i in medias if id(i) not in adiadas]
    adiadas |= {id(i) for r, i in resto[teto:]}      # ficam com no_notion=False: voltam na proxima rodada
    notion_itens = [i for r, i in candidatos_notion if id(i) not in adiadas]
    para_triar, n = [], 0
    for v, r, item in saida:
        ja_triada = estado["vagas"].get(v.chave, {}).get("triada", False)
        elegivel = (r.prioridade == "ALTA" and not ja_triada and item["funil"] != "ja_aplicou" and item["armadilha"] != "FORTE"
                    and item["funil"] != "empresa_no_funil")
        if elegivel and n < lim["max_triagens_por_rodada"]:
            n += 1
            item["triar"] = True
            os.makedirs(os.path.join(SAIDA, "descricoes"), exist_ok=True)
            item["arquivo_descricao"] = f"saida/descricoes/{slug(v)}.txt"
            with open(os.path.join(RAIZ, item["arquivo_descricao"]), "w", encoding="utf-8") as f:
                f.write(f"# {v.titulo} | {v.empresa} | {v.local}\n# {v.link}\n\n{v.descricao}\n")
            para_triar.append(item)
        else:
            item["triar"] = False
            if elegivel:
                item["motivo"] = (item["motivo"] + " Teto de triagens da rodada atingido: entra na próxima.").strip()
        vai_notion = any(i is item for i in notion_itens)
        ES.registrar(estado, v, r, triada=ja_triada, pendente=elegivel, no_notion=not vai_notion and id(item) not in adiadas)
        if item["armadilha"] == "FORTE":
            estado["vagas"][v.chave]["armadilha_forte"] = True

    return {"gerado_em": datetime.now().isoformat(timespec="seconds"), "stats": stats, "por_fonte": contagem,
            "erros": erros, "para_triar": para_triar, "para_notion": notion_itens}


def resumo_md(rd):
    L = [f"# Rodada {rd['gerado_em']}", "", f"Coletadas {rd['stats']['coletadas']} · "
         + " · ".join(f"{k} {v}" for k, v in rd["stats"].items() if k != "coletadas"), ""]
    if rd["erros"]:
        L += ["## Erros por fonte", *[f"- {e}" for e in rd["erros"]], ""]
    L += [f"## Para triagem ({len(rd['para_triar'])})"]
    L += [f"- **{i['empresa']}** — {i['titulo']} ({i['local']}) · score {i['score']} · {i['link']}" for i in rd["para_triar"]] or ["- nenhuma"]
    L += ["", f"## Para o Notion ({len(rd['para_notion'])})"]
    L += [f"- [{i['prioridade']}] {i['empresa']} — {i['titulo']} ({i['local']}) score {i['score']}"
          + (f" ⚠️ {i['armadilha']}" if i["armadilha"] else "") + (f" · {i['funil']}" if i["funil"] else "")
          for i in rd["para_notion"]]
    return "\n".join(L) + "\n"


def explicar(c, wl, trecho, so=None):
    vagas, erros, _ = coletar(wl, so)
    t = norm(trecho)
    achou = [v for v in vagas if t in norm(v.link) or t in norm(v.titulo) or t in norm(v.empresa) or t == norm(v.id_fonte)]
    for e in erros:
        print("aviso:", e, file=sys.stderr)
    if not achou:
        print(f"Nada na coleta atual casa com {trecho!r} ({len(vagas)} vagas coletadas).")
        return 1
    for v in achou[:10]:
        r = avaliar(c, v)
        print(f"\n{v.empresa} — {v.titulo} [{v.local}]\n  {v.link}")
        print(f"  => {r.prioridade}  score {r.score}  trilha {r.trilha or '-'}  geografia {r.geografia or '-'}")
        if r.motivo:
            print(f"  motivo: {r.motivo}")
        for p, why in r.pontos:
            print(f"    {p:+d}  {why}")
        if r.prioridade != "IGNORAR":
            print("  eliminatórios (o que dispararia se estivesse ligado):")
            for reg in c["eliminatorios"]:
                tr = casa_regra(reg, v, r.trilha)
                if tr is not None:
                    print(f"    ✗ {reg['id']}: “{tr}”")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--validar", action="store_true")
    ap.add_argument("--sem-estado", action="store_true")
    ap.add_argument("--explicar")
    ap.add_argument("--fonte")
    a = ap.parse_args(argv)
    try:
        c, wl = CR.carregar(), CR.carregar_watchlist()
    except CR.CriteriosInvalidos as e:
        print(f"CRITÉRIOS INVÁLIDOS: {e}", file=sys.stderr)
        return 2
    if a.validar:
        print(f"ok: {len(c['eliminatorios'])} eliminatórios, {sum(len(t['titulos']) for t in c['trilhas'].values())} títulos, "
              f"{len(wl.get('empresas', []))} empresas no watchlist")
        return 0
    if a.explicar:
        return explicar(c, wl, a.explicar, a.fonte)
    with open(os.path.join(RAIZ, "funil.yaml"), encoding="utf-8") as f:
        funil = yaml.safe_load(f) or {}
    estado = ES.carregar()
    rd = rodada(c, wl, funil, estado, a.fonte)
    os.makedirs(SAIDA, exist_ok=True)
    with open(os.path.join(SAIDA, "rodada.json"), "w", encoding="utf-8") as f:
        json.dump(rd, f, ensure_ascii=False, indent=1)
    with open(os.path.join(SAIDA, "resumo.md"), "w", encoding="utf-8") as f:
        f.write(resumo_md(rd))
    if not a.sem_estado:
        ES.salvar(estado)
    print(resumo_md(rd))
    return 0


if __name__ == "__main__":
    sys.exit(main())
