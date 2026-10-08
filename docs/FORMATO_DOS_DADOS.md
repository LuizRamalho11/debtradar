# Formato dos Dados

Este documento descreve todos os arquivos que o DebtRadar grava: onde
ficam, como são nomeados e o que significa cada campo. Ele é a referência
para quem for ler esses arquivos em outra etapa do projeto, como o
dashboard final.

Todos os arquivos são JSON em UTF-8, com indentação de dois espaços.

## Os três arquivos de uma execução

| Pasta | Arquivo | Gravado por | Conteúdo |
|---|---|---|---|
| `data/raw/` | `<nome>.json` | `github_collector.save_collection` | A coleta, com os campos da API já normalizados |
| `data/processed/` | `<nome>.json` | `pipeline.save_results` | Um documento por registro, com todas as análises |
| `data/results/` | `<nome>_summary.json` | `pipeline.save_results` | O resumo consolidado do corpus |

### Como o nome é formado

```text
<owner>_<repo>[_<label>]_<fonte>.json
```

- tudo em minúsculas;
- a label só entra se foi usada; caracteres que não são letras nem
  números viram `-` (`kind/cleanup` → `kind-cleanup`);
- a fonte é `issues`, `prs` ou `commits`; com mais de uma fonte, `all`.

Exemplos reais: `microsoft_vscode_debt_issues.json`,
`microsoft_vscode_debt_prs.json`, `microsoft_vscode_commits.json`,
`psf_requests_all.json`, `kubernetes_kubernetes_kind-cleanup_issues.json`.

Repetir uma coleta com os mesmos parâmetros substitui os três arquivos. A
coleta anterior é movida para `data/raw/backup/`, com data e hora no nome.

### Regras gerais

- **Campos de texto nunca são nulos.** Quando a API não traz o valor, o
  campo fica como string vazia. A única exceção é `number`, que é nulo em
  commits.
- **Datas** são strings no formato ISO 8601 da API, em UTC, como
  `2026-09-21T22:48:29Z`. As datas geradas pelo programa
  (`collected_at`, `generated_at`) usam o mesmo padrão, com `+00:00`.
- **E-mails são mascarados.** Endereços de e-mail que apareçam em
  títulos, corpos e comentários são trocados por `redacted@example.com`
  no momento da coleta.
- **Categorias e rótulos** ficam em inglês nos arquivos (`code`, `yes`,
  `positive`); a tradução para o português é feita só na apresentação.

## Coleta (`data/raw/`)

Dois campos na raiz: `metadata` e `issues`.

### `metadata`

| Campo | Tipo | Significado |
|---|---|---|
| `source` | texto | Sempre `"github"` |
| `owner` | texto | Dono ou organização do repositório |
| `repo` | texto | Nome do repositório |
| `label` | texto | Label usada no filtro; vazio se nenhuma |
| `sources` | lista de textos | Fontes coletadas, na ordem `issues`, `prs`, `commits`. Ausente em coletas antigas, que são só de issues |
| `requested` | inteiro | Quantidade pedida para cada fonte |
| `collected` | inteiro | Total de registros coletados, somando as fontes |
| `collected_at` | data | Momento da coleta |
| `comments_complete` | booleano | Falso se a busca de comentários foi interrompida, por exemplo pelo limite da API |
| `warning` | texto | Explicação quando algo ficou incompleto; vazio no caso normal |

### `issues`: a lista de registros

O nome é `issues` por compatibilidade, mas a lista pode trazer os três
tipos de registro. Todos têm os mesmos campos.

| Campo | Tipo | Issue e pull request | Commit |
|---|---|---|---|
| `type` | texto | `"issue"` ou `"pull_request"` | `"commit"` |
| `id` | texto | `"#"` mais o número, como `"#329218"` | Os 7 primeiros caracteres do hash |
| `number` | inteiro ou nulo | Número no repositório | Nulo |
| `title` | texto | Título | Primeira linha da mensagem |
| `body` | texto | Corpo, em Markdown | Restante da mensagem |
| `author` | texto | Login do autor | Login do GitHub; se não houver, o nome gravado no commit |
| `state` | texto | `"open"` ou `"closed"` | Vazio |
| `labels` | lista de textos | Nomes das labels | Lista vazia |
| `created_at` | data | Criação | Data de autoria do commit |
| `updated_at` | data | Última atualização | Igual a `created_at` |
| `closed_at` | data | Fechamento; vazio se aberta | Vazio |
| `url` | texto | Endereço da página no GitHub | Endereço do commit |
| `comments_count` | inteiro | Comentários informados pela API | `0` |
| `comments` | lista | Comentários coletados (até 100) | Lista vazia |
| `comments_collected` | booleano | Se os comentários deste registro foram buscados | `true` |

