# Arquitetura do DebtRadar

Este documento explica como o programa está organizado: quais são as
partes, o que cada uma faz, como os dados passam de uma para outra e onde
o projeto pode ser estendido. Para o detalhe de cada função, veja
[REFERENCIA_MODULOS.md](REFERENCIA_MODULOS.md); para os campos de cada
arquivo, [FORMATO_DOS_DADOS.md](FORMATO_DOS_DADOS.md).

## Visão geral

O DebtRadar é um programa de linha de comando em Python. Ele coleta textos
de um repositório do GitHub e os passa por uma sequência fixa de análises.
Cada análise fica em um módulo próprio, e o resultado final é um resumo
mostrado no terminal e gravado em disco.

```text
                        ┌──────────────────────────────┐
                        │  main.py  (interface)        │
                        │  opções, perguntas, erros    │
                        └──────────────┬───────────────┘
                                       │
                        ┌──────────────▼───────────────┐
                        │  src/pipeline.py             │
                        │  executa as etapas em ordem  │
                        └──────────────┬───────────────┘
                                       │
   ┌───────────────┬───────────────────┼───────────────────┬───────────────┐
   ▼               ▼                   ▼                   ▼               ▼
 coleta         limpeza        Regex · spaCy ·       classificação    estatísticas
 github_        text_          tecnologias           sentimento       statistics_
 collector      preprocessor   regex_analyzer        debt_classifier  analyzer
                               nlp_analyzer          sentiment_
                               technology_analyzer   analyzer
                                       │
                        ┌──────────────▼───────────────┐
                        │  src/report.py               │
                        │  mostra o resumo no terminal │
                        └──────────────────────────────┘

   Apoio: src/config.py (caminhos e .env) · src/storage.py (JSON em disco)
```

## As camadas

| Camada | Arquivos | Responsabilidade | O que NÃO faz |
|---|---|---|---|
| Interface | `main.py` | Lê as opções da linha de comando, faz as perguntas do modo interativo, transforma erros em mensagens | Nenhuma análise |
| Orquestração | `src/pipeline.py` | Chama as etapas em ordem, mostra o andamento `[1/7]`…`[7/7]`, grava os arquivos | Nenhuma regra de análise |
| Etapas | `github_collector`, `text_preprocessor`, `regex_analyzer`, `nlp_analyzer`, `technology_analyzer`, `debt_classifier`, `sentiment_analyzer`, `statistics_analyzer` | Cada módulo resolve um problema | Não imprimem nada e não conhecem as outras etapas |
| Apresentação | `src/report.py` | Formata o resumo consolidado para o terminal | Não calcula nada: só lê o resumo |
| Apoio | `src/config.py`, `src/storage.py` | Caminhos, variáveis do `.env`, leitura e gravação de JSON | |

Duas regras sustentam essa divisão:

1. **As etapas não imprimem e não se conhecem.** Elas recebem dados e
   devolvem dados. Por isso cada uma pode ser testada sozinha, e por isso
   a opção `--text` consegue reaproveitar todas para um único texto.
2. **O relatório lê só o resumo.** Tudo o que aparece na tela está em
   `data/results/..._summary.json`. Um dashboard futuro pode ler o mesmo
   arquivo sem tocar no restante do código.

## O pipeline, etapa por etapa

A coluna "Passo" é o número mostrado na tela durante a execução. A busca
de tecnologias roda dentro do passo 4, porque usa o mesmo documento do
spaCy.

| Passo | Função em `pipeline.py` | Módulo chamado | Entrada | O que acrescenta |
|---|---|---|---|---|
| 1 | `collect` ou `load` | `github_collector` | owner, repositório, quantidade, label, fontes — ou um arquivo salvo | A coleta: `metadata` e a lista de registros |
| 2 | `preprocess` | `text_preprocessor` | Registros da coleta | Um documento por registro, com `text` e `code` |
| 3 | `apply_regex` | `regex_analyzer` | `text` e `code` | Chave `regex` |
| 4 | `apply_spacy` | `nlp_analyzer`, `technology_analyzer` | `text` | Chaves `nlp` e `technologies` |
| 5 | `classify` | `debt_classifier` | `regex` e `nlp` | Chave `classification` |
| 6 | `measure_sentiment` | `sentiment_analyzer` | `text` | Chave `sentiment` |
| 7 | `analyze` (trecho final) | `statistics_analyzer` | Todos os documentos | O resumo consolidado |

O documento é um dicionário que **só cresce**: nenhuma etapa apaga ou
altera o que outra escreveu. A ordem importa em um ponto só: a
classificação (5) precisa da Regex (3) e do spaCy (4).

## Fluxo dos dados

```text
API do GitHub
     │  github_collector.collect()
     ▼
coleta  ──────────────────────────────►  data/raw/<nome>.json
     │  text_preprocessor.preprocess_issue()   (um por registro; bots saem)
     ▼
documentos  { type, id, title, …, text, code }
     │  + regex   + nlp   + technologies   + classification   + sentiment
     ▼
documentos analisados  ───────────────►  data/processed/<nome>.json
     │  statistics_analyzer.build_summary()
     ▼
resumo  ──────────────────────────────►  data/results/<nome>_summary.json
     │  report.print_report()
     ▼
terminal
```

Os três arquivos têm o mesmo nome-base. Como a coleta fica gravada, a
análise pode ser refeita sem rede com `--file`, quantas vezes for preciso.

