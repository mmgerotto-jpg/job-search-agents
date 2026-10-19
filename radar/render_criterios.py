#!/usr/bin/env python3
"""Gera CRITERIOS_DE_BUSCA.md (legível, para o triador e para o espelho no Notion) a partir do criterios.yaml."""
import os
import sys
from . import criterios as CR


def render(c):
    L = ["# Critérios de busca (gerado de criterios.yaml; não edite aqui)", ""]
    l = c["limiares"]
    L += [f"ALTA: score ≥ {l['alta']} com geografia forte · MÉDIA: ≥ {l['media']} · triagem automática: até {l['max_triagens_por_rodada']} por rodada", "", "## Trilhas"]
    for k, t in c["trilhas"].items():
        L += [f"**{k} — {t['nome']}** (+{t['pontos']}): " + " · ".join(t["titulos"]), ""]
    L += ["## Eliminatórios (descarte automático)", ""]
    L += [f"- **{r['id']}** [{r['escopo']}]: {r['motivo']}" for r in c["eliminatorios"]]
    L += ["", "## Penalidades", ""] + [f"- {r['pontos']:+d} **{r['id']}**: {r['motivo']}" for r in c["penalidades"]]
    g = c["geografia"]
    L += ["", "## Geografia", f"- forte: `{g['aceita_forte']['padrao']}`", f"- fraca (só MÉDIA): `{g['aceita_fraca']['padrao']}`",
          f"- EUA remoto (só MÉDIA, com aviso \"visto a checar depois\"): local nos EUA **e** remoto: `{g['eua_remoto']['eua']}`", f"- bloqueia (inclui EUA presencial): `{g['bloqueia']['padrao']}`", "", "## Bônus"]
    for k, b in c["bonus"].items():
        L.append(f"- {k} (+{b['pontos']}): " + ", ".join(b["empresas"]))
    return "\n".join(L) + "\n"


def main():
    txt = render(CR.carregar())
    destino = os.path.join(CR.RAIZ, "CRITERIOS_DE_BUSCA.md")
    if "--check" in sys.argv:
        return 0 if os.path.exists(destino) and open(destino, encoding="utf-8").read() == txt else 1
    open(destino, "w", encoding="utf-8").write(txt)
    print("ok:", destino)
    return 0


if __name__ == "__main__":
    sys.exit(main())