`type` e `id` não existem em coletas feitas antes da opção `--source`.
Ao ler essas coletas, o programa trata os registros como issues e monta o
`id` a partir do número.

### Cada item de `comments`

| Campo | Tipo | Significado |
|---|---|---|
| `author` | texto | Login de quem comentou |
| `body` | texto | Texto do comentário, em Markdown |
| `created_at` | data | Quando foi escrito |
| `url` | texto | Endereço do comentário |

## Documentos analisados (`data/processed/`)

Dois campos na raiz: `metadata` e `documents`.

O `metadata` repete o da coleta e acrescenta:

| Campo | Tipo | Significado |
|---|---|---|
| `bot_issues_ignored` | inteiro | Registros descartados por terem sido criados por bots |
| `spacy_model` | texto | Modelo usado, com versão: `en_core_web_sm 3.8.0` |
| `generated_at` | data | Momento da análise |

### Campos de identificação de cada documento

Copiados do registro: `type`, `id`, `number`, `title`, `url`, `author`,
`state`, `labels`, `created_at`, `updated_at`, `closed_at` e
`comments_count`. O `body` e os comentários originais não são copiados;
eles continuam no arquivo de coleta.

### Campos produzidos pelo pré-processamento

| Campo | Tipo | Significado |
|---|---|---|
| `text` | texto | Título, corpo e comentários de pessoas, limpos e unidos por linhas em branco |
| `code` | texto | Conteúdo dos blocos de código retirados do texto |
| `bot_comments_ignored` | inteiro | Comentários descartados por serem de bots |

### `regex`

| Campo | Tipo | Significado |
|---|---|---|
| `technical_debt_detected` | booleano | Verdadeiro se há ao menos um padrão explícito |
| `patterns` | objeto | Nome do padrão → número de ocorrências |
| `categories` | objeto | Categoria → número de ocorrências |
| `matches` | lista | Uma entrada por ocorrência, na ordem em que aparecem |

Cada item de `matches`:

| Campo | Tipo | Significado |
|---|---|---|
| `pattern` | texto | Nome do padrão, como `todo` ou `missing_tests` |
| `category` | texto | `general`, `code`, `architecture`, `tests`, `documentation` ou `dependencies` |
| `explicit` | booleano | Verdadeiro se o padrão por si só indica dívida |
| `text` | texto | O trecho encontrado, como foi escrito |
| `source` | texto | `"text"` ou `"code"`: em qual dos dois campos foi achado |
| `start`, `end` | inteiros | Posição do trecho dentro de `text` ou de `code` |
| `context` | texto | Até 50 caracteres antes e depois, para conferência |

### `nlp`

| Campo | Tipo | Significado |
|---|---|---|
| `tokens` | inteiro | Tokens do spaCy, sem contar espaços |
| `sentences` | inteiro | Sentenças segundo o spaCy |
| `pos` | objeto | Classe gramatical → número de tokens |
| `lemmas` | objeto | Três grupos, `noun`, `adjective` e `verb`; em cada um, lema → ocorrências |
| `noun_phrases` | objeto | Expressão nominal de duas ou mais palavras → ocorrências |
| `entities` | lista | Entidades do NER: `text`, `label` e `count` |

Só entram em `lemmas` e `noun_phrases` os tokens alfabéticos, com três
letras ou mais, que não são stopwords nem identificadores de código.

### `technologies`

Lista de objetos, da mais citada para a menos citada:

| Campo | Tipo | Significado |
|---|---|---|
| `name` | texto | Nome oficial, como em `TECHNOLOGIES` |
| `category` | texto | `language`, `framework`, `database`, `tool` ou `platform` |
| `count` | inteiro | Menções no documento |

### `classification`

