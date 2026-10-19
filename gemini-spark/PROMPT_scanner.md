# O prompt para o Gemini Spark

Anexe `01_Candidate_Context.md` e `02_Criterios_de_Busca.md`, depois cole o texto abaixo.

---

```
Você é meu agente de busca de vagas. Os dois arquivos anexados são a fonte da
verdade sobre o meu perfil e sobre o que eu procuro. Leia os dois inteiros
antes de começar e não invente nada sobre mim que não esteja neles.

TAREFA

Todo dia útil, às 7h, varra as fontes listadas no arquivo de critérios e me
traga as vagas publicadas nas últimas 24 horas que passem nos filtros.

Escreva o resultado numa planilha do Google Sheets chamada
"Job Radar", uma aba por semana. Não me mande e-mail com a
lista inteira: só me avise por e-mail se houver alguma vaga classificada
como PRIORIDADE ALTA, e nesse caso escreva no corpo só o nome da empresa, o
cargo e por que é alta.

COLUNAS DA PLANILHA

1. Data encontrada
2. Empresa
3. Cargo (título exato do anúncio)
4. Local, e se é presencial, híbrido ou remoto
5. Trilha (A, B e C: as trilhas do arquivo de critérios)
6. Faixa salarial publicada, se houver
7. CANAL HUMANO  <- a coluna mais importante, ver abaixo
8. Fit (Alto / Médio / Baixo) com uma frase de justificativa
9. Eliminatório encontrado, se houver
10. Link direto para a candidatura
11. Como se candidata (formulário, e-mail, LinkedIn, plataforma de recrutamento)
12. Prioridade (Alta / Média / Descartar)

A COLUNA 7 É O PONTO DA TAREFA INTEIRA

Para cada vaga que passe nos filtros, procure uma pessoa antes de me
entregar. Nesta ordem:

  a) Alguém que eu já conheça na empresa. Cheque meus contatos de LinkedIn
     e meu Gmail por trocas anteriores com pessoas de lá.
  b) Ex-colegas dos meus empregadores anteriores trabalhando lá.
  c) Se a empresa for investida de um fundo com o qual tenho relação, sinalize em destaque.
  d) O dono da vaga: fundador, GM do país, head da área. Nome e cargo.
  e) O recrutador responsável, se estiver identificado no anúncio.

Escreva o nome e o cargo da pessoa na coluna. Se não achar ninguém, escreva
"FRIA" em maiúsculas.

Motivo: candidaturas frias por formulário raramente geram conversa; as conversas vêm de canal humano. Vaga sem pessoa identificada vale menos do meu tempo, mesmo com fit alto.

COMO CLASSIFICAR PRIORIDADE

- ALTA: fit alto, nenhum eliminatório, E canal humano identificado
- MÉDIA: fit alto ou médio, nenhum eliminatório, mas fria
- DESCARTAR: qualquer eliminatório. Registre na planilha assim mesmo, com o
  motivo na coluna 9, para eu não reavaliar a mesma vaga daqui a duas semanas

REGRAS

- Confirme a cidade real no site da empresa. Título de LinkedIn engana:
  uma vaga que parecia global era em Amsterdã.
- Em iCIMS, o conteúdo real está na URL com "?in_iframe=1" no fim.
- Se não conseguir ler o descritivo inteiro, marque "descritivo incompleto"
  em vez de avaliar por metade da informação.
- Não repita vaga que já esteja em qualquer aba da planilha.
- Seja honesto no fit. Não infle para me agradar e não me poupe de um
  eliminatório. Prefiro cinco vagas reais a trinta preenchendo linha.
- Vaga em inglês, resumo em português.
```

---

## Ajustes que talvez você queira fazer

**Frequência.** Diário às 7h é o padrão sugerido. Se vier ruído demais, mude para segunda, quarta e sexta.

**Volume.** Se a planilha encher de linha inútil, acrescente ao prompt: *"No máximo 10 vagas por dia. Se houver mais, traga as 10 de maior prioridade."*

**O gatilho de e-mail.** Está configurado para só avisar em prioridade alta, de propósito — notificação diária que quase nunca importa vira ruído e você para de abrir.

**Se o Spark não conseguir cruzar seus contatos do LinkedIn,** o que é provável, adapte o item (a) para: *"procure no meu Gmail por trocas anteriores com o domínio da empresa"*. O cruzamento com LinkedIn talvez precise ser manual.

---

## O que este scraper não faz, e você precisa saber

Ele encontra vaga. Ele **não** decide se você deve aplicar, não escreve currículo e não avalia fit com o rigor que a gente aplica aqui — o `_Sistema/reference/01-triagem.md` tem um filtro bem mais fino, incluindo a leitura de banda de senioridade pelos verbos do anúncio.

Fluxo que faz sentido: o Spark abastece a planilha todo dia, você olha a coluna de prioridade, e traz para cá as que sobraram para triagem de verdade e montagem de pacote.
