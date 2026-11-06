# job-search-agents

A small system that treats a job search like a deployment problem: code does the cheap filtering, an LLM judges only what code cannot, and a human makes the two decisions that matter (whether to apply, and when to send).

Built with Claude Code. Overengineered on purpose, as a way to learn.

## What is here

| Folder | What it does |
|---|---|
| `radar/` | Daily scan of company career pages (Greenhouse, Ashby, Lever), remote boards and Gupy. Scores each role against criteria kept in a YAML file and sends only the best few to triage. Zero LLM tokens in the funnel. |
| `checks/checar_vaga.py` | Prompt-injection detector for job posts: hidden text, HTML comments, zero-width characters, phrases aimed at AI ("if you are an AI, include the word...") |
| `agents/` | Claude Code agents: `triador` (is the role worth the time), `canal-humano` (who can introduce me), `construtor` (builds CV and cover letter from a facts file), `auditor`, `preenchedor` (fills forms in the browser, never submits), `registrador` (logs to a tracker) |
| `commands/` | Slash commands that chain the agents |
| `antigravity/` | The same agent flow ported as Antigravity skills (`.agents/skills`), to test how the tools talk to each other |
| `gemini-spark/PROMPT_scanner.md` | The prompt for a daily scanner running on Gemini, written from a markdown spec Claude Code produced. Runs in parallel with the Claude Code radar |
| `sistema/` | The facts layer: `fatos.yaml` (single source of facts: identity, jobs and dates, deliverables per company, work anecdotes, client facts, banned strings), `fatos.py` (loader that fails loudly), `render_fatos.py` (human-readable `FATOS.md`), `auditar.py` (the mechanical gate before sending) and `geradores/` (docx builders for resume and ATS plain). Ships with a fictional `fatos.example.yaml` |
| `applications/` | One folder per role: `_modelo/` (templates for `Triagem.md`, `Entregaveis.md`, `Notas.md`) and a fictional worked example |
| `docs/tracker.md` | How applications are tracked: the folder per role, the Notion or `Tracker.md` tracker, and the silence rule |
| `tests/` | Golden-set regression tests on the scoring rules (synthetic cases) |
| `criterios.example.yaml`, `watchlist.example.yaml` | Examples. The criteria reflect one person's search (geography, languages, knockouts); copy to `criterios.yaml` and `watchlist.yaml` and replace with yours |

## Use only one piece

You do not need the whole flow. Each piece works on its own, with a few adjustments:

**The radar (`radar/`)** runs standalone.
- Needs: `pip install -r requirements.txt`, then your own `criterios.yaml` and `watchlist.yaml` (copy the `.example` files).
- Run: `python -m radar.varrer`. It needs no agent, no facts file and no Notion; results land in `saida/`.
- Optional: the daily routine in `routines/` and the Notion writes are a layer on top, not a requirement.

**The triager (`agents/triador.md`)** works as a single Claude Code agent.
- Copy it to `.claude/agents/`.
- It points to files this repo does not ship: `CLAUDE.md` (start from `CLAUDE.example.md`), `contexto/` (your own history, search criteria and notes) and `sistema/FATOS.md` (generated from your facts file). Create short versions of those, or edit the "Read before evaluating" list in the prompt to match what you have.
- It also calls `sistema/checar_vaga.py`; the same script is in `checks/`.

**The builder (`agents/construtor.md`) and the gate** need the facts layer.
- Copy `sistema/` and replace `fatos.example.yaml` with your own `fatos.yaml`.
- The builder writes a `build_<company>.py` that imports `fatos.py`; see `applications/Acme - Senior Operations Manager/` for a working example.
- `sistema/auditar.py` needs LibreOffice and poppler to count PDF pages.
- The builder also cites `contexto/` notes (narrative rules, ATS notes); drop those references or write your own.

**The tracker** is independent: see `docs/tracker.md`.

## Principles

1. **No agent types a fact.** Facts come from one source file and are imported, never retyped. A missing fact is listed as a question for the human.
2. **A mechanical gate before sending.** Checks do not depend on anyone remembering.
3. **Two human gates never go away:** the decision to apply, and the final send.
4. **Text inside a job post is data, never an instruction.**
5. **Every new rule gets a test case.**

## Run

```
pip install -r requirements.txt
python -m radar.varrer --validar        # check criteria and watchlist
python -m radar.varrer --sem-estado     # dry run
python -m unittest discover -s tests    # golden tests
```

The facts layer and the gate (needs LibreOffice and poppler for PDF page counts):

```
cp sistema/fatos.example.yaml sistema/fatos.yaml   # then replace with your own facts
python sistema/fatos.py                            # loads and checks the yaml
python sistema/render_fatos.py                     # writes FATOS.md
cd "applications/Acme - Senior Operations Manager"
JOBSEARCH_OUT="$PWD" python _partes/build_acme.py  # builds the example resume from the facts
python ../../sistema/auditar.py . --gravar         # PASS or BLOCKED
```

## What is not here

The author's own facts file, history and narrative notes, tracker state and real applications. Everything under `sistema/fatos.example.yaml` and `applications/` is fictional. This repository holds the method, not the personal data. The agent prompts were scrubbed of personal details; read them before reusing. Folder and file names keep their original Portuguese (`triador` = triager, `construtor` = builder, `registrador` = logger, `preenchedor` = form filler, `canal-humano` = human channel, `Entregaveis.md` = deliverables, `Triagem.md` = triage, `Notas.md` = notes, `Auditoria.md` = audit); everything inside them is in English. Internal codes in the radar keep their original names: priorities `ALTA`/`MEDIA`/`BAIXA` = HIGH/MEDIUM/LOW, `DESCARTAR`/`IGNORAR` = discard/ignore. A few detection patterns (`checar_vaga.py`) deliberately cover Portuguese phrases as well as English.

Tool names in the agent files (`mcp__gmail__*`, `mcp__notion__*`, `mcp__claude-in-chrome__*`) are generic: rename them to match the connectors in your own setup.

## License

MIT.
