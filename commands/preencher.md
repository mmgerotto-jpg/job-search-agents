---
description: "Preenche o formulário de candidatura aberto no Chrome, a partir da pasta da vaga já construída. Não envia nada."
argument-hint: "<pasta da vaga>"
---

Pasta: $ARGUMENTS

1. Confirme que a pasta tem `Triagem.md` com `Decisão dele: aplicar` (ou triagem barata) e `Entregaveis.md`. Sem isso, pare.
2. Confirme que há uma aba do Chrome (extensão Claude, não o browser isolado) com o formulário da vaga aberto. Se não houver, peça a ele para abrir a página e me avisar.
3. **Pergunte antes de digitar qualquer dado pessoal na página**, com `AskUserQuestion` ou em texto simples: "Posso ler os campos deste formulário e preencher com os dados prontos da pasta?" Sem essa confirmação, não avance para o passo 4.
4. Lance o subagente `preenchedor` com a pasta.
5. Mostre a ele: quantos campos preenchidos, quais ficaram `PERGUNTAR` e o que fazer com cada um, e alertas (armadilha para IA, campo sem fonte).
6. **PARE.** Revisão, senha, criação de conta, termos, captcha e o clique final de envio são sempre dele. Depois que ele confirmar o envio, o próximo passo é `/registrar <pasta>`.
