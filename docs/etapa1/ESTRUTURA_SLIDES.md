# Estrutura dos Slides — DebtRadar (1ª etapa)

Doze slides para 10 minutos. Os slides sustentam a fala; não a
substituem. Tudo o que aparece aqui vem do programa e dos dados reais.

## Regras de formato

- Pouco texto: no máximo quatro tópicos curtos por slide.
- Código em fonte grande, com poucas linhas, igual ao do arquivo.
- Números sempre com a unidade: "16 de 30 issues", não "53%" sozinho.
- A demonstração é ao vivo; o slide dela traz só os comandos.
- Exportar em PDF com o nome `etapa1-DebtRadar.pdf`.

## Slide 1 — DebtRadar

- **Conteúdo:** "DebtRadar — Analisador Multimodal de Dívida Técnica";
  1ª etapa: texto; disciplina; nomes dos dois integrantes.
- **Quem fala:** Integrante 1.

## Slide 2 — Problema e pergunta de pesquisa

- **Conteúdo:**
  - Dívida técnica deixa rastros em texto, mas esse texto não é
    estruturado.
  - Pergunta: como os desenvolvedores identificam, discutem e priorizam
    a dívida técnica?
  - Nesta etapa: issues, pull requests e commits do GitHub, com Regex
    e spaCy.
- **Quem fala:** Integrante 1.

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

- **Observação:** a de documentação é do Flask; as outras, do VS Code.
- **Quem fala:** Integrante 1.

## Slide 4 — Fonte dos dados

- **Conteúdo:**
  - GitHub REST API: `GET /repos/{owner}/{repo}/issues` e `.../commits`.
  - Três fontes, escolhidas por `--source`: issues, pull requests e
    mensagens de commit.
  - Por registro: título, corpo, autor, datas, labels, comentários.
  - Sem token: 60 requisições por hora.
- **Visual:** os três campos que o usuário informa (owner, repositório,
  quantidade) ao lado de um trecho do JSON de uma issue.
- **Código a mostrar no editor:** `src/github_collector.py`,
  `_fetch_issues` e `_paginate`.
- **Quem fala:** Integrante 1.

## Slide 5 — Metodologia

- **Visual:** o pipeline, em uma coluna:

  ```text
  GitHub API
      ↓
  Coleta
      ↓
  Pré-processamento
      ↓
  Regex
      ↓
  spaCy e tecnologias
      ↓
  Classificação
      ↓
  Sentimento
      ↓
  Estatísticas e resultado
  ```

- **Conteúdo:** uma frase: cada etapa acrescenta o seu resultado ao
  documento da issue.
- **Código a mostrar no editor:** `src/pipeline.py`, `analyze`.
- **Quem fala:** Integrante 1.

## Slide 6 — Regex

- **Conteúdo:**
  - Limpeza do Markdown: 22 expressões.
  - Detecção: 36 padrões, 22 explícitos e 14 de contexto.
  - Um padrão para explicar:
    `\btech(?:nical)?[\s-]+debts?\b`
  - Limite: em 30 issues rotuladas como `debt`, só 11 têm um padrão
    explícito.
- **Visual:** uma tabela pequena com três recursos de Regex usados
  (`\b`, lookahead negativo, referência retroativa `\1`) e o que cada um
  resolve.
- **Código a mostrar no editor:** `src/text_preprocessor.py`
  (`CODE_BLOCK`) e `src/regex_analyzer.py` (`PATTERNS`).
- **Quem fala:** Integrante 1.

## Slide 7 — spaCy

- **Conteúdo:**
  - Tokens, lemas, stopwords, classes gramaticais, entidades.
  - Lema: remove, removed, removing, removes → `remove`.
  - Regex achou 8 ocorrências de "duplicated/duplication"; o lema
    `duplicate` reuniu 12.
  - Tecnologias não vêm do NER: lista própria com 40 nomes.
- **Visual:** duas colunas lado a lado, com dados reais:

  | NER do modelo | Lista do projeto |
  |---|---|
  | UI [ORG] 25 | Copilot 20 |
  | Copilot [ORG] 11 | VS Code 19 |
  | CSS [ORG] 10 | CSS 14 |
  | Claude [PERSON] 4 | Codex 10 |

