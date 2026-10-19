---
description: "Fluxo completo para uma vaga — triador e canal-humano em paralelo, depois PARA para a decisão dele."
argument-hint: "<URL ou texto da vaga>"
---

Vaga: $ARGUMENTS

1. Descubra empresa e cargo (leia a página se for URL). Crie `Applications_teste/<Empresa> - <Cargo>/` (ou use `../Applications/` se ele disser que é produção).
2. **Em paralelo, na mesma mensagem**, lance os subagentes `triador` (com a URL/texto e o caminho da pasta) e `canal-humano` (com empresa, cargo e caminho da pasta).
3. Quando os dois voltarem, mostre a ele, curto:
   - o VEREDITO e o motivo em uma linha
   - eliminatórios, se houver
   - o melhor canal humano (ou FRIA) e eventual conflito
   - as "Perguntas para ele" do triador
   - se o triador mapeou o formulário (`Formulario.md` criado), avise em uma linha e destaque campo obrigatório fora do óbvio (GitHub, portfólio, teste técnico)
4. **PARE.** Pergunte com `AskUserQuestion`: aplicar / triagem barata / não aplicar. Esse portão é dele. Não chame o construtor antes da resposta.
5. Registre a decisão dele no fim de `Triagem.md` (`Decisão dele (<data>): ...`). Se for aplicar, diga que o próximo passo é `/construir <pasta>`, que **começa perguntando quais arquivos criar** (idioma, carta, ATS, respostas de formulário, mensagem).
