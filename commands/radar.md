---
description: "Consome o Radar de Vagas (inbox) do Notion: tria cada vaga nova e promove só o que passar."
argument-hint: "[--tudo reavalia as já triadas | --auto inclui as MEDIA do radar da nuvem]"
---

Banco: data source `<RADAR_INBOX_DATA_SOURCE_ID>` ("Radar de Vagas (inbox)"). Ele captura pelo celular; aqui é onde a coisa é avaliada.

1. **Leia as linhas com `Status = Novo`** (com `--tudo`, leia todas). Se não houver nenhuma, diga isso e pare.
   - **Como ler:** o plano do Notion não tem consulta SQL. Use `notion-search` com `data_source_url = collection://<RADAR_INBOX_DATA_SOURCE_ID>` (query curta, ex. "vaga", e também o nome de empresas, se precisar), depois `notion-fetch` em cada página para ver `Status`, `Link`, `Nota` e `Fonte`.
   - **Por padrão, só as capturadas por ele** (`Fonte` diferente de `Radar automatico`). As do radar da nuvem já chegam triadas quando são ALTA; as MEDIA ficam `Novo` e só entram com `--auto`.
2. **Para cada uma**, rode o `triador` (que já roda `checar_vaga.py` e avisa de armadilha para IA) (subagente) com o link e a `Nota` dele. Em paralelo, no máximo 3 por vez, para não estourar o navegador.
3. **Mostre uma tabela** ordenada por prioridade: empresa, cargo, local, veredito, o eliminatório encontrado (se houver) e o prazo. Uma linha de motivo por vaga, não mais.
4. **Atualize o banco:**
   - veredito NÃO APLICAR → `Status = Descartado`, e o motivo vai na `Nota`, depois do que ele escreveu (para não reavaliar a mesma vaga daqui a duas semanas);
   - veredito APLICAR ou TRIAGEM BARATA → `Status = Triado`.
5. **Pare e pergunte** quais ele quer levar adiante. A decisão de aplicar é dele.
6. **Para as escolhidas**, crie a linha no Applications Tracker (`<TRACKER_DATA_SOURCE_ID>`) com `Status = To apply` e o link, e diga que o próximo passo é `/construir`.

Não crie pasta em `Applications/` nesta etapa: pasta só nasce quando ele decide aplicar.