- **Código a mostrar no editor:** `src/nlp_analyzer.py` (`is_relevant`)
  e `src/technology_analyzer.py` (`TECHNOLOGIES`).
- **Quem fala:** Integrante 2.

## Slide 8 — Classificação e sentimento

- **Conteúdo, lado esquerdo (classificação):**
  - Baseline de regras, sem Machine Learning.
  - `yes`: padrão explícito, ou 3 ocorrências do vocabulário do tema.
  - `possible`: 1 ou 2 ocorrências. `no`: nenhuma.
- **Conteúdo, lado direito (sentimento):**
  - VADER: `compound = x / √(x² + 15)`, de -1 a +1.
  - Positivo ≥ +0,05; negativo ≤ -0,05.
  - Média por sentença; 37 termos técnicos neutralizados.
- **Rodapé, onde aprender:** VADER em github.com/cjhutto/vaderSentiment;
  spaCy em spacy.io e course.spacy.io.
- **Código a mostrar no editor:** `src/debt_classifier.py` (`decide`).
- **Quem fala:** Integrante 2.

## Slide 9 — Resultados

- **Conteúdo:** o corpus principal, 30 issues `debt` do VS Code:
  - 16 de 30 com dívida identificada.
  - Por tipo: código 7, testes 6, arquitetura 3, dependências 1,
    documentação 0.
  - Sentimento: 8 positivas, 15 neutras, 7 negativas.
- **Visual:** a tabela de validação:

  | Corpus | Issues | Dívida identificada |
  |---|---|---|
  | VS Code, label `debt` | 30 | 16 |
  | Kubernetes, label `kind/cleanup` | 15 | 8 |
  | pandas, label `Refactor` | 12 | 5 |
  | VS Code, label `bug` (controle) | 9 | 1 |

  Total nas três labels de dívida: 29 de 57.
- **Uma linha por fonte, no VS Code:** issues `debt` 16 de 30; pull
  requests `debt` 3 de 15; commits recentes 16 de 97.
- **Uma linha de priorização:** mediana até fechar de 1,3 dia com dívida
  contra 4,0 sem (indício; no pandas se inverte).
- **Quem fala:** Integrante 2.

## Slide 10 — Diário de bordo

- **Conteúdo:** três problemas, cada um em duas linhas:

  | Problema | Solução |
  |---|---|
  | "todo" é um recurso do VS Code, não um `TODO` | Marcador vale em maiúsculas, ou como `todo:` |
  | 13 de 16 comentários eram de um bot | Contas `[bot]` são ignoradas |
  | "shared" somava +95 pontos de sentimento | 37 termos técnicos sem valência |

- **Opcional, se couber:** a pasta `hack/` do Kubernetes contada como
  `HACK` (6 ocorrências falsas).
- **Quem fala:** Integrante 1.

## Slide 11 — Demonstração

- **Conteúdo:** só os comandos, em fonte grande:

  ```text
  python main.py
  python main.py --file data/raw/microsoft_vscode_debt_issues.json
  python main.py --text "Authentication needs refactoring and has no tests."
  ```

- **Reserva:** uma captura de tela da saída real, guardada em um slide
  oculto, para o caso de o terminal falhar.
- **Quem fala:** Integrante 2.

## Slide 12 — Próximas etapas

- **Conteúdo:**
  - 2ª etapa: áudio de podcasts sobre dívida técnica.
  - 3ª etapa: vídeo de palestras.
  - Dashboard final com as três modalidades.
  - Limitação a atacar no texto: a classificação ainda não distingue
    assunto de problema.
- **Quem fala:** Integrante 2.

## Antes de exportar o PDF

- Conferir cada número dos slides contra a saída de
  `python main.py --file data/raw/microsoft_vscode_debt_issues.json`.
- Conferir os trechos de código contra os arquivos.
- Salvar como `etapa1-DebtRadar.pdf`.
