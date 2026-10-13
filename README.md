# DebtRadar — Analisador Multimodal de Dívida Técnica

Projeto da disciplina **Modelagem de Dados não Estruturados** — 1ª etapa
(texto). Tema: **Dívida Técnica em Projetos de Software**.

Integrantes: Luiz Felipe Ramalho Reis e Luy Koji Castelo Branco Nakamura.

Este arquivo ensina a instalar e usar o programa. A documentação completa
está em [docs/](docs/README.md):

| Documento | Conteúdo |
|---|---|
| [Arquitetura](docs/ARQUITETURA.md) | Como o programa está organizado e como os dados passam pelas etapas |
| [Referência dos módulos](docs/REFERENCIA_MODULOS.md) | Todas as funções, classes e constantes |
| [Formato dos dados](docs/FORMATO_DOS_DADOS.md) | Cada campo dos arquivos gerados |
| [Decisões](docs/DECISOES.md) | Por que o projeto é como é |
| [Guia de desenvolvimento](docs/GUIA_DE_DESENVOLVIMENTO.md) | Como alterar e testar |
| [Próximas etapas](docs/PROXIMAS_ETAPAS.md) | Áudio, vídeo e o que se reaproveita |
| [Etapa 1](docs/etapa1/README.md) | Resultados, documentação acadêmica, diário de bordo e apresentação |

## Problema

Dívida técnica são os atalhos e as decisões de curto prazo que
comprometem a qualidade e a manutenção do software. Ela deixa rastros em
texto: issues de refatoração, comentários `TODO` e `FIXME`, discussões
sobre código legado. Esse material é abundante, mas não é estruturado.

A pergunta de pesquisa do projeto é:

> Como os desenvolvedores de software identificam, discutem e priorizam a
> dívida técnica ao longo do ciclo de desenvolvimento, e como esse
> discurso se manifesta em repositórios, comunidades virtuais e mídias
> técnicas?

## Objetivo

Nesta primeira etapa, o objetivo é analisar o discurso sobre dívida
técnica em **textos do GitHub** — issues, pull requests e mensagens de
commit — usando expressões regulares (`re`) e spaCy. Para um repositório
escolhido pelo usuário, o programa informa:

- quantos registros apresentam indícios de dívida técnica;
- de que tipo: código, arquitetura, testes, documentação ou dependências;
- quais termos, entidades e tecnologias são mais frequentes;
- qual o tom (sentimento) das discussões;
- como as ocorrências se distribuem ao longo do tempo;
- quanto das issues e dos pull requests já foi fechado, e em quanto
  tempo, como indício de priorização.

Áudio e vídeo ficam para as etapas seguintes da disciplina.

## Metodologia

O programa executa as etapas abaixo em sequência, e cada uma acrescenta
o seu resultado ao documento da issue. No andamento mostrado na tela são
sete passos, porque a busca de tecnologias roda junto com o spaCy.

```text
GitHub API → coleta → pré-processamento → Regex → spaCy e tecnologias
           → classificação → sentimento → estatísticas → resultado
```

As issues do GitHub são majoritariamente em inglês, por isso o modelo de
linguagem usado é o `en_core_web_sm` e o sentimento é medido com o VADER.

### 1. Coleta (`src/github_collector.py`)

Usa a API REST do GitHub. A opção `--source` escolhe o que coletar:

| Fonte | O que vem | Observação |
|---|---|---|
| `issues` (padrão) | Issues abertas e fechadas, com até 100 comentários cada | |
| `prs` | Pull requests, com os comentários da conversa | A API os devolve na mesma listagem das issues |
| `commits` | Mensagens de commit: a primeira linha é o título | Commits de merge são descartados; uma requisição a cada 100 |
| `all` | As três fontes, até a quantidade pedida de cada uma | |

Os registros vêm dos mais recentes para os mais antigos, e a paginação
segue o cabeçalho `Link` da resposta. Cada registro traz o campo `type`
(`issue`, `pull_request` ou `commit`). Se já existir uma coleta com o
mesmo nome, ela é movida para `data/raw/backup/` antes de ser substituída.
Endereços de e-mail que apareçam nos textos são trocados por um endereço
fictício no momento da coleta.

### 2. Pré-processamento (`src/text_preprocessor.py`)

- descarta registros criados por bots, como relatórios automáticos de
  erro e commits do `dependabot`;
- junta título, corpo e comentários em um único texto;
- remove as assinaturas do Git no fim das mensagens de commit
  (`Co-authored-by:`, `Signed-off-by:`);
- ignora comentários de bots (contas terminadas em `[bot]` ou listadas
  em `KNOWN_BOTS`);
