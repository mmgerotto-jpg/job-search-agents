---
description: "Pergunta quais arquivos criar, depois construtor + auditor em loop até PASSA (máx. 3 voltas). Para antes do envio."
argument-hint: "<pasta da vaga>"
---

Pasta: $ARGUMENTS

1. Confirme que `Triagem.md` tem `Decisão dele: aplicar` (ou triagem barata). Sem isso, pare.
2. **Pergunte os entregáveis ANTES de começar qualquer trabalho.** Se a pasta já tem `Entregaveis.md`, mostre o que ele diz e pergunte só se mudou algo. Senão, use `AskUserQuestion` com estas quatro perguntas de uma vez (a primeira opção de cada uma é a sugestão para esta vaga, marcada "(Recomendado)"):
   - **Idioma do currículo:** EN · PT-BR · Os dois.
   - **Documentos além do currículo** (múltipla): Carta · Versão ATS em texto plano · PDF único (currículo + carta) · Nenhum extra.
   - **Textos de apoio** (múltipla): Respostas de formulário · Mensagem ao canal humano · E-mail de apresentação · Nenhum.
   - **Ajustes de conteúdo:** Sem ajustes · Omitir uma linha (idioma, cidadania…) · Enfatizar um ponto específico.
   **Como sugerir:** LinkedIn Easy Apply → só currículo, sem carta. Formulário com campo de carta (Greenhouse, Ashby, hiBob) → carta separada. Um único campo de upload → PDF único. Workday, Gupy, iCIMS → versão ATS. Perguntas abertas no formulário → respostas de formulário (100 a 300 palavras, contando). Vaga só no Brasil → sem cidadania italiana. Indicação ou canal humano → mensagem.
3. Grave a resposta em `<pasta>/Entregaveis.md`, neste formato, e só então siga:
   ```
   # Entregáveis — <Empresa - Cargo>
   *<data>. Definidos por ele antes de construir.*
   - Currículo: EN | PT_BR | os dois
   - Carta: sim | não
   - ATS: sim | não
   - PDF único: sim | não
   - Respostas de formulário: sim | não
   - Mensagem ao canal humano: sim | não
   - E-mail de apresentação: sim | não
   - Ajustes: <o que omitir ou enfatizar, ou "nenhum">
   ```
4. Lance o subagente `construtor` com a pasta. Ele constrói **só o que está no `Entregaveis.md`**.
5. Lance o subagente `auditor` com a pasta.
6. BLOQUEIA → devolva ao `construtor` a lista "Reprovou" literal e repita. No máximo 3 voltas; se ainda bloquear, pare e mostre a ele o que sobrou.
7. PASSA → mostre a ele: arquivos gerados, qual arquivo vai em qual campo, alertas restantes, e fatos faltando do `Notas.md`.
8. **PARE.** O envio é dele: senha, termos, captcha e submit. Depois que ele confirmar, o próximo passo é `/registrar <pasta>`.
