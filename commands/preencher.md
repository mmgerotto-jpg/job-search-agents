---
description: "Fills in the application form open in Chrome, from the already-built role folder. Sends nothing."
argument-hint: "<role folder>"
---

Folder: $ARGUMENTS

1. Confirm that the folder has `Triagem.md` with `Decision: apply` (or cheap triage) and `Entregaveis.md`. Without them, stop.
2. Confirm there is a Chrome tab (Claude extension, not the isolated browser) with the role's form open. If not, ask the human to open the page and tell me.
3. **Ask before typing any personal data on the page**, with `AskUserQuestion` or in plain text: "May I read this form's fields and fill them with the ready data in the folder?" Without that confirmation, do not go to step 4.
4. Launch the `preenchedor` subagent with the folder.
5. Show the human: how many fields were filled, which stayed `ASK` and what to do about each, and warnings (trap for AI, field without a source).
6. **STOP.** Review, password, account creation, terms, captcha and the final send click always belong to the human. After they confirm sending, the next step is `/registrar <folder>`.