## Dependências entre os módulos

Levantadas dos `import` do código. Uma seta significa "importa de".

```text
main.py ─────────► config, pipeline, github_collector (só SOURCES), report

pipeline ────────► config, storage, github_collector, text_preprocessor,
                   regex_analyzer, nlp_analyzer*, technology_analyzer*,
                   debt_classifier, sentiment_analyzer, statistics_analyzer,
                   report (só count)

github_collector ► config, storage
report ──────────► config, statistics_analyzer (só TYPE_NAMES)
statistics_analyzer ► debt_classifier (só CATEGORIES)

Sem dependências internas: config, storage, text_preprocessor,
regex_analyzer, nlp_analyzer, technology_analyzer, debt_classifier,
sentiment_analyzer
```

`*` importados dentro das funções, e não no topo do arquivo. Assim
`python main.py --check` consegue rodar e explicar o que falta mesmo em
uma máquina sem o spaCy instalado.

Bibliotecas externas e onde entram:

| Biblioteca | Usada em | Para quê |
|---|---|---|
| `requests` | `github_collector` | Requisições à API do GitHub |
| `python-dotenv` | `config` | Ler o arquivo `.env` |
| `spacy` | `nlp_analyzer`, `technology_analyzer`, `main` (só no `--check`) | Análise linguística e `PhraseMatcher` |
| `vaderSentiment` | `sentiment_analyzer` | Léxico de sentimento |
| `re`, `unicodedata` | `text_preprocessor`, `regex_analyzer`, `sentiment_analyzer` | Limpeza, padrões, divisão em sentenças |
| `pytest` | `tests/` | Testes |

## Tratamento de erros

Há três tipos de erro próprios, um por camada. Todos carregam uma
mensagem em português pronta para o usuário.

| Erro | Onde nasce | Quem trata | Exemplos |
|---|---|---|---|
| `ConfigError` | `config.load_config` | `main.main` | `DEFAULT_ISSUES=abc` |
| `GitHubError` e `RateLimitError` | `github_collector` | `pipeline.collect`, que o converte em `PipelineError` | Repositório não encontrado, token inválido, limite atingido, timeout |
| `PipelineError` | `pipeline` | `main.run_pipeline` e `main.run_explanation` | Arquivo que não é uma coleta, modelo do spaCy ausente, só registros de bots |

Um caso não vira erro de propósito: se o limite da API acaba **durante a
busca dos comentários**, a coleta é mantida, `metadata.warning` explica o
que faltou e `comments_complete` fica falso.

O programa termina com código `0` em caso de sucesso, `1` em qualquer
erro tratado e `130` se for interrompido com Ctrl+C.

## Configuração e segredos

- O único segredo é o `GITHUB_TOKEN`, lido do arquivo `.env`, que está no
  `.gitignore`.
- O token vai apenas no cabeçalho `Authorization` das requisições. Ele
  não aparece na representação do objeto `Config`, nas mensagens, nem nos
  arquivos de dados.
- O coletor só segue links de próxima página que comecem com o endereço
  da API do GitHub, porque o token acompanha toda requisição.

## Pontos de extensão

O que foi desenhado para crescer, e onde mexer. O passo a passo de cada
um está em [GUIA_DE_DESENVOLVIMENTO.md](GUIA_DE_DESENVOLVIMENTO.md).

| Quero acrescentar | Onde | Efeito colateral a lembrar |
|---|---|---|
| Um padrão de Regex | Lista `PATTERNS` em `regex_analyzer.py` | Se for explícito e de uma categoria, incluir em `STRONG_PATTERNS` do classificador |
| Uma tecnologia | Dicionário `TECHNOLOGIES` em `technology_analyzer.py` | Nomes ambíguos também em `CASE_SENSITIVE` |
| Vocabulário de um tipo de dívida | `TERMS` em `debt_classifier.py` | Em forma de lema |
| Um termo técnico neutro no sentimento | `TECHNICAL_NEUTRAL` em `sentiment_analyzer.py` | |
| Uma conta de bot | `KNOWN_BOTS` em `text_preprocessor.py` | |
| Uma fonte de dados | `github_collector.py`: uma função `normalize_…` e um `_fetch_…` | Devolver o mesmo formato de registro; incluir em `SOURCES` e em `TYPE_NAMES` |
| Uma etapa de análise | Um módulo novo e uma função em `pipeline.py` | Escrever em uma chave nova do documento; somar no resumo |
| Um bloco no relatório | Uma função `print_…` em `report.py` | Ler só o resumo |
| Uma opção de linha de comando | `build_parser` em `main.py` | |

## Limites conhecidos da arquitetura

- **Tudo em memória.** A coleta e os documentos ficam inteiros em
  memória. Serve para centenas de registros; não foi pensado para
  dezenas de milhares.
- **Sem execução incremental.** Cada execução refaz todas as etapas. É
  rápido (cerca de dois segundos para 30 issues), então não houve
  necessidade.
- **A lista de registros se chama `issues`** nos arquivos de coleta,
  mesmo quando traz pull requests e commits. O nome foi mantido para as
  coletas antigas continuarem válidas.
- **Um idioma.** O modelo do spaCy e o léxico de sentimento são para
  inglês.
- **O texto é o único tipo de dado.** Áudio e vídeo, das próximas etapas,
  ainda não têm lugar na estrutura; veja
  [PROXIMAS_ETAPAS.md](PROXIMAS_ETAPAS.md).
