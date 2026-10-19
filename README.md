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
| `tests/` | Golden-set regression tests on the scoring rules (synthetic cases) |
| `criterios.example.yaml`, `watchlist.example.yaml` | Examples. Copy to `criterios.yaml` and `watchlist.yaml` and adapt |

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

## What is not here

The candidate facts file, the history and narrative notes, the tracker state and the applications folder. This repository holds the method, not the personal data. The agent prompts are written in Portuguese and were scrubbed of personal details; read them before reusing.

## License

MIT.