| Campo | Tipo | Significado |
|---|---|---|
| `categories` | objeto | Para cada um dos cinco tipos, `"yes"`, `"possible"` ou `"no"` |
| `evidence` | objeto | Para cada tipo, o que levou à decisão |

Em `evidence`, cada tipo tem `patterns` (padrões da Regex que contaram,
com o número de ocorrências) e `terms` (lemas do vocabulário do tema, com
o número de ocorrências).

### `sentiment`

| Campo | Tipo | Significado |
|---|---|---|
| `label` | texto | `"positive"`, `"neutral"` ou `"negative"` |
| `compound` | número | Média do `compound` das sentenças, de -1 a +1, com quatro casas |
| `sentences` | inteiro | Sentenças pontuadas |
| `positive_sentences`, `negative_sentences`, `neutral_sentences` | inteiros | Quantas sentenças em cada rótulo |

A contagem de sentenças aqui pode diferir da de `nlp`: o sentimento
divide o texto com uma Regex própria, e não com o spaCy.

## Resumo consolidado (`data/results/`)

É o arquivo que o relatório do terminal lê, e o ponto de entrada indicado
para um dashboard.

### `metadata`

O mesmo dos documentos analisados.

### `totals`

| Campo | Tipo | Significado |
|---|---|---|
| `documents` | inteiro | Documentos analisados (sem os de bots) |
| `debt_documents` | inteiro | Com dívida identificada: padrão explícito **ou** algum tipo `yes` |
| `explicit_debt_documents` | inteiro | Com ao menos um padrão explícito da Regex |
| `classified_documents` | inteiro | Com ao menos um tipo `yes` |
| `tokens` | inteiro | Soma dos tokens |
| `sentences` | inteiro | Soma das sentenças do spaCy |
| `first_date`, `last_date` | data | Primeira e última data de criação, só o dia |

### `by_type`

Um objeto por tipo de registro presente (`issue`, `pull_request`,
`commit`), com `documents` e `debt_documents`.

### `classification`

Um objeto por tipo de dívida, com as contagens `yes`, `possible` e `no`.
Em cada tipo, as três somam o total de documentos.

### `resolution`

Dois grupos, `with_debt` e `without_debt`, formados só por issues e pull
requests (commits não têm estado):

| Campo | Tipo | Significado |
|---|---|---|
| `documents` | inteiro | Registros no grupo |
| `closed` | inteiro | Quantos estão fechados |
| `median_days_to_close` | número ou nulo | Mediana de dias entre criação e fechamento; nulo se nenhum fechou |

### `sentiment`

- `overall`: `documents`, `positive`, `neutral`, `negative` e
  `mean_compound`;
- `by_category`: os mesmos campos, para os documentos em que cada tipo
  de dívida é `yes`.

### `frequencies`

Todas as listas vêm da mais frequente para a menos frequente.

| Campo | Conteúdo de cada item | Limite |
|---|---|---|
| `terms.noun`, `terms.adjective`, `terms.verb` | `name`, `count`, `documents` | 20 |
| `noun_phrases` | `name`, `count`, `documents` | 20 |
| `technologies` | `name`, `category`, `count`, `documents` | sem limite |
| `entities` | `name`, `text`, `label`, `count`, `documents` | 20 |
| `regex_patterns` | `name`, `category`, `count`, `documents` | sem limite |
| `debt_categories` | `name`, `yes`, `possible`, `no` | os cinco tipos |

Em todas, `count` é o total de ocorrências no corpus e `documents` é em
quantos documentos o item aparece. Em `entities`, `name` junta o texto e
o rótulo (`"UI [ORG]"`), porque o mesmo texto com rótulos diferentes
conta separado.

### `timeline`

Uma entrada por mês de criação, em ordem:

| Campo | Tipo | Significado |
|---|---|---|
| `month` | texto | `AAAA-MM`, ou `"unknown"` se o registro não tem data |
| `documents` | inteiro | Registros criados no mês |
| `debt_documents` | inteiro | Com dívida identificada |
| `explicit_debt` | inteiro | Com padrão explícito |
| `categories` | objeto | Tipo de dívida → quantos `yes` no mês |
| `mean_compound` | número | Média do sentimento no mês |

No terminal, períodos com mais de 12 meses são somados por ano; o
arquivo continua mês a mês.

## Verificações de coerência

