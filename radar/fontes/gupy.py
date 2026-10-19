"""Gupy: busca pública por termo (employability-portal.gupy.io). Uma busca por termo em criterios/fontes."""
import urllib.parse
from ..modelo import Vaga
from . import json_de

BASE = "https://employability-portal.gupy.io/api/v1/jobs"


def buscar(termos, limite=50, paginas=2):
    for termo in termos:
        for p in range(paginas):
            url = f"{BASE}?jobName={urllib.parse.quote(termo)}&limit={limite}&offset={p * limite}"
            d = json_de(url)
            dados = d.get("data", [])
            for j in dados:
                cidade = ", ".join(x for x in (j.get("city"), j.get("state"), j.get("country")) if x)
                remoto = j.get("workplaceType") == "remote" or str(j.get("isRemoteWork")).lower() == "true"
                yield Vaga(fonte="gupy", id_fonte=str(j["id"]), empresa=j.get("careerPageName", ""),
                           titulo=j.get("name", ""), local=("Remoto - " if remoto else "") + cidade,
                           link=j.get("jobUrl", ""), descricao_html=j.get("description", ""),
                           publicada=(j.get("publishedDate") or "")[:10], prazo=j.get("applicationDeadline") or "")
            if len(dados) < limite:
                break