- separa blocos de código em um campo próprio, em vez de descartá-los;
- remove URLs, imagens, comentários e tags HTML, menções a usuários;
- retira a formatação do Markdown (títulos, listas, tabelas, negrito),
  mantendo o conteúdo;
- preserva maiúsculas e minúsculas, referências como `#123` e
  identificadores de código.

### 3. Regex (`src/regex_analyzer.py`)

São 36 padrões, sem diferenciar maiúsculas de minúsculas, em seis
categorias: `general`, `code`, `architecture`, `tests`, `documentation`
e `dependencies`. Cada padrão é de um de dois níveis:

| Nível | Significado | Exemplos |
|---|---|---|
| Explícito | A expressão por si só indica dívida técnica | `TODO`, `tech debt`, `code smell`, `missing tests`, `vulnerable dependency` |
| Contexto | Palavra neutra que só indica o assunto | `architecture`, `documentation`, `unit test`, `cleanup` |

Um documento só é marcado com `technical_debt_detected` quando tem ao
menos um padrão explícito. Nos blocos de código, apenas os marcadores
`TODO`, `FIXME`, `HACK` e `XXX` são procurados.

Dois cuidados com os marcadores, ambos vindos de falsos positivos reais:

- `TODO`, `FIXME` e `XXX` valem sempre em maiúsculas; em minúsculas só
  com a sintaxe de marcador (`todo:`, `todo(fulano)`). No VS Code, "todo"
  em texto comum é o nome de um recurso do produto.
- nenhum marcador é contado quando faz parte de um caminho de arquivo: o
  Kubernetes tem uma pasta `hack/`, e `hack/README.md` não é um `HACK`.

### 4. spaCy (`src/nlp_analyzer.py`)

| Recurso do spaCy | Uso no projeto |
|---|---|
| Tokenização | Divide o texto em tokens; a contagem ignora espaços |
| Lematização | Junta as formas de uma palavra: `remove`, `removed`, `removing` |
| Stopwords | Palavras como `the` e `and` ficam fora das frequências |
| Part-of-speech | Separa substantivos, adjetivos e verbos |
| Noun chunks | Expressões nominais de duas ou mais palavras (`chat input`) |
| NER | Entidades reconhecidas pelo modelo, com o rótulo que ele atribuiu |
| Componente próprio | `blank_line_sentences`: linha em branco encerra a sentença |

Entram nas frequências só tokens alfabéticos, com três letras ou mais,
que não são stopwords nem identificadores de código (`runInTerminal`).

**Atenção ao NER:** o modelo `en_core_web_sm` foi treinado com notícias e
textos da web, não com texto técnico. Os nomes que ele encontra costumam
ser reais, mas os rótulos erram muito (por exemplo, `CSS` como `ORG` e
`Linux` como `GPE`). Entidades numéricas são descartadas, porque o modelo
marca números de issue como `MONEY`.

### 5. Tecnologias (`src/technology_analyzer.py`)

Não vêm do NER. São procuradas com uma lista do próprio projeto (40
nomes) e o `PhraseMatcher` do spaCy, em cinco categorias: `language`,
`framework`, `database`, `tool` e `platform`. Para acrescentar uma
tecnologia, inclua uma linha no dicionário `TECHNOLOGIES`:

```python
"Nome oficial": ["apelido", "outra grafia"],
```

Nomes que também são palavras comuns (`React`, `Spring`, `Windows`) só
valem com a grafia exata; os demais valem com maiúsculas ou minúsculas.
Tokens com barra, como `C++/Rust`, são analisados de novo com as partes
separadas, porque o tokenizador os mantém inteiros.

### 6. Classificação (`src/debt_classifier.py`)

Baseline de regras, sem aprendizado de máquina. Para cada uma das cinco
categorias (código, arquitetura, testes, documentação, dependências) o
documento recebe:

| Resultado | Regra |
|---|---|
| `yes` | Há um padrão explícito da Regex para a categoria, ou o vocabulário do tema aparece 3 vezes ou mais |
| `possible` | O vocabulário do tema aparece 1 ou 2 vezes |
| `no` | Nenhuma evidência |

O vocabulário de cada tema é uma lista de lemas (`TERMS`), contados pelo
spaCy em qualquer flexão. Um documento pode ter várias categorias, e a
evidência de cada decisão fica gravada junto com o resultado.

### 7. Sentimento (`src/sentiment_analyzer.py`)

