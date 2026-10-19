#!/usr/bin/env python3
"""Confirma no estado.json o que a rotina fez: python -m radar.marcar <chave> notion_page=<id> veredito=APLICAR ..."""
import sys
from . import estado as ES

CAMPOS = {"notion_page", "veredito", "triada", "no_notion"}


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    e = ES.carregar()
    v = e["vagas"].get(argv[0])
    if not v:
        print(f"chave desconhecida: {argv[0]}")
        return 1
    for kv in argv[1:]:
        k, _, val = kv.partition("=")
        if k not in CAMPOS:
            print(f"campo inválido: {k} (use {sorted(CAMPOS)})")
            return 2
        v[k] = val.lower() == "true" if k in ("triada", "no_notion") else val
    if v.get("triada"):
        v["pendente_triagem"] = False
    ES.salvar(e)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
