# Referência dos Módulos

Um capítulo por arquivo de código, na ordem em que os dados passam por
eles. Para cada módulo: o papel, do que ele depende, onde está testado,
as constantes que podem ser ajustadas e todas as funções e classes.

Os nomes, as assinaturas e os números de linha foram extraídos do código;
as descrições das funções são as primeiras linhas das docstrings. Funções
cujo nome começa com `_` são internas ao módulo.

Para a visão de conjunto, veja [ARQUITETURA.md](ARQUITETURA.md). Para os
campos dos dados que essas funções trocam, veja
[FORMATO_DOS_DADOS.md](FORMATO_DOS_DADOS.md).

## Índice

| Módulo | Linhas | Papel em uma frase |
|---|---|---|
| [`main.py`](#mainpy) | 180 | Interface de linha de comando |
| [`src/pipeline.py`](#srcpipelinepy) | 237 | Executa as etapas em ordem |
| [`src/config.py`](#srcconfigpy) | 80 | Caminhos e leitura do `.env` |
| [`src/storage.py`](#srcstoragepy) | 12 | JSON em disco |
| [`src/github_collector.py`](#srcgithub_collectorpy) | 334 | Coleta pela API do GitHub |
| [`src/text_preprocessor.py`](#srctext_preprocessorpy) | 150 | Limpeza do Markdown |
| [`src/regex_analyzer.py`](#srcregex_analyzerpy) | 179 | Padrões de dívida com Regex |
| [`src/nlp_analyzer.py`](#srcnlp_analyzerpy) | 146 | Análise linguística com spaCy |
| [`src/technology_analyzer.py`](#srctechnology_analyzerpy) | 123 | Tecnologias, por lista própria |
| [`src/debt_classifier.py`](#srcdebt_classifierpy) | 95 | Tipo de dívida, por regras |
| [`src/sentiment_analyzer.py`](#srcsentiment_analyzerpy) | 86 | Sentimento com VADER |
| [`src/statistics_analyzer.py`](#srcstatistics_analyzerpy) | 230 | Resumo consolidado |
| [`src/report.py`](#srcreportpy) | 279 | Relatório no terminal |

## `main.py`

180 linhas. Ponto de entrada. Lê as opções da linha de comando, faz as perguntas do modo interativo, chama o pipeline e transforma os erros em mensagens. Não contém nenhuma regra de análise.

Três caminhos: `--check` chama `run_check`; `--text` chama `run_explanation`; o restante chama `run_pipeline`, que coleta (ou lê um arquivo com `--file`), analisa, grava e mostra o relatório.

- **Importa do projeto:** `config`, `github_collector`, `pipeline`, `report`
- **Testes:** Não há teste automatizado da interface; as opções foram exercitadas manualmente.

### Funções e classes

| Nome | Linha | O que faz |
|---|---|---|
| `check_spacy_model(model_name)` | 28 | Tenta carregar o modelo do spaCy. Devolve (ok, mensagem). |
| `run_check(settings)` | 44 | Mostra a configuração carregada e verifica se o ambiente está pronto. |
| `ask(prompt)` | 69 | Lê uma resposta do usuário; sem terminal interativo, explica o que fazer. |
| `ask_parameters(args, settings)` | 79 | Completa, perguntando ao usuário, o que não veio pela linha de comando. |
| `run_pipeline(args, settings)` | 105 | Executa o pipeline completo e mostra o resultado. |
| `run_explanation(text, settings)` | 134 | Mostra o que cada etapa faz com um único texto. |
| `build_parser()` | 145 | Define as opções da linha de comando. |
| `main()` | 162 | Carrega a configuração, cria as pastas e escolhe o caminho a seguir. Devolve o código de saída. |

## `src/pipeline.py`

237 linhas. Orquestra as etapas. Cada etapa é uma função curta que chama o módulo responsável, grava o resultado em uma chave do documento e mostra uma linha de andamento.

`collect` e `load` são as duas formas de obter a coleta (passo 1). `analyze` executa os passos 2 a 7. `explain` reaproveita os mesmos módulos para um único texto, sem gravar nada.

- **Importa do projeto:** `config`, `debt_classifier`, `github_collector`, `nlp_analyzer`, `regex_analyzer`, `report`, `sentiment_analyzer`, `statistics_analyzer`, `storage`, `technology_analyzer`, `text_preprocessor`
- **Testes:** `tests/test_pipeline.py`

### Constantes

| Nome | Linha | Significado |
|---|---|---|
| `TOTAL_STEPS` | 24 | Número de passos mostrados no andamento. |
| `ISSUE_FIELDS` | 27 | Campos que todo registro de uma coleta precisa ter. |
| `METADATA_FIELDS` | 29 | Campos obrigatórios no `metadata` de uma coleta. |

### Funções e classes

| Nome | Linha | O que faz |
|---|---|---|
| `class PipelineError` | 32 | Erro que interrompe o pipeline, com mensagem pronta para o usuário. |
| `start_step(number, message)` | 36 | Mostra o início de uma etapa; o resultado sai na mesma linha. |
| `end_step(detail)` | 41 | Mostra o resultado de uma etapa. |
| `describe_records(records)` | 45 | Resume uma coleta por tipo: "30 issues, 20 pull requests, 14 comentários". |
| `show_records(records)` | 59 | Fecha a etapa 1; o detalhe por tipo vai para outra linha se for longo. |
| `load_spacy(model_name)` | 69 | Carrega o pipeline do spaCy e o buscador de tecnologias. |
| `collect(owner, repo, limit, label, sources, settings)` | 85 | Coleta os registros pela API. Devolve (coleta, arquivo salvo). |
| `load(path)` | 105 | Lê uma coleta já salva, sem usar a rede. Devolve (coleta, arquivo). |
| `preprocess(collection)` | 131 | Etapa 2: limpa os textos. Devolve (documentos, registros de bots ignorados). |
| `apply_regex(documents)` | 150 | Etapa 3: procura os padrões de dívida técnica. |
| `apply_spacy(documents, model_name)` | 159 | Etapa 4: análise linguística e tecnologias. Devolve o nome do modelo. |
| `classify(documents)` | 175 | Etapa 5: tipo de dívida de cada documento. |
| `measure_sentiment(documents)` | 184 | Etapa 6: sentimento de cada documento. |
| `analyze(collection, settings)` | 194 | Executa as etapas 2 a 7. Devolve (documentos analisados, resumo). |
| `save_results(documents, summary, raw_path)` | 211 | Grava os documentos analisados e o resumo. Devolve os dois caminhos. |
| `explain(text, settings)` | 222 | Passa um único texto por todas as análises e devolve cada resultado. |

## `src/config.py`

80 linhas. Reúne os caminhos do projeto e a leitura validada do arquivo `.env`. É o único lugar que lê variáveis de ambiente; os outros módulos recebem um objeto `Config` pronto.

Variáveis aceitas no `.env`: `GITHUB_TOKEN`, `SPACY_MODEL` e `DEFAULT_ISSUES`. Variáveis já definidas no terminal têm prioridade.

- **Importa do projeto:** nada
- **Testes:** `tests/test_pipeline.py` (validação e proteção do token)

### Constantes

| Nome | Linha | Significado |
|---|---|---|
| `BASE_DIR` | 14 | Pasta do projeto. |
| `ENV_FILE` | 15 | Caminho do arquivo `.env`. |
| `DATA_DIR` | 16 | Pasta `data/`. |
| `RAW_DIR` | 17 | Coletas, como vieram da API. |
| `PROCESSED_DIR` | 18 | Documentos com todas as análises. |
| `RESULTS_DIR` | 19 | Resumos consolidados. |
| `GITHUB_API_URL` | 22 | Endereço da API. O coletor só segue páginas que comecem por ele. |
| `REQUEST_TIMEOUT` | 23 | Segundos de espera por resposta da API. |
| `DEFAULT_SPACY_MODEL` | 26 | Modelo usado quando `SPACY_MODEL` não está no `.env`. |
| `DEFAULT_ISSUES` | 27 | Quantidade sugerida quando o programa pergunta. |

### Funções e classes

| Nome | Linha | O que faz |
|---|---|---|
| `class ConfigError` | 30 | Erro de configuração com mensagem pronta para mostrar ao usuário. |
| `class Config` | 35 | Valores de configuração usados pelo programa. |
| `Config.has_github_token()` | 44 | Propriedade: verdadeiro se há token configurado. |
| `_read_positive_int(name, default)` | 48 | Lê uma variável de ambiente que deve ser um inteiro maior que zero. |
| `load_config()` | 64 | Carrega o .env (se existir) e devolve a configuração validada. |
| `ensure_directories()` | 77 | Cria as pastas de dados caso ainda não existam. |

## `src/storage.py`

12 linhas. Leitura e gravação de JSON em UTF-8. Existe para que o formato de gravação (indentação, acentos sem escape) seja o mesmo em todo o projeto.

- **Importa do projeto:** nada
- **Testes:** Indiretamente, em `tests/test_pipeline.py` e `tests/test_github_collector.py`

### Funções e classes

| Nome | Linha | O que faz |
|---|---|---|
| `load_json(path)` | 5 | Lê um arquivo JSON em UTF-8. |
| `save_json(data, path)` | 10 | Grava um arquivo JSON em UTF-8, indentado e sem escapar acentos. |

## `src/github_collector.py`

334 linhas. Fala com a API REST do GitHub. Busca issues, pull requests e commits, junta os comentários e devolve tudo em um formato único de registro.

A paginação segue o cabeçalho `Link`. Os erros de rede e de HTTP viram `GitHubError` com mensagem em português. Se o limite da API acaba durante os comentários, a coleta é mantida e o motivo vai para `metadata.warning`.

- **Importa do projeto:** `config`, `storage`
- **Testes:** `tests/test_github_collector.py`

### Constantes

| Nome | Linha | Significado |
|---|---|---|
| `PER_PAGE` | 19 | Itens por página pedidos à API (o máximo aceito). |
| `MAX_COMMENTS_PER_ISSUE` | 20 | Limite de comentários guardados por issue ou pull request. |
| `SOURCES` | 23 | Fontes aceitas por `--source`, na ordem em que aparecem no resultado. |
| `EMAIL` | 28 | Regex de endereço de e-mail; não casa com `git@github.com:org/repo` nem `react@18.2.0`. |
| `MASKED_EMAIL` | 29 | Endereço fictício que substitui os e-mails coletados. |

### Funções e classes

| Nome | Linha | O que faz |
|---|---|---|
| `class GitHubError` | 32 | Erro na coleta com mensagem pronta para mostrar ao usuário. |
| `class RateLimitError` | 36 | A API recusou a requisição porque o limite foi atingido. |
| `mask_emails(text)` | 40 | Troca endereços de e-mail por um endereço fictício. |
| `normalize_issue(raw)` | 50 | Converte uma issue da API para o formato do DebtRadar. |
| `normalize_commit(raw)` | 77 | Converte um commit da API para o mesmo formato das issues. |
| `normalize_comment(raw)` | 108 | Converte um comentário da API para o formato do DebtRadar. |
| `_login(user)` | 118 | Nome do usuário; contas apagadas chegam como null na API. |
| `_label_name(label)` | 123 | A API pode devolver a label como objeto ou como texto simples. |
| `class GitHubCollector` | 130 | Cliente simples da API do GitHub para coletar issues e comentários. |
| `GitHubCollector.__init__(token='', timeout=config.REQUEST_TIMEOUT)` | 133 | Cria a sessão HTTP com os cabeçalhos da API; o token entra só se existir. |
| `GitHubCollector.collect(owner, repo, limit, label=None, sources=('issues',))` | 147 | Coleta até 'limit' registros de cada fonte pedida em owner/repo. |
| `GitHubCollector._fetch_issues(owner, repo, limit, label, sources)` | 177 | Busca issues e pull requests, que a API devolve na mesma listagem. |
| `GitHubCollector._fetch_commits(owner, repo, limit)` | 197 | Busca os commits, descartando os de merge. |
| `GitHubCollector._add_comments(owner, repo, issues)` | 208 | Preenche os comentários de cada issue ou pull request. |
| `GitHubCollector._fetch_comments(url)` | 224 | Busca os comentários de um registro, até o limite. |
| `GitHubCollector._paginate(url, params)` | 232 | Gera os itens de todas as páginas, uma requisição por página. |
| `GitHubCollector._get(url, params)` | 255 | Faz uma requisição e converte timeout e falha de conexão em `GitHubError`. |
| `GitHubCollector._update_rate_limit(response)` | 268 | Guarda a cota restante e o horário de renovação, lidos dos cabeçalhos. |
| `GitHubCollector._check_status(response)` | 276 | Transforma respostas de erro em exceções com mensagens claras. |
| `GitHubCollector._rate_limit_message()` | 298 | Monta a mensagem de limite atingido, com o horário de renovação. |
| `GitHubCollector._repo_url(owner, repo)` | 308 | Monta o endereço do repositório na API. |
| `save_collection(collection, directory=config.RAW_DIR)` | 312 | Salva a coleta em JSON e devolve o caminho do arquivo. |

## `src/text_preprocessor.py`

150 linhas. Limpa o Markdown e transforma um registro coletado em um documento pronto para análise. Separa os blocos de código em um campo próprio e descarta o que foi escrito por bots.

`clean_text` aplica as expressões em cinco passos numerados no código: normalização de caracteres, separação do código, remoção do que não é texto, retirada da formatação e normalização dos espaços. A ordem importa: os blocos de código saem antes de qualquer outra regra tocar no texto.

- **Importa do projeto:** nada
- **Testes:** `tests/test_text_preprocessor.py`

### Constantes

| Nome | Linha | Significado |
|---|---|---|
| `CODE_BLOCK` | 21 | Bloco de código cercado por três ou mais crases ou tis. |
| `HTML_COMMENT` | 23 | Comentário HTML. |
| `IMAGE` | 25 | Imagem em Markdown; é removida inteira. |
| `LINK` | 28 | Link em Markdown; fica só o texto. |
| `URL` | 30 | Endereço solto. |
| `HTML_TAG` | 32 | Tags HTML conhecidas; placeholders como `<name>` sobrevivem. |
| `GIT_TRAILER` | 40 | Assinaturas do Git, como `Co-authored-by:`. |
| `MENTION` | 42 | Menção a usuário (`@fulano`). |
| `INLINE_CODE` | 46 | Código entre crases; fica o conteúdo. |
| `QUOTE` | 47 | Marca de citação no início da linha. |
| `ALERT` | 48 | Marcas `[!NOTE]`, `[!WARNING]` e semelhantes. |
| `HEADING` | 49 | Cerquilhas de título. |
| `BULLET` | 50 | Marcador de item de lista. |
| `CHECKBOX` | 51 | Caixa de seleção de lista de tarefas. |
| `TABLE_RULE` | 54 | Régua horizontal ou linha divisória de tabela. |
| `TABLE_ROW` | 55 | Linha de tabela; as barras viram espaços. |
| `BOLD` | 56 | Negrito. |
| `ITALIC` | 57 | Itálico com asterisco. Sublinhados são preservados, por causa de `snake_case`. |
| `STRIKE` | 58 | Texto riscado. |
| `SPACES` | 61 | Sequência de espaços e tabulações. |
| `SPACES_AROUND_NEWLINE` | 62 | Espaços colados a uma quebra de linha. |
| `BLANK_LINES` | 63 | Três ou mais quebras de linha seguidas. |
| `CURLY_QUOTES` | 65 | Tabela que troca aspas curvas por retas. |
| `KNOWN_BOTS` | 113 | Contas automáticas que não usam o sufixo `[bot]`. Expansível. |

### Funções e classes

| Nome | Linha | O que faz |
|---|---|---|
| `clean_text(text)` | 68 | Limpa um texto em Markdown. Devolve (texto_limpo, codigo). |
| `is_bot(author)` | 116 | Contas automáticas: nome terminado em [bot] ou listado em KNOWN_BOTS. |
| `preprocess_issue(issue)` | 121 | Transforma um registro coletado em um documento pronto para análise. |

## `src/regex_analyzer.py`

179 linhas. Procura os padrões de dívida técnica com expressões regulares. Cada padrão tem nome, categoria e nível (explícito ou de contexto).

Um trecho do texto é contado uma vez só: a lista `PATTERNS` é percorrida em ordem, e um trecho já contado por um padrão não conta para os seguintes. Por isso as expressões específicas vêm antes das genéricas, e `debt` é o último padrão.

- **Importa do projeto:** nada
- **Testes:** `tests/test_regex_analyzer.py`

### Constantes

| Nome | Linha | Significado |
|---|---|---|
| `CATEGORIES` | 35 | As seis categorias dos padrões; inclui `general`. |
| `BEFORE_MARKER` | 41 | Trecho de Regex: o marcador não vem depois de letra, `/` ou `.`. |
| `AFTER_MARKER` | 42 | Trecho de Regex: o marcador não é seguido de letra, `/` ou extensão. |
| `PATTERNS` | 60 | Os 36 padrões, na ordem em que são aplicados. |
| `COMPILED` | 125 | Os padrões compilados com `re.IGNORECASE`. |
| `CODE_MARKERS` | 128 | Padrões procurados dentro dos blocos de código. |
| `CONTEXT_WIDTH` | 130 | Caracteres de contexto guardados antes e depois de cada ocorrência. |

### Funções e classes

| Nome | Linha | O que faz |
|---|---|---|
| `class DebtPattern` | 28 | Um padrão: `name`, `category`, `explicit` e `regex`. |
| `comment_marker(word)` | 45 | Regex de um marcador de comentário de código (TODO, FIXME, XXX). |
| `find_matches(content, source, only=None)` | 133 | Procura os padrões em 'content' e devolve as ocorrências em ordem. |
| `count_by(matches, field)` | 163 | Conta as ocorrências por um campo, ex.: 'pattern' ou 'category'. |
| `analyze_document(text, code='')` | 171 | Analisa um documento e devolve o resultado das Regex. |

## `src/nlp_analyzer.py`

146 linhas. Análise linguística com spaCy: tokens, lemas, stopwords, classes gramaticais, expressões nominais e entidades nomeadas.

Acrescenta ao pipeline do spaCy um componente próprio, `blank_line_sentences`, antes do `parser`. As tecnologias não são tratadas aqui.

- **Importa do projeto:** nada
- **Testes:** `tests/test_nlp_and_classification.py`

### Constantes

| Nome | Linha | Significado |
|---|---|---|
| `RELEVANT_POS` | 21 | Classes gramaticais que entram nas frequências. |
| `EXTRA_STOPWORDS` | 25 | Palavras ignoradas além das stopwords do spaCy. Expansível. |
| `NUMERIC_LABELS` | 29 | Rótulos numéricos do NER, descartados. |
| `MIN_TERM_LENGTH` | 31 | Tamanho mínimo de um termo para entrar nas frequências. |

### Funções e classes

| Nome | Linha | O que faz |
|---|---|---|
| `blank_line_sentences(doc)` | 35 | Componente próprio do pipeline: linha em branco encerra a sentença. |
| `load_pipeline(model_name)` | 47 | Carrega o modelo do spaCy e acrescenta o componente de sentenças. |
| `is_identifier(token)` | 54 | Nomes de código como runInTerminal: letra maiúscula no meio da palavra. |
| `is_relevant(token)` | 60 | Decide se o token entra nas contagens de frequência. |
| `count_lemmas(doc)` | 71 | Frequência dos lemas relevantes, separada por classe gramatical. |
| `count_noun_phrases(doc)` | 80 | Expressões nominais com duas ou mais palavras relevantes. |
| `is_clean_entity(entity)` | 95 | Descarta entidades numéricas e trechos que claramente são código. |
| `extract_entities(doc)` | 106 | Entidades do NER do modelo, com rótulo e número de ocorrências. |
| `analyze_doc(doc)` | 119 | Resume a análise linguística de um documento já processado pelo spaCy. |
| `describe_tokens(doc)` | 133 | Lista, token a token, o que o spaCy extraiu (usado em --text). |

## `src/technology_analyzer.py`

123 linhas. Identifica tecnologias com uma lista do próprio projeto e o `PhraseMatcher` do spaCy. Não usa o NER.

Há dois buscadores: um ignora maiúsculas e minúsculas e outro exige a grafia exata, para nomes que também são palavras comuns. Tokens com barra são analisados de novo com as partes separadas.

- **Importa do projeto:** nada
- **Testes:** `tests/test_nlp_and_classification.py`

### Constantes

| Nome | Linha | Significado |
|---|---|---|
| `TECHNOLOGIES` | 24 | As 40 tecnologias, por categoria, cada uma com os seus apelidos. Expansível. |
| `CASE_SENSITIVE` | 80 | Nomes que também são palavras comuns e exigem a grafia exata. |
| `ALIASES_ONLY` | 84 | Nomes ambíguos demais; só os apelidos são procurados. |

### Funções e classes

| Nome | Linha | O que faz |
|---|---|---|
| `class TechnologyAnalyzer` | 87 | Procura as tecnologias de TECHNOLOGIES em documentos do spaCy. |
| `TechnologyAnalyzer.__init__(nlp)` | 90 | Monta os dois buscadores a partir de `TECHNOLOGIES`. |
| `TechnologyAnalyzer._names_in(doc)` | 106 | Nomes de tecnologia encontrados em um documento, um por ocorrência. |
| `TechnologyAnalyzer.find(doc)` | 113 | Devolve as tecnologias citadas no documento, com a contagem. |

## `src/debt_classifier.py`

95 linhas. Classifica cada documento em cinco tipos de dívida técnica, com regras. Não há aprendizado de máquina.

Junta a evidência forte (padrões explícitos da Regex) com a fraca (lemas do vocabulário de cada tema) e aplica a regra de `decide`. Precisa das chaves `regex` e `nlp` do documento.

- **Importa do projeto:** nada
- **Testes:** `tests/test_nlp_and_classification.py`

### Constantes

| Nome | Linha | Significado |
|---|---|---|
| `CATEGORIES` | 22 | Os cinco tipos de dívida classificados. |
| `YES_THRESHOLD` | 24 | Ocorrências de evidência fraca que bastam para confirmar um tipo. |
| `STRONG_PATTERNS` | 27 | Padrões explícitos da Regex que confirmam cada tipo. |
| `WEAK_PATTERNS` | 39 | Padrões que só sugerem um tipo. |
| `TERMS` | 45 | Vocabulário de cada tipo, em forma de lema. Expansível. |

### Funções e classes

| Nome | Linha | O que faz |
|---|---|---|
| `decide(strong, weak)` | 60 | Aplica a regra de decisão a partir das contagens de evidência. |
| `classify_document(document)` | 69 | Classifica um documento já analisado pela Regex e pelo spaCy. |

## `src/sentiment_analyzer.py`

86 linhas. Mede o sentimento com o VADER, por sentença, depois de retirar do léxico a valência de termos técnicos.

O texto é dividido em sentenças por uma Regex própria, e não pelo spaCy, para o módulo não depender do modelo.

- **Importa do projeto:** nada
- **Testes:** `tests/test_nlp_and_classification.py`

### Constantes

| Nome | Linha | Significado |
|---|---|---|
| `TECHNICAL_NEUTRAL` | 24 | Os 37 termos técnicos sem valência. Expansível. |
| `NEUTRAL_FUNCTION_WORDS` | 42 | Palavras funcionais sem valência própria. |
| `POSITIVE_THRESHOLD` | 45 | A partir deste `compound` o rótulo é positivo. |
| `NEGATIVE_THRESHOLD` | 46 | Até este `compound` o rótulo é negativo. |
| `SENTENCE_END` | 50 | Regex que divide o texto em sentenças. |

### Funções e classes

| Nome | Linha | O que faz |
|---|---|---|
| `split_sentences(text)` | 53 | Divide o texto em sentenças. |
| `label_for(compound)` | 57 | Converte um `compound` em rótulo. |
| `class SentimentAnalyzer` | 65 | Calcula o sentimento de documentos em inglês. |
| `SentimentAnalyzer.__init__()` | 68 | Carrega o VADER e retira do léxico os termos neutros. |
| `SentimentAnalyzer.analyze(text)` | 73 | Devolve o rótulo do documento e os números que o justificam. |

## `src/statistics_analyzer.py`

230 linhas. Soma os resultados de todos os documentos e monta o resumo consolidado: totais, contagens por fonte, classificação, resolução, sentimento, frequências e linha do tempo.

`has_debt` é a definição de "dívida identificada" usada em todo o projeto. `rank` é a função genérica por trás de todas as listas de frequência.

- **Importa do projeto:** `debt_classifier`
- **Testes:** `tests/test_pipeline.py`

### Constantes

| Nome | Linha | Significado |
|---|---|---|
| `TOP_TERMS` | 18 | Tamanho das listas de termos, expressões e entidades. |
| `TYPE_NAMES` | 21 | Tipos de registro, com o nome no singular e no plural. |
| `SENTIMENT_LABELS` | 26 | Rótulos de sentimento, na ordem de exibição. |
| `STATUSES` | 27 | Resultados possíveis da classificação. |

### Funções e classes

| Nome | Linha | O que faz |
|---|---|---|
| `rank(documents, counts_of, limit=None)` | 30 | Soma contagens de todos os documentos e devolve o ranking. |
| `term_frequencies(documents)` | 47 | Lemas mais frequentes por classe gramatical e expressões nominais. |
| `technology_frequencies(documents)` | 63 | Tecnologias mais citadas, com a categoria. |
| `entity_frequencies(documents)` | 70 | Entidades do NER; o mesmo texto com rótulos diferentes conta separado. |
| `pattern_frequencies(documents)` | 79 | Padrões de Regex mais frequentes, com a categoria. |
| `classification_counts(documents)` | 87 | Para cada categoria, quantos documentos ficaram em yes/possible/no. |
| `sentiment_counts(documents)` | 96 | Distribuição dos rótulos de sentimento e média do compound. |
| `has_category(document, category)` | 106 | Verdadeiro se o documento tem o tipo de dívida como `yes`. |
| `has_debt(document)` | 110 | Dívida identificada: marcador explícito da Regex ou algum tipo confirmado. |
| `counts_by_type(documents)` | 116 | Quantos documentos de cada tipo, e em quantos há dívida identificada. |
| `days_to_close(document)` | 127 | Dias entre a criação e o fechamento; None se o registro não foi fechado. |
| `resolution(documents)` | 139 | Fechamento de issues e pull requests, com e sem dívida identificada. |
| `timeline(documents)` | 162 | Contagens por mês de criação da issue (campo created_at da API). |
| `build_summary(documents, metadata)` | 182 | Monta o resultado consolidado do corpus. |

## `src/report.py`

279 linhas. Mostra o resumo consolidado no terminal, em blocos, e a explicação de um texto na opção `--text`. Lê apenas o resumo; não calcula nada.

A largura é controlada por `WIDTH`, e as listas quebram de linha por item, para caber em 80 colunas.

- **Importa do projeto:** `config`, `statistics_analyzer`
- **Testes:** `tests/test_pipeline.py`

### Constantes

| Nome | Linha | Significado |
|---|---|---|
| `WIDTH` | 10 | Largura do relatório, em colunas. |
| `BAR_WIDTH` | 11 | Tamanho máximo das barras. |
| `MAX_TIMELINE_ROWS` | 12 | Acima disso a linha do tempo é mostrada por ano. |
| `CATEGORY_NAMES` | 14 | Nome em português de cada tipo de dívida. |
| `MARKERS` | 23 | Marcadores sempre exibidos no bloco de Regex. |
| `EXPRESSIONS` | 24 | Expressões sempre exibidas no bloco de Regex. |

### Funções e classes

| Nome | Linha | O que faz |
|---|---|---|
| `section(title)` | 29 | Imprime o título de um bloco, com a linha até a largura do relatório. |
| `bar(value, maximum)` | 34 | Barra proporcional ao valor; qualquer valor acima de zero aparece. |
| `percent(part, total)` | 41 | Formata uma parte do total como porcentagem. |
| `print_items(title, items, separator=', ')` | 45 | Mostra uma lista em uma ou mais linhas, alinhada depois do título. |
| `ranking(entries, size)` | 62 | Itens de um ranking no formato: nome (ocorrências). |
| `count(number, names)` | 67 | Número com o nome no singular ou no plural: "1 issue", "2 issues". |
| `relative(path)` | 73 | Caminho a partir da pasta do projeto, quando o arquivo está nela. |
| `print_collection(summary)` | 81 | Bloco COLETA: repositório, registros coletados e analisados, fontes e período. |
| `print_debt(summary)` | 104 | Bloco DÍVIDA TÉCNICA: total identificado, por critério, por fonte e por tipo. |
| `print_regex(summary)` | 126 | Bloco REGEX: marcadores e expressões fixos, mais os outros padrões mais frequentes. |
| `print_spacy(summary)` | 143 | Bloco SPACY: tokens, lemas, expressões e entidades do NER. |
| `print_technologies(summary)` | 155 | Bloco TECNOLOGIAS: as oito mais citadas, com barras. |
| `print_sentiment(summary)` | 169 | Bloco SENTIMENTO: distribuição dos rótulos e média. |
| `print_resolution(summary)` | 181 | Bloco RESOLUÇÃO: fechamento com e sem dívida. Não aparece se só há commits. |
| `group_by_year(months)` | 195 | Soma os meses de cada ano, para períodos longos caberem na tela. |
| `print_timeline(summary)` | 206 | Bloco TEMPO: registros por mês, ou por ano em períodos longos. |
| `print_explanation(result)` | 219 | Mostra, etapa por etapa, a análise de um único texto (opção --text). |
| `print_report(summary, files)` | 259 | Mostra o resultado completo. 'files' são os arquivos gravados. |