VADER, um analisador por léxico para inglês. O rótulo é `positive`,
`neutral` ou `negative`, conforme a média do `compound` das sentenças
(limites de ±0,05). Termos técnicos como `shared`, `approval`, `kill` e
o próprio `debt` têm a valência removida (`TECHNICAL_NEUTRAL`), assim
como a palavra `no` isolada ("no tests"), que continua invertendo a
palavra seguinte ("no good"). O sentimento descreve o tom do texto; não
mede a dívida técnica.

### 8. Estatísticas (`src/statistics_analyzer.py`)

Frequência de termos, expressões, tecnologias, entidades, padrões Regex
e categorias de dívida; sentimento geral e por categoria; contagens por
fonte e por mês de criação. Cada item de frequência traz o total de
ocorrências (`count`) e em quantos documentos aparece (`documents`).

**Resolução.** Para issues e pull requests, o resumo compara os registros
com e sem dívida identificada: quantos foram fechados e a mediana de dias
até o fechamento. É um indício de priorização, não uma medida: nos dados
coletados o resultado muda de um repositório para outro.

## Arquitetura

O `main.py` cuida apenas da interface. O `pipeline.py` chama, em ordem,
um módulo por etapa; cada módulo tem uma responsabilidade e pode ser
testado sozinho. O `report.py` lê somente o resumo consolidado.

```text
projeto/
├── main.py            # ponto de entrada: opções, perguntas e chamada do pipeline
├── requirements.txt   # dependências
├── .env.example       # modelo do arquivo de configuração
├── src/
│   ├── config.py               # caminhos do projeto e leitura validada do .env
│   ├── storage.py              # leitura e gravação dos arquivos JSON
│   ├── pipeline.py             # executa as sete etapas em sequência
│   ├── github_collector.py     # coleta de issues e comentários pela API do GitHub
│   ├── text_preprocessor.py    # limpeza do Markdown e separação do código
│   ├── regex_analyzer.py       # padrões de dívida técnica com expressões regulares
│   ├── nlp_analyzer.py         # tokens, lemas, classes gramaticais e entidades (spaCy)
│   ├── technology_analyzer.py  # tecnologias, com lista própria do projeto
│   ├── debt_classifier.py      # tipo de dívida, por regras
│   ├── sentiment_analyzer.py   # sentimento com VADER
│   ├── statistics_analyzer.py  # frequências, sentimento e evolução temporal
│   └── report.py               # apresentação do resultado no terminal
├── tests/             # testes automatizados (pytest)
├── tools/             # geradores de documentação
├── docs/              # documentação geral e de cada etapa
└── data/
    ├── raw/           # coletas, como vieram da API (e backup/ das substituídas)
    ├── processed/     # documentos com todas as análises
    └── results/       # resumo consolidado de cada corpus
```

As pastas de `data/` são criadas automaticamente na primeira execução. O
formato dos três arquivos gravados está descrito em
[docs/FORMATO_DOS_DADOS.md](docs/FORMATO_DOS_DADOS.md), e cada função, em
[docs/REFERENCIA_MODULOS.md](docs/REFERENCIA_MODULOS.md).

## Instalação

Testado no macOS com Python 3.14.7 e 3.9.6. As versões intermediárias
não foram testadas.

```bash
python3 -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install --only-binary=:all: -r requirements.txt
python -m spacy download en_core_web_sm
```

A opção `--only-binary=:all:` faz o pip usar só pacotes prontos. Sem ela,
em versões antigas do Python o pip tenta compilar o spaCy e falha.

## Configuração

Copie o arquivo de exemplo e preencha os valores:

```bash
cp .env.example .env
```

| Variável | Obrigatória | Padrão | Descrição |
|---|---|---|---|
| `GITHUB_TOKEN` | Não | vazio | Token pessoal do GitHub. Sem ele a API permite só 60 requisições por hora. |
| `SPACY_MODEL` | Não | `en_core_web_sm` | Modelo do spaCy usado na análise. |
| `DEFAULT_ISSUES` | Não | `100` | Quantidade de issues sugerida quando o programa pergunta (inteiro maior que zero). |

O programa funciona sem o arquivo `.env`, usando os valores padrão.
O `.env` contém o token e não deve ser compartilhado; ele já está no
`.gitignore`. O token é enviado apenas no cabeçalho das requisições à
API do GitHub e nunca é impresso nem gravado nos arquivos de dados.

**Como criar o token.** No GitHub: *Settings → Developer settings →
Personal access tokens → Fine-grained tokens → Generate new token*. Em
*Repository access* escolha *Public repositories*; nenhuma permissão
adicional é necessária para ler issues públicas. Copie o valor gerado
para a linha `GITHUB_TOKEN=` do `.env`. Sem token, uma coleta de 50
issues pode consumir quase toda a cota de uma hora.

