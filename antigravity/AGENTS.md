# Fluxo de candidatura — the candidate (Antigravity)

Cinco skills (`.agents/skills/`) para o fluxo de candidatura. Adaptado do projeto Claude Code em `../`.

## Duas ideias que valem acima de tudo

1. **Nenhum agente digita um fato.** Fato vem de `../sistema/fatos.yaml`, por import (`../sistema/fatos.py`). Precisa de um fato que não está lá? **Pare e liste como "fato faltando" para ele.** Não invente, não copie de material antigo.
2. **Existe um portão mecânico antes do envio:** `../sistema/auditar.py`. Não depende de alguém lembrar.

## Dois portões humanos. Não saem.

- **A decisão de aplicar** (depois do triador + canal-humano).
- **O envio.** Sempre ele. Senha, criação de conta, aceite de termos/GDPR, captcha e submit final são dele, mesmo se ele pedir.

## Caminhos

| O quê | Onde (a partir desta pasta) |
|---|---|
| Fonte única de fatos | `../sistema/fatos.yaml` (o `FATOS.md` ao lado é GERADO) |
| Loader para geradores | `../sistema/fatos.py` |
| Portão | `python3 ../sistema/auditar.py "<pasta da vaga>" --gravar` |
| Varredura de pasta inteira | `python3 ../sistema/checar_fatos.py <pasta> [--desde AAAA-MM-DD]` |
| Auditor de texto | `../sistema/checar_texto.py` |
| Geradores (já migrados para `fatos.py`) | `../sistema/geradores/` |
| Como contar (PPF, linguagem a cortar) | `../contexto/NARRATIVA.md` |
| Formulário (remuneração, visto, gap) | `../contexto/RESPOSTAS.md` |
| Padrão do funil, erros, Staff vs gestão | `../contexto/HISTORICO.md` |
| Critérios de busca e eliminatórios | `../contexto/CRITERIOS_DE_BUSCA.md` |
| ATS por plataforma | `../contexto/03-ats.md` |
| Pasta das candidaturas | **`../Applications_teste/`** (padrão seguro). Para produção: `../../Applications/` |

`../contexto/` são **cópias congeladas de 21/09/2026**; `FATOS.md`/`NARRATIVA.md` etc. vivos estão em `../../_Sistema/`. Ao ativar de verdade, aponte para lá.

Pasta de cada vaga: `<APPS>/<Empresa> - <Cargo>/`. Arquivos: `Triagem.md`, `Canal_Humano.md`, `Candidate_Resume.{docx,pdf}`, `..._ATS.docx`, `..._Cover_Letter.{docx,pdf}`, `Email.md`, `Notas.md`, `Auditoria.md`, `_partes/build_<empresa>.py`.

## Ler fato

```bash
python3 ../sistema/fatos.py arvo.agentes           # um valor
python3 ../sistema/fatos.py                         # confere as contas e lista pendências
```

## O que NÃO vira agente

O julgamento de enquadramento (o que sobe, o que desce no currículo), a conversa (entrevista, negociação), e a nota de conexão de 300 caracteres. É leitura de contexto e artesanato.

## O fluxo

```
vaga
 ├─► triador ──────────┐
 └─► canal-humano ─────┤   (em paralelo)
                       ▼
              [ELE decide: aplicar ou não]
                       ▼
                   construtor
                       ▼
                    auditor ──❌──► volta ao construtor
                       │✅
                       ▼
              [ELE envia. Sempre ele]
                       ▼
                  registrador
```
