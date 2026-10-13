# Estrutura dos Slides — DebtRadar (1ª etapa)

Doze slides para 10 minutos. Os slides sustentam a fala; não a
substituem. Tudo o que aparece aqui vem do programa e dos dados reais.

Este documento descreve o deck como ele está publicado em
https://claude.ai/artifact/W2tHprsQx3iEGwcJaSpZ8v (conferido em
13/10/2026). Luy apresenta os slides 1 a 6 e o 10; Luiz, os slides 7 a
9, o 11 e o 12.

## Regras de formato

- Pouco texto: no máximo quatro tópicos curtos por slide.
- Código em fonte grande, com poucas linhas, igual ao do arquivo.
- Números sempre com a unidade: "16 de 30 issues", não "53%" sozinho.
- A demonstração é ao vivo; o slide dela traz só os comandos.
- Exportar em PDF com o nome `etapa1-DebtRadar.pdf`.

## Slide 1 — DebtRadar

- **Conteúdo:** "DebtRadar — Analisador Multimodal de Dívida Técnica";
  "Dívida técnica em textos do GitHub, com Regex e spaCy"; disciplina e
  etapa; nomes dos dois integrantes.
- **Quem fala:** Luy.

## Slide 2 — O problema

- **Título:** "Dívida técnica deixa rastros em texto".
- **Conteúdo, à esquerda:** issues, pull requests e commits registram
  atalhos e pendências; é muito texto, e nada dele é estruturado. Nesta
  etapa: só texto do GitHub, com Regex e spaCy.
- **Conteúdo, à direita:** a pergunta de pesquisa, por extenso.
- **Quem fala:** Luy.

## Slide 3 — O que é dívida técnica

- **Conteúdo:** a definição em uma linha (atalhos e decisões de curto
  prazo que comprometem a qualidade e a manutenção) e os cinco tipos,
  cada um com o título de uma issue real coletada:

  | Tipo | Issue real |
  |---|---|
  | Código | "Debt: two implementations of chat model selection should be one" |
  | Arquitetura | "Share the command file-write parser contract across terminal auto-approval" |
  | Testes | "Flaky Tests: imports a prepared model directory and creates scanner metadata" |
  | Documentação | "update docs for MAX_CONTENT_LENGTH" |
  | Dependências | "Security: vulnerable dependency image-size" |

- **Observação:** a de documentação é do Flask; as outras, do VS Code. O
  programa classifica cada uma delas como `yes` no tipo indicado.
- **Quem fala:** Luy.

## Slide 4 — Fonte dos dados

- **Título:** "GitHub REST API".
- **Visual:** três cartões, um por fonte:

  | Fonte | Como vem | Texto do cartão |
  |---|---|---|
  | Issues | `GET /repos/{owner}/{repo}/issues` | Título, corpo e comentários. É a fonte padrão |
  | Pull requests | A mesma listagem, campo `pull_request` | No VS Code, 36 de 50 itens da listagem eram pull requests |
  | Commits | `GET /repos/{owner}/{repo}/commits` | A mensagem: primeira linha como título, o resto como corpo |

- **Linha final:** o usuário informa owner, repositório e quantidade.
  Sem token, são 60 requisições por hora.
- **Código a mostrar no editor:** `src/github_collector.py`,
  `_fetch_issues` e `_paginate`.
- **Quem fala:** Luy.

## Slide 5 — Metodologia

- **Título:** "Sete passos, do GitHub ao resultado".
- **Visual:** sete cartões numerados, os mesmos passos que o programa
  mostra na tela, de `[1/7]` a `[7/7]`:

  | Nº | Passo | Texto do cartão |
  |---|---|---|
  | 01 | Coleta | Issues, PRs e commits pela API |
  | 02 | Limpeza | Tira o Markdown, separa o código |
  | 03 | Regex | 36 padrões de dívida técnica |
  | 04 | spaCy e tecnologias | Lemas, classes e entidades; lista própria de 40 nomes |
  | 05 | Classificação | Cinco tipos de dívida, por regras |
  | 06 | Sentimento | VADER, com média por sentença |
  | 07 | Estatísticas | Frequências, tempo e resolução |

- **Rodapé:** cada passo acrescenta o seu resultado ao documento.
- **Código a mostrar no editor:** `src/pipeline.py`, `analyze`, que
  executa os passos 2 a 7; o passo 1 fica em `collect`.
- **Quem fala:** Luy.

## Slide 6 — Regex

- **Título:** "Limpar o texto e achar o literal".
- **Conteúdo:**
  - 22 expressões limpam o Markdown.
  - 36 padrões de dívida: 22 explícitos e 14 de contexto.
  - Um padrão para explicar:
    `\btech(?:nical)?[\s-]+debts?\b`
  - Limite: em 30 issues rotuladas como `debt`, só 11 têm um padrão
    explícito.
- **Visual:** três recursos de Regex usados (`\b`, lookahead negativo,
  referência retroativa `\1`) e o que cada um resolve.
- **Código a mostrar no editor:** `src/text_preprocessor.py`
  (`CODE_BLOCK`) e `src/regex_analyzer.py` (`PATTERNS`).
- **Quem fala:** Luy.

## Slide 7 — spaCy

- **Título:** "Tokens, lemas e gramática".
- **Conteúdo:**
  - Lema: remove, removed, removing, removes → `remove`.
  - Regex achou 8 ocorrências de "duplicated/duplication"; o lema
    `duplicate` reuniu 12.
  - Tecnologias não vêm do NER: lista própria com 40 nomes.