Relações que devem valer em qualquer resumo, usadas na conferência dos
resultados:

- em cada tipo de dívida, `yes + possible + no = totals.documents`;
- `positive + neutral + negative = totals.documents`;
- a soma de `documents` na `timeline` é `totals.documents`, e a de
  `debt_documents` é `totals.debt_documents`;
- a soma de `documents` em `by_type` é `totals.documents`;
- `debt_documents` fica entre o maior de `explicit_debt_documents` e
  `classified_documents` e a soma dos dois;
- `metadata.collected - metadata.bot_issues_ignored = totals.documents`.

## Exemplos reais

Os valores abaixo saíram de arquivos gerados pelo programa.

### Exemplo de resumo

`data/results/<arquivo>_summary.json` (valores reais, listas encurtadas):

```json
{
  "metadata": {"owner": "microsoft", "repo": "vscode", "label": "debt"},
  "totals": {
    "documents": 30,
    "debt_documents": 16,
    "tokens": 14830,
    "sentences": 881,
    "explicit_debt_documents": 11,
    "classified_documents": 13,
    "first_date": "2026-07-31",
    "last_date": "2026-10-06"
  },
  "by_type": {
    "issue": {"documents": 30, "debt_documents": 16}
  },
  "classification": {
    "code": {"yes": 7, "possible": 11, "no": 12}
  },
  "resolution": {
    "with_debt": {"documents": 16, "closed": 7, "median_days_to_close": 1.3},
    "without_debt": {"documents": 14, "closed": 7, "median_days_to_close": 4.0}
  },
  "sentiment": {
    "overall": {"documents": 30, "positive": 8, "neutral": 15, "negative": 7, "mean_compound": -0.0079},
    "by_category": {
      "code": {"documents": 7, "positive": 2, "neutral": 3, "negative": 2, "mean_compound": -0.0055}
    }
  },
  "frequencies": {
    "terms": {"noun": [{"name": "icon", "count": 72, "documents": 3}], "adjective": [], "verb": []},
    "noun_phrases": [{"name": "agent host", "count": 19, "documents": 10}],
    "technologies": [{"name": "Copilot", "category": "tool", "count": 20, "documents": 7}],
    "entities": [{"name": "UI [ORG]", "text": "UI", "label": "ORG", "count": 25, "documents": 9}],
    "regex_patterns": [{"name": "cleanup", "category": "general", "count": 11, "documents": 11}],
    "debt_categories": [{"name": "code", "yes": 7, "possible": 11, "no": 12}]
  },
  "timeline": [
    {"month": "2026-08", "documents": 22, "debt_documents": 11, "explicit_debt": 9,
     "categories": {"code": 4, "architecture": 1, "tests": 3, "documentation": 0, "dependencies": 1},
     "mean_compound": -0.0189}
  ]
}
```

`debt_documents` conta os documentos com marcador explícito da Regex ou
com ao menos um tipo de dívida confirmado pelas regras. `by_type` separa
as contagens por fonte, e `resolution` compara o fechamento de issues e
pull requests com e sem dívida (commits não têm estado).

### Exemplo de documento analisado

Cada documento de `data/processed/` tem os dados do registro (inclusive
`type`, que diz se é `issue`, `pull_request` ou `commit`, e `id`, como
`#329218` ou o início do hash do commit), o texto limpo e o resultado de
cada etapa. Primeiro, as Regex:

```json
{
  "number": 329218,
  "title": "Replace sed script-argument deny regexes with a shared script analyzer",
  "url": "https://github.com/microsoft/vscode/issues/329218",
  "author": "anthonykim1",
  "state": "open",
  "labels": ["debt", "agent-host", "terminal-auto-approve"],
  "created_at": "2026-08-05T17:27:55Z",
  "updated_at": "2026-08-12T09:47:07Z",
  "closed_at": "",
  "comments_count": 0,
  "bot_comments_ignored": 0,
  "text": "texto limpo: título, corpo e comentários",
  "code": "conteúdo dos blocos de código",
  "regex": {
    "technical_debt_detected": true,
    "patterns": {"debt": 1, "duplication": 1, "todo": 1},
    "categories": {"general": 1, "code": 2},
    "matches": [
      {
        "pattern": "todo",
        "category": "code",
        "explicit": true,
        "text": "TODO",
        "source": "text",
        "start": 2120,
        "end": 2124,
        "context": "and terminalChatAgentToolsConfiguration.ts carry TODO comments pointing here. Add tests for the shapes"
      }
    ]
  }
}
```

