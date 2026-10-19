"""Páginas de carreira via API pública do ATS (Greenhouse, Ashby, Lever). A descrição vem completa em JSON."""
import html as _html
from datetime import datetime
from ..modelo import Vaga
from . import json_de


def _dia(s):
    return (s or "")[:10]


def greenhouse(e):
    d = json_de(f"https://boards-api.greenhouse.io/v1/boards/{e['slug']}/jobs?content=true")
    for j in d.get("jobs", []):
        yield Vaga(fonte=f"greenhouse:{e['slug']}", id_fonte=str(j["id"]), empresa=e.get("nome") or j.get("company_name", ""),
                   titulo=j.get("title", ""), local=(j.get("location") or {}).get("name", ""),
                   link=j.get("absolute_url", ""), descricao_html=_html.unescape(j.get("content", "")),
                   publicada=_dia(j.get("first_published") or j.get("updated_at")),
                   prazo=_dia(j.get("application_deadline")), fundo=e.get("fundo", ""))


def ashby(e):
    d = json_de(f"https://api.ashbyhq.com/posting-api/job-board/{e['slug']}?includeCompensation=true")
    for j in d.get("jobs", []):
        if j.get("isListed") is False:
            continue
        loc = j.get("location") or ""
        for s in j.get("secondaryLocations") or []:
            loc += " / " + (s.get("location") if isinstance(s, dict) else str(s))
        if j.get("isRemote") and "remote" not in loc.lower():
            loc = (loc + " (remote)").strip()
        comp = (j.get("compensation") or {}).get("compensationTierSummary", "")
        yield Vaga(fonte=f"ashby:{e['slug']}", id_fonte=j["id"], empresa=e.get("nome", e["slug"]),
                   titulo=j.get("title", ""), local=loc, link=j.get("jobUrl", ""),
                   descricao_html=j.get("descriptionHtml") or j.get("descriptionPlain", ""),
                   tipo=j.get("employmentType", ""), publicada=_dia(j.get("publishedAt")),
                   salario=comp, fundo=e.get("fundo", ""))


def lever(e):
    d = json_de(f"https://api.lever.co/v0/postings/{e['slug']}?mode=json")
    for j in d if isinstance(d, list) else []:
        cat = j.get("categories") or {}
        ts = j.get("createdAt")
        yield Vaga(fonte=f"lever:{e['slug']}", id_fonte=j["id"], empresa=e.get("nome", e["slug"]),
                   titulo=j.get("text", ""), local=cat.get("location", "") or j.get("workplaceType", ""),
                   link=j.get("hostedUrl", ""),
                   descricao_html=j.get("description", "") + "".join(
                       f"<h3>{l.get('text','')}</h3>{l.get('content','')}" for l in (j.get("lists") or [])) + (j.get("additional") or ""),
                   tipo=cat.get("commitment", ""),
                   publicada=datetime.fromtimestamp(ts / 1000).strftime("%Y-%m-%d") if ts else "",
                   fundo=e.get("fundo", ""))


ADAPTADORES = {"greenhouse": greenhouse, "ashby": ashby, "lever": lever}
