# DebtRadar — Documentação Acadêmica da 1ª Etapa

Este documento explica por que cada técnica foi usada e como ela funciona
no programa. Tudo o que está descrito aqui corresponde ao código em
`src/`; os números vêm de execuções reais sobre issues do GitHub.

## Regex — por que foi utilizada?

As expressões regulares aparecem em três pontos do programa.

**1. Limpeza do texto** (`text_preprocessor.py`, 22 expressões). Issues
do GitHub são escritas em Markdown. Blocos de código, links, imagens,
tags HTML e marcas de formatação têm uma forma fixa, que uma Regex
descreve bem. Exemplo: `` (`{3,}|~{3,})[^\n]*\n(.*?)(?:\1|\Z) `` retira
um bloco de código, e a referência retroativa `\1` exige que ele feche
com a mesma cerca que abriu.

**2. Detecção de dívida técnica** (`regex_analyzer.py`, 36 padrões).
Parte da dívida técnica é declarada com palavras de forma previsível:
`TODO`, `FIXME`, "technical debt", "code smell", "no tests". São
22 padrões explícitos, que por si só indicam dívida, e 14 de contexto,
que só indicam o assunto.

**3. Divisão em sentenças** para o sentimento (`sentiment_analyzer.py`).

Recursos de Regex usados e para quê:

| Recurso | Exemplo no código | Para que serve |
|---|---|---|
| `\b` | `\bwork[\s-]?arounds?\b` | Não casar dentro de outra palavra |
| `(?:a\|b)` e `?` | `\btech(?:nical)?[\s-]+debts?\b` | Cobrir "tech debt", "technical-debt" e o plural |
| Lookahead negativo | `(?![\w/]\|\.\w)` | Ignorar `hack/README.md` |
| Lookbehind negativo | `(?<![\w/.])` | Ignorar `docs/TODO.md` |
| Lookahead positivo | `todo(?=\s*[:(])` | Aceitar "todo:" em minúsculas |
| Flag local | `(?-i:TODO)` | Exigir maiúsculas só nesse trecho |
| Referência retroativa | `\1` | Fechar o bloco com a mesma cerca |

**O que a Regex não faz.** Ela só encontra o que foi escrito de forma
literal. Em 30 issues que os mantenedores do VS Code rotularam como
`debt`, apenas 11 têm um padrão explícito. Por isso ela não é a única
fonte de evidência.

## spaCy — por que foi utilizado?

O spaCy dá ao programa o que a Regex não tem: conhecimento da língua.

| Recurso | Uso no código (`nlp_analyzer.py`) | Exemplo real |
|---|---|---|
| Tokenização | `nlp.pipe(textos)` | "JavaScript" é um token; "Java" não é encontrado dentro dele |
| Lematização | `token.lemma_` | remove, removed, removing, removes → `remove` |
| Stopwords | `token.is_stop` | "the", "and" ficam fora das frequências |
| Part-of-speech | `token.pos_` | Separa substantivos, adjetivos e verbos |
| Noun chunks | `doc.noun_chunks` | "agent host", "chat input" |
| NER | `doc.ents` | Entidades com o rótulo dado pelo modelo |
| Componente próprio | `blank_line_sentences` | Linha em branco encerra a sentença |
| `PhraseMatcher` | `technology_analyzer.py` | Busca das 40 tecnologias da lista do projeto |

A diferença para a Regex aparece nos dados: o padrão
`duplicat(?:ed|ion)` encontrou 8 ocorrências, porque só casa as
terminações escritas; o lema `duplicate` do spaCy reuniu 12.

**NER e tecnologias são coisas separadas.** O modelo `en_core_web_sm`
foi treinado com notícias e textos da web. Em issues ele rotula `Linux`
como lugar (`GPE`) e `Claude` como pessoa. O programa não usa o NER para
identificar tecnologias: usa um dicionário próprio (`TECHNOLOGIES`) e o
`PhraseMatcher`, que compara tokens. O resultado mostra as duas listas
separadas e identificadas.

## GitHub API — por que foi escolhida?

- **É a fonte definida na proposta** do projeto e está entre as fontes
  sugeridas pela disciplina para a primeira etapa.
- **Os dados vêm estruturados.** Cada issue chega em JSON com título,
  corpo, autor, estado, labels, datas e comentários. O texto vem do
  título, do corpo e dos comentários; as datas alimentam a análise
  temporal; e o autor permite descartar textos de bots. Estado e labels
  ficam guardados junto de cada documento.
- **As labels funcionam como referência.** Issues rotuladas pelos
  próprios mantenedores (`debt`, `kind/cleanup`, `Refactor`) permitiram
  medir quanto da dívida o programa encontra.
- **A API informa os seus limites.** Os cabeçalhos da resposta trazem a
  cota restante e o endereço da próxima página, usados na paginação e no
  tratamento do limite de requisições.

A coleta usa três endpoints, escolhidos pela opção `--source`:

| Fonte | Endpoint | O que é analisado |
|---|---|---|
| Issues | `GET /repos/{owner}/{repo}/issues` | Título, corpo e comentários |
| Pull requests | A mesma listagem; a API marca cada um com o campo `pull_request` | Título, corpo e comentários da conversa |
| Commits | `GET /repos/{owner}/{repo}/commits` | A mensagem: primeira linha como título, o resto como corpo |

Os comentários vêm de `.../issues/{número}/comments`. A proposta do
projeto cita issues, pull requests, commits e documentação; as três
primeiras fontes estão implementadas. Arquivos de documentação, o
BugRepo e a raspagem de páginas com BeautifulSoup ficaram de fora: as
regras da etapa aceitam web scraping ou Web API, e o programa usa a API.

## Classificação — como funciona?

É um **baseline de regras**, sem aprendizado de máquina e sem
treinamento (`debt_classifier.py`). Para cada uma das cinco categorias
(código, arquitetura, testes, documentação, dependências), o programa
junta dois tipos de evidência:

- **forte:** um padrão explícito da Regex ligado à categoria, como
  "no tests" para testes;
- **fraca:** o vocabulário do tema, contado pelos lemas do spaCy, como
  `test` e `coverage`.

| Resultado | Regra |
|---|---|
| `yes` | Há evidência forte, ou a evidência fraca aparece 3 vezes ou mais |
| `possible` | A evidência fraca aparece 1 ou 2 vezes |
| `no` | Nenhuma evidência |

Um documento pode ter várias categorias. Para a frase
"Authentication needs refactoring and has no tests." o resultado é:
código `yes` (padrão "refactor"), arquitetura `possible` (refatorar pode
envolver o desenho), testes `yes` (padrão "no tests"), documentação e
dependências `no`.

A evidência de cada decisão fica gravada junto com o resultado, o que
permite conferir por que uma issue recebeu cada categoria.

**Avaliação.** Não há gabarito do tipo de dívida. Usando as labels dos
mantenedores como referência, o programa identifica dívida em 29 das 57
issues rotuladas como dívida, limpeza ou refatoração (51%), e em 1 das 9
issues de um corpus de controle com a label `bug`. Em pull requests com
a label `debt` o resultado cai para 3 de 15: os textos são curtos, como
"remove deprecated setting", e trazem pouco vocabulário.

**Priorização.** A pergunta de pesquisa fala em como a dívida é
priorizada. O programa não mede prioridade; ele mostra um indício
(`statistics_analyzer.resolution`): quantas issues e pull requests com e
sem dívida já foram fechados e a mediana de dias até o fechamento. Nas 30
issues `debt` do VS Code, as 7 fechadas com dívida identificada levaram
uma mediana de 1,3 dia, contra 4,0 dias das 7 fechadas sem dívida
identificada. No pandas o padrão se inverte (666 contra 108 dias),
portanto o indício não permite uma conclusão geral.

## Sentimento — qual é o seu papel?

O sentimento descreve o **tom** com que a dívida é discutida. É uma
característica complementar do discurso: não mede a dívida técnica nem
entra na classificação.

O programa usa o VADER (`sentiment_analyzer.py`), um analisador por
léxico para inglês, idioma predominante das issues. Cada palavra tem uma
valência e a pontuação final (`compound`) vai de -1 a +1. O rótulo é
`positive` a partir de +0,05, `negative` até -0,05 e `neutral` entre os
dois.

Duas adaptações foram necessárias, ambas observadas nos dados:

- **Média por sentença.** Aplicado ao documento inteiro, o VADER
  saturava: 11 de 30 documentos ficavam acima de 0,9 em módulo.
- **Termos técnicos neutros.** "shared" somava +95 pontos em 68
  ocorrências, embora "shared state" não seja um elogio. São 37 termos
  com a valência removida, entre eles "debt", além de "no" isolado.

Nas 30 issues `debt` do VS Code, o resultado é 8 positivas, 15 neutras e
7 negativas: o tom predominante é neutro.

## Limitações — o que a primeira versão ainda não faz?

- **Não reconhece dívida descrita sem o vocabulário esperado.** Issues
  como "Remove the AI Usage Statistics widget" não recebem nenhuma
  categoria.
- **Não mede a própria acurácia por categoria.** A avaliação usa labels
  de repositório, que dizem se há dívida, mas não de que tipo.
- **Não distingue assunto de problema.** Citar `test` três vezes
  confirma a categoria de testes, mesmo que a issue trate de outra coisa.
- **Não reconhece entidades técnicas de forma confiável.** Os rótulos do
  NER erram em texto de software, e o lematizador reduz "pandas" a
  "panda".
- **Não entende ironia nem contexto no sentimento.** O VADER soma
  valências de palavras.
- **Não analisa a documentação dos repositórios, o BugRepo nem páginas
  raspadas,** apenas issues, pull requests e commits obtidos pela API, e
  apenas em inglês.
- **Não mede a priorização.** O fechamento de issues é só um indício, e
  o padrão muda de um repositório para outro.
- **Não representa o histórico do repositório.** A análise temporal
  descreve só as issues coletadas, que são as mais recentes.
- **Não trata áudio nem vídeo,** previstos para as etapas seguintes.

## Referências — de onde vêm os conceitos e as ferramentas?

**Dívida técnica**

- CUNNINGHAM, Ward. The WyCash Portfolio Management System. *OOPSLA '92
  Experience Report*, 1992. Origem da metáfora da dívida: entregar código
  imaturo é como tomar um empréstimo, e os juros são o retrabalho.
- KRUCHTEN, Philippe; NORD, Robert L.; OZKAYA, Ipek. Technical Debt: From
  Metaphor to Theory and Practice. *IEEE Software*, v. 29, n. 6, 2012.
- POTDAR, Aniket; SHIHAB, Emad. An Exploratory Study on Self-Admitted
  Technical Debt. *IEEE International Conference on Software Maintenance
  and Evolution (ICSME)*, 2014. Estuda a dívida que os próprios
  desenvolvedores declaram em comentários como `TODO`, `FIXME` e `HACK`,
  que é o que os marcadores da Regex procuram.

**Ferramentas**

- HUTTO, C. J.; GILBERT, Eric. VADER: A Parsimonious Rule-based Model for
  Sentiment Analysis of Social Media Text. *International AAAI Conference
  on Weblogs and Social Media (ICWSM)*, 2014. Código e léxico em
  <https://github.com/cjhutto/vaderSentiment>.
- spaCy: documentação em <https://spacy.io> e curso gratuito em
  <https://course.spacy.io>. Modelo `en_core_web_sm` em
  <https://spacy.io/models/en>.
- Módulo `re` do Python: <https://docs.python.org/3/library/re.html>.
- GitHub REST API: <https://docs.github.com/rest>.

O VADER não foi apresentado em aula; o artigo de Hutto e Gilbert e o
repositório `cjhutto/vaderSentiment` são o ponto de partida para
aprendê-lo.
