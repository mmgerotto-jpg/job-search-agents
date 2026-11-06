---
description: "Full flow for a role — triager and human channel in parallel, then STOP for the human's decision."
argument-hint: "<role URL or text>"
---

Role: $ARGUMENTS

1. Find the company and role (read the page if it is a URL). Create `Applications_teste/<Company> - <Role>/` (or use `../Applications/` if the human says it is production).
2. **In parallel, in the same message**, launch the `triador` subagents (with the URL/text and the folder path) and `canal-humano` (with company, role and folder path).
3. When both return, show the human, briefly:
   - the VERDICT and the reason in one line
   - knockouts, if any
   - the best human channel (or COLD) and any conflict
   - the triager's "Questions for the human"
   - if the triager mapped the form (`Formulario.md` created), say so in one line and highlight any required field outside the obvious (GitHub, portfolio, technical test)
4. **STOP.** Ask with `AskUserQuestion`: apply / cheap triage / do not apply. This gate is the human's. Do not call the builder before the answer.
5. Record the human's decision at the end of `Triagem.md` (`Decision (<date>): ...`). If applying, say the next step is `/construir <folder>`, which **starts by asking which files to create** (language, letter, ATS, form answers, message).
