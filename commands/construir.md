---
description: "Asks which files to create, then builder + auditor in a loop until PASS (max. 3 rounds). Stops before sending."
argument-hint: "<role folder>"
---

Folder: $ARGUMENTS

1. Confirm that `Triagem.md` has `Decision: apply` (or cheap triage). Without it, stop.
2. **Ask for the deliverables BEFORE starting any work.** If the folder already has `Entregaveis.md`, show what it says and ask only whether anything changed. Otherwise, use `AskUserQuestion` with these four questions at once (the first option of each is the suggestion for this role, marked "(Recommended)"):
   - **Resume language:** EN · PT-BR · Both.
   - **Documents besides the resume** (multiple): Letter · Plain-text ATS version · Single PDF (resume + letter) · No extras.
   - **Supporting texts** (multiple): Form answers · Message to the human channel · Introduction email · None.
   - **Content adjustments:** No adjustments · Omit a line (language, citizenship…) · Emphasize a specific point.
   **How to suggest:** LinkedIn Easy Apply → resume only, no letter. Form with a letter field (Greenhouse, Ashby, hiBob) → separate letter. A single upload field → single PDF. Workday, Gupy, iCIMS → ATS version. Open questions on the form → form answers (100 to 300 words, counted). Role only in the home country → no second citizenship. Referral or human channel → message.
3. Write the answer to `<folder>/Entregaveis.md`, in this format, and only then proceed:
   ```
   # Deliverables — <Company - Role>
   *<date>. Defined by the human before building.*
   - Resume: EN | PT_BR | both
   - Letter: yes | no
   - ATS: yes | no
   - Single PDF: yes | no
   - Form answers: yes | no
   - Message to the human channel: yes | no
   - Introduction email: yes | no
   - Adjustments: <what to omit or emphasize, or "none">
   ```
4. Launch the `construtor` subagent with the folder. It builds **only what is in `Entregaveis.md`**.
5. Launch the `auditor` subagent with the folder.
6. BLOCKED → return the literal "Failed" list to the `construtor` and repeat. At most 3 rounds; if it still blocks, stop and show the human what is left.
7. PASS → show the human: files generated, which file goes in which field, remaining warnings, and missing facts from `Notas.md`.
8. **STOP.** Sending is the human's: password, terms, captcha and submit. After they confirm, the next step is `/registrar <folder>`.