- **Visual:** duas colunas lado a lado, com dados reais das 30 issues
  `debt` do VS Code:

  | NER do modelo | Lista do projeto |
  |---|---|
  | UI [ORG] 25 | Copilot 20 |
  | Copilot [ORG] 11 | VS Code 19 |
  | CSS [ORG] 10 | CSS 14 |
  | Claude [PERSON] 4 | Codex 10 |

- **Atenção ao falar:** o NER reconheceu Copilot 12 vezes, 11 como
  organização (a linha da tabela) e 1 como pessoa. A lista achou 20.
- **Código a mostrar no editor:** `src/nlp_analyzer.py` (`is_relevant`)
  e `src/technology_analyzer.py` (`TECHNOLOGIES`).
- **Quem fala:** Luiz.

## Slide 8 — Classificação e sentimento

- **Título:** "Regras, não Machine Learning".
- **Conteúdo, lado esquerdo (classificação):**
  - Sim: padrão explícito da Regex, ou 3 ocorrências do vocabulário do
    tema.
  - Possível: 1 ou 2 ocorrências. Não: nenhuma evidência.
  - Exemplo: "needs refactoring and has no tests" dá código sim,
    arquitetura possível, testes sim.
- **Conteúdo, lado direito (sentimento):**
  - VADER: `compound = x / √(x² + 15)`, de -1 a +1; `x` é a soma das
    valências e 15, a constante de normalização.
  - Positivo ≥ +0,05; negativo ≤ -0,05.
  - Média por sentença; 37 termos técnicos sem valência.
  - Mede o tom do texto, não a dívida.
- **Rodapé, onde aprender:** github.com/cjhutto/vaderSentiment;
  spacy.io e course.spacy.io.
- **Código a mostrar no editor:** `src/debt_classifier.py` (`decide`).
- **Quem fala:** Luiz.

## Slide 9 — Resultados

- **Título:** "Metade da dívida rotulada é achada".
- **Visual:** quatro números grandes:

  | Número | Legenda |
  |---|---|
  | 16/30 | Issues `debt` do VS Code com dívida identificada |
  | 29/57 | Issues rotuladas como dívida, em três repositórios |
  | 3/15 | Pull requests `debt`: textos curtos rendem menos |
  | 1/9 | Alarmes no grupo de controle, com label `bug` |

- **Três linhas, sobre as 30 issues `debt` do VS Code:**
  - Tipos: código 7, testes 6, arquitetura 3, dependências 1,
    documentação 0.
  - Tom: 8 issues positivas, 15 neutras, 7 negativas.
  - Até fechar: mediana de 1,3 dia com dívida e 4,0 sem; no pandas se
    inverte.
- **Para dizer, sem estar no slide:** os 29 de 57 são a soma de VS Code
  (16 de 30), Kubernetes (8 de 15) e pandas (5 de 12); em 97 commits
  recentes do VS Code, 16 têm dívida identificada.
- **Quem fala:** Luiz.

## Slide 10 — Diário de bordo

- **Título:** "Três erros que os dados revelaram".
- **Conteúdo:** três problemas, cada um com a solução:

  | Problema | Solução |
  |---|---|
  | "todo" é um recurso do chat do VS Code, não um `TODO` | Marcador vale em maiúsculas, ou como `todo:` |
  | Em um corpus, 13 dos 16 comentários eram de um bot | Contas `[bot]` são ignoradas |
  | "shared" somava +95 pontos em 68 ocorrências | 37 termos técnicos sem valência |

- **Se sobrar tempo:** a pasta `hack/` do Kubernetes, contada 6 vezes
  como `HACK`, e as 206 assinaturas `Co-authored-by` nas mensagens de
  commit.
- **Quem fala:** Luy.

## Slide 11 — Demonstração

- **Título:** "O programa, com todas as opções".
- **Conteúdo:** os cinco comandos, na ordem em que são executados:

  ```text
  python main.py --check
  python main.py
  python main.py --file data/raw/microsoft_vscode_debt_issues.json
  python main.py --owner microsoft --repo vscode --limit 5 --label debt --source prs
  python main.py --text "Authentication needs refactoring and has no tests."
  ```

- **No segundo comando:** responder `psf`, `requests`, `5` e só Enter na
  label.
- **Reserva:** uma captura de tela da saída real, para o caso de o
  terminal falhar.
- **Quem fala:** Luiz.

## Slide 12 — Próximas etapas

- **Título:** "Do texto ao áudio e ao vídeo".
- **Conteúdo:**
  - 2ª etapa: áudio de podcasts e entrevistas sobre dívida técnica.
  - 3ª etapa: vídeo de palestras técnicas.
  - Ao final: dashboard com as três modalidades.
  - No texto, o próximo passo é rotular uma amostra à mão, para medir a
    classificação por tipo de dívida.
- **Para dizer:** a classificação ainda não distingue assunto de
  problema, e falta um gabarito por tipo.
- **Quem fala:** Luiz.

## Antes de exportar o PDF

- Conferir cada número dos slides contra a saída de
  `python main.py --file data/raw/microsoft_vscode_debt_issues.json`.
- Conferir os trechos de código contra os arquivos.
- Exportar pela página dos slides e salvar como `etapa1-DebtRadar.pdf`.
  Um PDF exportado antes de 13/10/2026 não tem as mudanças dos slides 5
  e 11.