`start` e `end` são as posições da ocorrência dentro de `text` (ou de
`code`, conforme `source`).

A etapa do spaCy acrescenta as chaves `nlp` e `technologies` (valores
reais da issue #334760, listas encurtadas):

```json
{
  "nlp": {
    "tokens": 451,
    "sentences": 23,
    "pos": {"NOUN": 147, "PUNCT": 104, "VERB": 51},
    "lemmas": {
      "noun": {"file": 26, "owner": 21, "test": 8},
      "adjective": {"applicable": 2, "local": 1, "new": 1},
      "verb": {"suggest": 21, "remove": 4}
    },
    "noun_phrases": {"suggested owner": 10, "allowlisted test file": 2},
    "entities": [
      {"text": "ESLint", "label": "ORG", "count": 2},
      {"text": "JavaScript", "label": "PRODUCT", "count": 1},
      {"text": "TypeScript", "label": "ORG", "count": 1}
    ]
  },
  "technologies": [
    {"name": "ESLint", "category": "tool", "count": 2},
    {"name": "JavaScript", "category": "language", "count": 1},
    {"name": "TypeScript", "category": "language", "count": 1}
  ]
}
```

`entities` são as entidades do NER do modelo; `technologies` são as
tecnologias encontradas pela lista do projeto. As duas ficam separadas.

As etapas de classificação e sentimento acrescentam `classification` e
`sentiment` (valores reais da issue #330885):

```json
{
  "classification": {
    "categories": {
      "code": "yes",
      "architecture": "possible",
      "tests": "possible",
      "documentation": "no",
      "dependencies": "no"
    },
    "evidence": {
      "code": {"patterns": {"refactor": 1}, "terms": {"legacy": 1, "unused": 1}},
      "architecture": {"patterns": {"refactor": 1}, "terms": {"architecture": 1}},
      "tests": {"patterns": {}, "terms": {"test": 2}},
      "documentation": {"patterns": {}, "terms": {}},
      "dependencies": {"patterns": {}, "terms": {}}
    }
  },
  "sentiment": {
    "label": "neutral",
    "compound": -0.0084,
    "sentences": 41,
    "positive_sentences": 2,
    "negative_sentences": 3,
    "neutral_sentences": 36
  }
}
```

### Exemplo de coleta

```json
{
  "metadata": {
    "source": "github",
    "owner": "microsoft",
    "repo": "vscode",
    "label": "debt",
    "requested": 30,
    "collected": 30,
    "collected_at": "2026-10-07T23:36:02+00:00",
    "comments_complete": true,
    "warning": ""
  },
  "issues": [
    {
      "number": 337178,
      "title": "Remove automation client-side support",
      "body": "texto da issue...",
      "author": "benvillalobos",
      "state": "closed",
      "labels": ["debt", "automations"],
      "created_at": "2026-09-21T22:48:29Z",
      "updated_at": "2026-09-25T23:45:09Z",
      "closed_at": "2026-09-25T23:45:09Z",
      "url": "https://github.com/microsoft/vscode/issues/337178",
      "comments_count": 2,
      "comments": [
        {
          "author": "ulugbekna",
          "body": "texto do comentário...",
          "created_at": "2026-09-22T13:17:37Z",
          "url": "https://github.com/microsoft/vscode/issues/337178#issuecomment-5777236721"
        }
      ],
      "comments_collected": true
    }
  ]
}
```

Campos de texto nunca são nulos: quando a API não traz o valor, o campo
fica como string vazia (por exemplo, `closed_at` em issues abertas).
`comments_collected` indica se os comentários daquela issue foram buscados;
são guardados no máximo 100 comentários por issue.

A lista se chama `issues` mesmo quando traz outros tipos. Nas coletas
feitas a partir da versão com `--source`, cada registro tem também `type`
e `id`, e o `metadata` tem `sources`. Um commit usa o mesmo formato, com
`number` nulo, `state` vazio e sem labels nem comentários; coletas antigas,
sem esses campos, são lidas como issues.