## Execução

```bash
python main.py
```

O programa pergunta o que coletar:

```text
Owner: microsoft
Repository: vscode
Quantidade [100]: 30
Label (opcional; Enter = sem label): debt
```

Depois executa o pipeline, mostrando o andamento, e apresenta o resultado
em sete blocos: coleta, dívida técnica, Regex, spaCy, tecnologias,
sentimento e tempo. Trecho de uma execução real:

```text
[1/7] Carregando coleta salva... 30 issues
      Arquivo: microsoft_vscode_debt_issues.json
[2/7] Pré-processando...         30 documentos
[3/7] Executando Regex...        51 ocorrências de padrões
[4/7] Executando spaCy...        14830 tokens, 19 tecnologias distintas
[5/7] Classificando dívida...    16 documentos com dívida
[6/7] Analisando sentimento...   1015 sentenças pontuadas
[7/7] Gerando resultados...      resumo consolidado

── DÍVIDA TÉCNICA ──────────────────────────────────────────────────
  Total identificado    16 de 30 (53%)
    com marcador explícito (Regex)   11
    com tipo confirmado (regras)     13

  Categoria      Sim  Possível
  Código           7        11  ████████████████████████
  Testes           6         8  █████████████████████
  Arquitetura      3         7  ██████████
  Dependências     1         0  ███
  Documentação     0         2

── REGEX  (ocorrências/documentos) ─────────────────────────────────
  Marcadores     TODO 1/1   FIXME 0/0   HACK 0/0   XXX 0/0
  Expressões     technical debt 0/0   debt 9/8   refactor 1/1
                 legacy code 0/0   workaround 0/0
```

Os valores também podem ser passados pela linha de comando:

```bash
python main.py --owner microsoft --repo vscode --limit 30 --label debt
python main.py --owner psf --repo requests --limit 8 --source all
python main.py --file data/raw/microsoft_vscode_debt_issues.json
python main.py --text "Authentication needs refactoring and has no tests."
python main.py --check
```

| Opção | Descrição |
|---|---|
| `--owner` | Dono ou organização do repositório |
| `--repo` | Nome do repositório |
| `--limit` | Quantidade de registros de cada fonte |
| `--label` | Coleta só issues e pull requests com essa label (ex.: `debt`, `kind/cleanup`) |
| `--source` | O que coletar: `issues` (padrão), `prs`, `commits` ou `all` |
| `--file` | Analisa uma coleta já salva em `data/raw/`, sem acessar a API |
| `--text` | Analisa só o texto informado e mostra o resultado de cada etapa |
| `--check` | Só verifica a configuração e se o spaCy e o modelo estão instalados |

A opção `--file` refaz toda a análise sem rede e sem gastar a cota da
API; é a forma indicada para demonstrar o programa.

A opção `--text` serve para ver cada técnica funcionando em uma frase:

```text
── 1. TEXTO LIMPO ──────────────────────────────────────────────────
  Authentication needs refactoring and has no tests.

── 2. REGEX ────────────────────────────────────────────────────────
  refactor              general        explícito  "refactoring"
  missing_tests         tests          explícito  "no tests"

── 3. SPACY  (token, lema, classe gramatical) ──────────────────────
  token             lema              classe  stopword  conta?
  Authentication    authentication    NOUN    não       sim
  needs             need              VERB    não       sim
  refactoring       refactore         VERB    não       sim
  and               and               CCONJ   sim       não
  has               have              VERB    sim       não
  no                no                DET     sim       não
  tests             test              NOUN    não       sim
  .                 .                 PUNCT   não       não
  Tecnologias    nenhum

── 4. CLASSIFICAÇÃO  (regras) ──────────────────────────────────────
  Código        SIM       refactor
  Arquitetura   possível  refactor
  Testes        SIM       missing_tests, test×1
  Documentação  não
  Dependências  não

── 5. SENTIMENTO ───────────────────────────────────────────────────
  neutro (compound +0.000, média de 1 sentença)
```

**Limite da API:** cada coleta gasta uma requisição a cada 100 itens
listados, mais uma por issue que tenha comentários. Sem `GITHUB_TOKEN` o
limite é de 60 requisições por hora; com token, 5000. Se o limite acabar
durante a busca dos comentários, as issues já coletadas são mantidas e o
programa avisa que os comentários ficaram incompletos.

## Tecnologias

