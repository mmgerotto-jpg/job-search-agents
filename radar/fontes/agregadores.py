"""Himalayas, Working Nomads, We Work Remotely. Descrição vem no próprio feed."""
import xml.etree.ElementTree as ET
from datetime import datetime
from ..modelo import Vaga
from . import json_de, pegar


def himalayas(paginas=5):
    cursor = None
    for _ in range(paginas):
        url = "https://himalayas.app/jobs/api?limit=20" + (f"&cursor={cursor}" if cursor else "")
        d = json_de(url)
        cursor = d.get("nextCursor")
        for j in d.get("jobs", []):
            restr = j.get("locationRestrictions") or []
            local = "Remote (" + ", ".join(restr) + ")" if restr else "Remote worldwide"
            lo, hi, cur = j.get("minSalary"), j.get("maxSalary"), j.get("currency", "USD")
            pub = j.get("pubDate")
            yield Vaga(fonte="himalayas", id_fonte=str(j.get("guid") or j.get("applicationLink")), empresa=j.get("companyName", ""),
                       titulo=j.get("title", ""), local=local, link=j.get("applicationLink") or j.get("guid", ""),
                       descricao_html=j.get("description", ""), tipo=j.get("employmentType") or "",
                       publicada=datetime.fromtimestamp(pub).strftime("%Y-%m-%d") if pub else "",
                       salario=f"{cur} {lo:,.0f}-{hi:,.0f}" if lo and hi else "")
        if not cursor or not d.get("jobs"):
            break


def working_nomads():
    for j in json_de("https://www.workingnomads.com/api/exposed_jobs/"):
        yield Vaga(fonte="workingnomads", id_fonte=j.get("url", ""), empresa=j.get("company_name", ""),
                   titulo=j.get("title", ""), local="Remote (" + (j.get("location") or "Global") + ")",
                   link=j.get("url", ""), descricao_html=j.get("description", ""),
                   publicada=(j.get("pub_date") or "")[:10])


def wwr():
    for feed in ("remote-management-and-finance-jobs", "remote-customer-support-jobs"):
        raiz = ET.fromstring(pegar(f"https://weworkremotely.com/categories/{feed}.rss"))
        for it in raiz.iter("item"):
            t = it.findtext("title", "")
            emp, _, tit = t.partition(":") if ":" in t else ("", "", t)
            # o rótulo de região do WWR é fraco; a restrição real costuma estar no corpo
            reg = it.findtext("region", "") or "Remote"
            yield Vaga(fonte="wwr", id_fonte=it.findtext("guid", "") or it.findtext("link", ""), empresa=emp.strip(),
                       titulo=tit.strip(), local="Remote (" + reg + ")", link=it.findtext("link", ""),
                       descricao_html=it.findtext("description", ""))


ADAPTADORES = {"himalayas": himalayas, "working_nomads": working_nomads, "wwr": wwr}
