---
description: "Consumes the Notion Job Radar (inbox): triages each new role and promotes only what passes."
argument-hint: "[--tudo re-evaluates the already triaged | --auto includes the cloud radar's MEDIUM]"
---

Database: data source `<RADAR_INBOX_DATA_SOURCE_ID>` ("Job Radar (inbox)"). The human captures from the phone; this is where things are evaluated.

1. **Read the rows with `Status = New`** (with `--tudo`, read all). If there are none, say so and stop.
   - **How to read:** the Notion plan has no SQL query. Use `notion-search` with `data_source_url = collection://<RADAR_INBOX_DATA_SOURCE_ID>` (a short query, e.g. "role", and also company names if needed), then `notion-fetch` on each page to see `Status`, `Link`, `Note` and `Source`.
   - **By default, only the ones the human captured** (`Source` other than `Automatic radar`). The cloud radar's come already triaged when they are HIGH; the MEDIUM ones stay `New` and only come in with `--auto`.
2. **For each one**, run the `triador` (which already runs `checar_vaga.py` and warns of a trap for AI) (subagent) with the link and the human's `Note`. In parallel, at most 3 at a time, so the browser is not overwhelmed.
3. **Show a table** ordered by priority: company, role, location, verdict, the knockout found (if any) and the deadline. One line of reason per role, no more.
4. **Update the database:**
   - verdict DO NOT APPLY → `Status = Discarded`, and the reason goes in `Note`, after what the human wrote (so the same role is not re-evaluated two weeks later);
   - verdict APPLY or CHEAP TRIAGE → `Status = Triaged`.
5. **Stop and ask** which ones the human wants to take forward. The decision to apply is theirs.
6. **For the chosen ones**, create the row in the Applications Tracker (`<TRACKER_DATA_SOURCE_ID>`) with `Status = To apply` and the link, and say the next step is `/construir`.

Do not create a folder in `Applications/` at this stage: a folder is only born when the human decides to apply.
