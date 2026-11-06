---
description: "Runs checar_fatos.py over the whole search and summarizes where known errors are still alive."
argument-hint: "[YYYY-MM-DD for recent only]"
---

Run from this folder:

```bash
python3 sistema/checar_fatos.py ../Applications ../_Sistema ../Archive "../Gemini Spark" --relatorio sistema/relatorios/varredura_$(date +%F).md $( [ -n "$ARGUMENTS" ] && echo --desde $ARGUMENTS )
```

Summarize for the human: blocks per rule (how many files), which `Applications/` folders were touched in the last 7 days and have a block, and the report path. Do not edit any material: material already sent is not corrected, only known.
