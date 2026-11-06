# Application workflow — the candidate (Antigravity)

Five skills (`.agents/skills/`) for the application workflow. Adapted from the Claude Code project in `../`.

## Two ideas that matter above all

1. **No agent types a fact.** Facts come from `../sistema/fatos.yaml`, by import (`../sistema/fatos.py`). Need a fact that is not there? **Stop and list it as a "missing fact" for the human.** Do not invent it, do not copy it from old material.
2. **There is a mechanical gate before sending:** `../sistema/auditar.py`. It does not depend on anyone remembering.

## Two human gates. They never go away.

- **The decision to apply** (after the triager + human channel).
- **The send.** Always the human. Password, account creation, acceptance of terms/GDPR, captcha and the final submit are theirs, even if they ask you to.

## Paths

| What | Where (from this folder) |
|---|---|
| Single source of facts | `../sistema/fatos.yaml` (the `FATOS.md` next to it is GENERATED) |
| Loader for generators | `../sistema/fatos.py` |
| Gate | `python3 ../sistema/auditar.py "<role folder>" --gravar` |
| Whole-folder sweep | `python3 ../sistema/checar_fatos.py <folder> [--desde YYYY-MM-DD]` |
| Text auditor | `../sistema/checar_texto.py` |
| Generators (already migrated to `fatos.py`) | `../sistema/geradores/` |
| How to tell the story (PPF, language to cut) | `../contexto/NARRATIVA.md` |
| Form answers (compensation, visa, gap) | `../contexto/RESPOSTAS.md` |
| Funnel pattern, mistakes, Staff vs management | `../contexto/HISTORICO.md` |
| Search criteria and knockouts | `../contexto/CRITERIOS_DE_BUSCA.md` |
| ATS by platform | `../contexto/03-ats.md` |
| Applications folder | **`../Applications_teste/`** (safe default). For production: `../../Applications/` |

`../contexto/` holds **frozen copies**; the live `FATOS.md`/`NARRATIVA.md` etc. live in `../../_Sistema/`. When activating for real, point there.

Each role's folder: `<APPS>/<Company> - <Role>/`. Files: `Triagem.md`, `Canal_Humano.md`, `Candidate_Resume.{docx,pdf}`, `..._ATS.docx`, `..._Cover_Letter.{docx,pdf}`, `Email.md`, `Notas.md`, `Auditoria.md`, `_partes/build_<company>.py`.

## Reading a fact

```bash
python3 ../sistema/fatos.py northwind.agentes           # one value
python3 ../sistema/fatos.py                         # checks the sums and lists pending items
```

## What does NOT become an agent

Framing judgment (what rises and what falls in the resume), the conversation (interview, negotiation), and the 300-character connection note. That is context reading and craft.

## The flow

```
role
 ├─► triador ──────────┐
 └─► canal-humano ─────┤   (in parallel)
                       ▼
          [HUMAN decides: apply or not]
                       ▼
                   construtor
                       ▼
                    auditor ──❌──► back to the builder
                       │✅
                       ▼
          [HUMAN sends. Always the human]
                       ▼
                  registrador
```
