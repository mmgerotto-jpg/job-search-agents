---
description: "Roda checar_fatos.py na busca inteira e resume onde os erros conhecidos ainda estão vivos."
argument-hint: "[AAAA-MM-DD para só o recente]"
---

Rode a partir desta pasta:

```bash
python3 sistema/checar_fatos.py ../Applications ../_Sistema ../Archive "../Gemini Spark" --relatorio sistema/relatorios/varredura_$(date +%F).md $( [ -n "$ARGUMENTS" ] && echo --desde $ARGUMENTS )
```

Resuma para ele: bloqueios por regra (quantos arquivos), quais pastas de `Applications/` foram tocadas nos últimos 7 dias e têm bloqueio, e o caminho do relatório. Não edite nenhum material: material enviado não se corrige, só se sabe.
