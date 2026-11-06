#!/usr/bin/env python3
"""Generates CRITERIOS_DE_BUSCA.md (readable, for the triager and for the Notion mirror) from criterios.yaml."""
import os
import sys
from . import criterios as CR


def render(c):
    L = ["# Search criteria (generated from criterios.yaml; do not edit here)", ""]
    l = c["limiares"]
    L += [f"HIGH: score ≥ {l['alta']} with strong geography · MEDIUM: ≥ {l['media']} · automatic triage: up to {l['max_triagens_por_rodada']} per round", "", "## Tracks"]
    for k, t in c["trilhas"].items():
        L += [f"**{k} — {t['nome']}** (+{t['pontos']}): " + " · ".join(t["titulos"]), ""]
    L += ["## Knockouts (automatic discard)", ""]
    L += [f"- **{r['id']}** [{r['escopo']}]: {r['motivo']}" for r in c["eliminatorios"]]
    L += ["", "## Penalties", ""] + [f"- {r['pontos']:+d} **{r['id']}**: {r['motivo']}" for r in c["penalidades"]]
    g = c["geografia"]
    L += ["", "## Geography", f"- strong: `{g['aceita_forte']['padrao']}`", f"- weak (MEDIUM only): `{g['aceita_fraca']['padrao']}`",
          f"- remote US (MEDIUM only, with a \"visa to check later\" warning): location in the US **and** remote: `{g['eua_remoto']['eua']}`", f"- blocks (includes on-site US): `{g['bloqueia']['padrao']}`", "", "## Bonuses"]
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