| Tecnologia | Versão testada | Papel no projeto |
|---|---|---|
| Python | 3.14.7 e 3.9.6 | Linguagem do projeto |
| `re` (biblioteca padrão) | — | Limpeza do Markdown e padrões de dívida técnica |
| spaCy | 3.8.16 | Tokenização, lemas, classes gramaticais, NER e busca de tecnologias |
| `en_core_web_sm` | 3.8.0 | Modelo de inglês do spaCy |
| requests | 2.34.2 | Acesso à API REST do GitHub |
| vaderSentiment | 3.3.2 | Análise de sentimento por léxico |
| python-dotenv | 1.2.4 | Leitura do arquivo `.env` |
| pytest | 9.1.1 | Testes automatizados |

## Testes

```bash
python -m pytest
```

São 119 testes em `tests/`, que rodam em menos de um segundo e não
acessam a rede: a coleta é testada com respostas simuladas da API e o
pipeline com uma coleta pequena escrita para o teste. Cada defeito
encontrado nos dados reais durante o desenvolvimento tem um teste que
impede a sua volta.

## Validação com dados reais

Não há gabarito do tipo de dívida, mas os rótulos dados pelos
mantenedores permitem medir a detecção. "Dívida identificada" é ter um
marcador explícito da Regex ou ao menos um tipo confirmado pelas regras.

| Corpus | Registros analisados | Dívida identificada |
|---|---|---|
| `microsoft/vscode`, issues com label `debt` | 30 | 16 |
| `kubernetes/kubernetes`, issues com label `kind/cleanup` | 15 | 8 |
| `pandas-dev/pandas`, issues com label `Refactor` | 12 | 5 |
| `microsoft/vscode`, pull requests com label `debt` | 15 | 3 |
| `microsoft/vscode`, issues com label `bug` (controle) | 9 | 1 |
| `pallets/flask`, issues sem label | 15 | 4 |
| `microsoft/vscode`, 100 commits mais recentes | 97 | 16 |

Das 57 issues que os mantenedores rotularam como dívida, limpeza ou
refatoração, o programa identifica 29 (51%); no corpus de controle, 1 em
9. Nos pull requests com a mesma label o resultado é pior, 3 de 15: os
textos são curtos e dizem "remove deprecated setting", sem vocabulário de
dívida. As amostras são pequenas e de poucos repositórios.

## Limitações

- **Vocabulário explícito é raro.** Em 30 issues que os mantenedores do
  VS Code rotularam como `debt`, só 11 têm um padrão explícito.
- **Classificação por regras.** Repetir um termo ambíguo como `test` três
  vezes basta para confirmar a categoria. Exigir dois termos diferentes
  foi testado e descartado: eliminava mais acertos do que erros.
- **NER impreciso em texto técnico.** Os rótulos das entidades não são
  confiáveis; as tecnologias vêm da lista do projeto. O modelo
  `en_core_web_md` foi testado e não melhora o resultado.
- **Lematização de nomes próprios.** O spaCy reduz `pandas` a `panda`,
  como se fosse um plural.
- **Sentimento por léxico.** O VADER não entende contexto técnico além
  dos termos neutralizados.
- **A linha do tempo descreve a amostra coletada**, não o histórico do
  repositório.
- **Bots sem o sufixo `[bot]`** só são filtrados se estiverem em
  `KNOWN_BOTS`.
- **Coleta com token não foi exercitada.** O desenvolvimento foi feito
  sem `GITHUB_TOKEN`; o envio do token está coberto por teste, mas não
  houve uma coleta autenticada real.
- **Textos curtos rendem pouco.** Pull requests e commits têm pouco
  vocabulário; em 15 pull requests rotulados como `debt`, só 3 são
  identificados.
- **A priorização é só um indício.** O fechamento de issues e pull
  requests não diz por que algo foi fechado, e o padrão muda entre
  repositórios.
- **Fontes da proposta que ficaram de fora.** Arquivos de documentação
  dos repositórios, o BugRepo e a raspagem de páginas com BeautifulSoup
  não foram implementados; a coleta usa só a API.
- **Só texto e só inglês.**

## Formato dos arquivos

Cada execução grava três arquivos com o mesmo nome-base,
`<owner>_<repo>[_<label>]_<fonte>`:

| Pasta | Conteúdo |
|---|---|
| `data/raw/` | A coleta, como veio da API |
| `data/processed/` | Um documento por registro, com todas as análises |
| `data/results/` | O resumo consolidado do corpus (`..._summary.json`) |

Repetir a mesma coleta substitui os arquivos; a coleta anterior é
guardada em `data/raw/backup/`. Todos os campos, com exemplos reais,
estão em [docs/FORMATO_DOS_DADOS.md](docs/FORMATO_DOS_DADOS.md).
