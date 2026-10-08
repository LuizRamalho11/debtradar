# Guia da Apresentação — DebtRadar (1ª etapa)

Roteiro de 10 minutos para dois integrantes, 5 minutos cada. Todos os
números deste guia saíram de execuções reais do programa; os valores
podem ser conferidos rodando os comandos da seção de demonstração.

Este guia traz **ideias para falar**, não um texto para decorar. As
regras da disciplina não permitem cola nem leitura dos slides: ensaiem
até conseguir explicar cada bloco com as próprias palavras.

## O que as regras exigem

- No máximo 5 minutos por integrante, e os dois falam pelo mesmo tempo.
- Ordem: tema e teoria → implementação → erros e soluções → programa
  funcionando.
- O arquivo-fonte é mostrado e o programa é executado ao vivo, com todas
  as suas opções.
- Para bibliotecas que não foram dadas em aula, dizer onde aprender.
- O diário de bordo aparece em um slide.

## Divisão

| Bloco | Tempo | Quem | Slide | Conteúdo |
|---|---|---|---|---|
| 1 | 0:00 – 1:15 | Integrante 1 | 1 a 3 | Abertura, problema, dívida técnica, pergunta |
| 2 | 1:15 – 2:15 | Integrante 1 | 4 | Fonte de dados e GitHub API |
| 3 | 2:15 – 2:45 | Integrante 1 | 5 | Metodologia (o pipeline) |
| 4 | 2:45 – 4:15 | Integrante 1 | 6 | Pré-processamento e Regex |
| 5 | 4:15 – 5:30 | Integrante 2 | 7 | spaCy e tecnologias |
| 6 | 5:30 – 6:45 | Integrante 2 | 8 | Classificação e sentimento |
| 7 | 6:45 – 7:20 | Integrante 2 | 9 | Resultados |
| 8 | 7:20 – 8:05 | Integrante 1 | 10 | Diário de bordo |
| 9 | 8:05 – 9:45 | Integrante 2 | 11 | Demonstração |
| 10 | 9:45 – 10:00 | Integrante 2 | 12 | Próximas etapas |

Integrante 1: 4:15 + 0:45 = 5:00. Integrante 2: 3:05 + 1:55 = 5:00.

A divisão acompanha o código: o Integrante 1 fica com tudo o que acontece
até a Regex (coleta, limpeza, padrões) e o Integrante 2 com tudo o que
vem depois (spaCy, classificação, sentimento, resultado).

## Roteiro bloco a bloco

### Bloco 1 — Abertura e problema (Integrante 1, 1:15)

- Dívida técnica: atalhos e decisões de curto prazo que comprometem a
  qualidade e a manutenção do software.
- Ela deixa rastros em texto: issues de refatoração, comentários `TODO`
  e `FIXME`, discussões sobre código legado.
- Pergunta de pesquisa: como os desenvolvedores identificam, discutem e
  priorizam a dívida técnica, e como esse discurso se manifesta?
- Nesta etapa: só texto do GitHub (issues, pull requests e mensagens
  de commit), com Regex e spaCy.
- Cinco tipos analisados: código, arquitetura, testes, documentação e
  dependências. Vale dar um exemplo real: "Security: vulnerable
  dependency image-size" é uma issue de dívida de dependências.

### Bloco 2 — Fonte de dados e GitHub API (Integrante 1, 1:00)

- Por que a API e não raspagem de página: os dados chegam em JSON, com
  título, corpo, autor, datas, labels e comentários.
- O usuário informa owner, repositório e quantidade. A opção `--source`
  escolhe a fonte: issues, pull requests, commits ou as três.
- Dois cuidados que os dados reais exigiram: a listagem de issues também
  devolve pull requests (no VS Code, 36 de 50 itens), e sem token a API
  permite 60 requisições por hora.
- **Mostrar:** `src/github_collector.py`, método `_fetch_issues`
  (linha 177), que separa issues de pull requests pelo campo `type`, e
  `_paginate` (linha 232).
- **Dizer sobre o código:** a próxima página vem no cabeçalho `Link` da
  resposta; como é um gerador, a página seguinte só é pedida se ainda
  faltam registros.

### Bloco 3 — Metodologia (Integrante 1, 0:30)

- O pipeline: coleta → pré-processamento → Regex → spaCy e tecnologias →
  classificação → sentimento → estatísticas.
- Cada etapa acrescenta o seu resultado ao documento da issue.
- **Mostrar:** `src/pipeline.py`, função `analyze` (linha 194). São seis
  chamadas, uma por etapa, na mesma ordem do diagrama do slide.

### Bloco 4 — Pré-processamento e Regex (Integrante 1, 1:30)

- Issue é Markdown: tem código, links, tabelas, HTML. Antes de analisar
  é preciso limpar, sem apagar o que interessa.
- Os blocos de código não são jogados fora: vão para um campo separado,
  onde ainda se procura `TODO` e `FIXME`.
- **Mostrar:** `src/text_preprocessor.py`, a Regex `CODE_BLOCK`
  (linha 21). O `\1` exige que o bloco feche com a mesma cerca que abriu.
- Detecção: 36 padrões, sem diferenciar maiúsculas de minúsculas. São 22
  explícitos (por si só indicam dívida, como `code smell`) e 14 de
  contexto (só indicam o assunto, como `documentation`).
- **Mostrar:** `src/regex_analyzer.py`, a lista `PATTERNS` (linha 60).
  Explicar uma linha: `\btech(?:nical)?[\s-]+debts?\b` cobre "tech
  debt", "technical-debt" e o plural.
- **Se der tempo:** a função `comment_marker` (linha 45), que nasceu de
  um falso positivo real (ver diário de bordo).
- Fechar com o limite: Regex só encontra o que foi escrito de forma
  literal. Em 30 issues rotuladas como `debt` pelos mantenedores do
  VS Code, só 11 têm um padrão explícito. Por isso entra o spaCy.

### Bloco 5 — spaCy e tecnologias (Integrante 2, 1:15)

- O spaCy traz conhecimento da língua: tokens, lemas, classes
  gramaticais, stopwords e entidades.
- Exemplo real de lematização: remove, removed, removing e removes viram
  o lema `remove`.
- Diferença para a Regex, medida nos dados: o padrão
  `duplicat(?:ed|ion)` achou 8 ocorrências; o lema `duplicate` reuniu 12.
- **Mostrar:** `src/nlp_analyzer.py`, função `is_relevant` (linha 60):
  só entram nas frequências tokens alfabéticos que não são stopwords
  nem identificadores de código.
- NER e tecnologias são coisas separadas. O modelo rotulou `Linux` como
  lugar e `Claude` como pessoa. Por isso as tecnologias vêm de uma lista
  própria, com 40 nomes, procurada com o `PhraseMatcher`.
- **Mostrar:** `src/technology_analyzer.py`, o dicionário `TECHNOLOGIES`
  (linha 24). Acrescentar uma tecnologia é incluir uma linha.
- Um número para citar: a lista encontrou 20 menções a Copilot; o NER
  havia reconhecido 12.

### Bloco 6 — Classificação e sentimento (Integrante 2, 1:15)

- A classificação é um baseline de regras. **Não é Machine Learning.**
- Dois tipos de evidência: forte (padrão explícito da Regex) e fraca
  (vocabulário do tema, contado pelos lemas do spaCy).
- **Mostrar:** `src/debt_classifier.py`, função `decide` (linha 60). A
  regra cabe em cinco linhas: `yes` com evidência forte ou 3 ocorrências
  fracas; `possible` com 1 ou 2; `no` sem nenhuma.
- Exemplo: "Authentication needs refactoring and has no tests." dá
  código sim, arquitetura possível, testes sim.
- Sentimento: VADER, um léxico para inglês. Mede o tom do texto, não a
  dívida.
- A fórmula do VADER: `compound = x / √(x² + 15)`, onde `x` é a soma das
  valências das palavras. O rótulo é positivo a partir de +0,05 e
  negativo até -0,05.
- Duas adaptações nossas: média por sentença, e 37 termos técnicos sem
  valência ("shared" contava como elogio).
- **Onde aprender:** o VADER não foi dado em aula. Indicar o
  repositório `cjhutto/vaderSentiment` no GitHub e o artigo de Hutto e
  Gilbert (2014). Para o spaCy, a documentação em spacy.io e o curso
  gratuito em course.spacy.io.

### Bloco 7 — Resultados (Integrante 2, 0:35)

- No corpus principal (30 issues `debt` do VS Code): 16 identificadas,
  53%. Código é o tipo mais comum (7), depois testes (6).
- Tom predominante neutro: 8 positivas, 15 neutras, 7 negativas.
- Validação com as labels dos mantenedores, em três repositórios: 29 de
  57 issues de dívida identificadas (51%); no grupo de controle, 1 em 9.
- Por fonte, no VS Code: 16 de 30 issues `debt`, mas só 3 de 15 pull
  requests `debt`. Textos curtos trazem menos vocabulário.
- Indício de priorização: as issues com dívida já fechadas levaram uma
  mediana de 1,3 dia; as sem dívida, 4,0 dias. No pandas o padrão se
  inverte, então não dá para generalizar.

### Bloco 8 — Diário de bordo (Integrante 1, 0:45)

Escolher três problemas e contar cada um em uma frase de causa e uma de
solução. Sugestão:

- **"todo" não era TODO.** No VS Code, "todo" é o nome de um recurso do
  chat. Solução: marcadores valem em maiúsculas, ou em minúsculas com
  dois-pontos.
- **Bots.** No corpus de controle, 13 dos 16 comentários eram de um bot.
  Solução: ignorar contas terminadas em `[bot]`.
- **Sentimento distorcido.** "shared" somava +95 pontos em 68
  ocorrências. Solução: neutralizar termos técnicos.

O arquivo `DIARIO_DE_BORDO.md` tem 27 problemas; o slide deve trazer só
os escolhidos.

### Bloco 9 — Demonstração (Integrante 2, 1:40)

Ver a seção [Demonstração](#demonstração).

### Bloco 10 — Próximas etapas (Integrante 2, 0:15)

- 2ª etapa: áudio de podcasts sobre dívida técnica.
- 3ª etapa: vídeo de palestras.
- Ao final, um dashboard reunindo as três modalidades.

## Demonstração

### Antes de começar

- Terminal aberto na pasta do projeto, com o ambiente ativado
  (`source .venv/bin/activate`).
- Fonte grande e janela com pelo menos 80 colunas.
- Editor com os arquivos de código já abertos em abas.
- Rodar uma vez `python main.py --check` minutos antes, para confirmar
  que o ambiente está pronto.

### Roteiro

| Passo | Comando ou ação | O que mostrar | Tempo |
|---|---|---|---|
| 1 | `python main.py` | O programa pergunta owner, repositório e quantidade | 20 s |
| 2 | Responder `psf`, `requests`, `5` e Enter na label | A coleta ao vivo e o andamento de `[1/7]` a `[7/7]` | 10 s |
| 3 | `python main.py --file data/raw/microsoft_vscode_debt_issues.json` | O corpus principal, o mesmo dos slides | 5 s |
| 4 | Rolar a saída: bloco COLETA | 30 issues, período | 5 s |
| 5 | Bloco DÍVIDA TÉCNICA | 16 de 30; categorias com "sim" e "possível" | 15 s |
| 6 | Bloco REGEX | `TODO 1/1`, `debt 9/8`, `refactor 1/1` | 10 s |
| 7 | Blocos SPACY e TECNOLOGIAS | Lemas; entidades do NER ao lado da lista do projeto | 15 s |
| 8 | Blocos SENTIMENTO e TEMPO | 8, 15 e 7; issues por mês | 10 s |
| 9 | `python main.py --text "Authentication needs refactoring and has no tests."` | Uma frase passando por Regex, spaCy (tabela de tokens), classificação e sentimento | 20 s |

Os passos 1, 3 e 9 mostram três formas de usar o programa: modo
interativo, `--file` e `--text`. Vale dizer em uma frase que os mesmos
valores podem ser passados por `--owner`, `--repo`, `--limit` e
`--label`, que `--source` escolhe entre issues, pull requests e commits,
e que `--check` verifica o ambiente.

O passo 9 funciona sem internet e é o melhor momento para apontar a
tabela de tokens: `refactoring` e `tests` aparecem com o lema e a classe
gramatical, e a classificação mostra a evidência de cada categoria.

### O que esperar no passo 2

A coleta ao vivo traz as issues mais recentes, então o resultado muda a
cada dia. No ensaio de 08/10/2026 vieram 5 issues e 13 comentários em 3
segundos, e 3 das 5 foram marcadas "com dívida" apenas por repetirem a
palavra `test`. Se isso aparecer, usem a favor: é a limitação da regra,
acontecendo ao vivo.

Cada coleta de 5 issues gasta cerca de 6 requisições. Sem token são 60
por hora: dá para ensaiar umas dez vezes por hora.

### Plano B, sem internet

Pular os passos 1 e 2 e começar no passo 3. Dizer por quê: a coleta fica
gravada em disco, e a análise pode ser refeita sem rede. O passo 3 é o
que importa; os números dos slides vêm dele.

### Se sobrar tempo

- `python -m pytest -q` termina em um segundo e mostra `118 passed`.
- `python main.py --file data/raw/psf_requests_all.json` mostra as três
  fontes juntas: 24 registros coletados, 14 de bots, 10 analisados.
- Abrir `data/processed/microsoft_vscode_debt_issues.json` e buscar
  `"number": 329218` mostra a ocorrência `TODO` com o contexto.

## Código: o que cada um abre e explica

Ninguém precisa decorar arquivos inteiros. Cada trecho abaixo tem poucas
linhas e uma ideia para explicar.

### Integrante 1

| Arquivo | Trecho | A ideia |
|---|---|---|
| `src/github_collector.py` | `_fetch_issues` (linha 177) e `_paginate` (linha 232) | Issues e pull requests vêm na mesma listagem; paginação pelo cabeçalho `Link` |
| `src/pipeline.py` | `analyze` (linha 194) | Uma chamada por etapa, na ordem do diagrama |
| `src/text_preprocessor.py` | `CODE_BLOCK` (linha 21) e `clean_text` (linha 68) | Código é separado, não apagado; cinco passos numerados |
| `src/regex_analyzer.py` | `PATTERNS` (linha 60) e `comment_marker` (linha 45) | Padrão explícito ou de contexto; `TODO` em maiúsculas |

### Integrante 2

| Arquivo | Trecho | A ideia |
|---|---|---|
| `src/nlp_analyzer.py` | `is_relevant` (linha 60) e `count_lemmas` (linha 71) | Quais tokens contam; frequência por lema e classe gramatical |
| `src/technology_analyzer.py` | `TECHNOLOGIES` (linha 24) e `find` (linha 113) | Lista própria, buscada por tokens; não é NER |
| `src/debt_classifier.py` | `decide` (linha 60) e `TERMS` (linha 45) | A regra inteira em cinco linhas |
| `src/sentiment_analyzer.py` | `analyze` (linha 73) e `TECHNICAL_NEUTRAL` (linha 24) | Média por sentença; termos técnicos sem valência |

## Números para ter na ponta da língua

| Número | O que é |
|---|---|
| 30 → 16 (53%) | Issues `debt` do VS Code → identificadas com dívida |
| 11 de 30 | Têm um padrão explícito da Regex |
| 29 de 57 (51%) | Issues rotuladas como dívida em três repositórios → identificadas |
| 3 de 15 | Pull requests `debt` do VS Code → identificados |
| 16 de 97 | Commits recentes do VS Code com dívida identificada |
| 1,3 contra 4,0 dias | Mediana até fechar: issues com dívida contra sem dívida (VS Code) |
| 1 de 9 | Alarmes no corpus de controle (label `bug`) |
| 36 (22 + 14) | Padrões de Regex: explícitos + de contexto |
| 8 contra 12 | Regex `duplicat(?:ed\|ion)` contra o lema `duplicate` |
| 20 contra 12 | Menções a Copilot: lista do projeto contra o NER |
| 40 | Tecnologias na lista do projeto |
| 8, 15 e 7 | Issues positivas, neutras e negativas |
| +95 em 68 | Pontos de "shared" no léxico original do VADER |
| 13 de 16 | Comentários de bot no corpus de controle |
| 118 | Testes automatizados |

## O que não dizer

- Que a classificação é Machine Learning. É um conjunto de regras.
- Que o sentimento mede a dívida técnica. Ele mede o tom do texto.
- Que o spaCy reconhece tecnologias. Quem reconhece é a lista do projeto.
- Que 53% é a acurácia. É a parcela de issues rotuladas que o programa
  identifica; não há gabarito por tipo de dívida.
- Que as issues com dívida são mais prioritárias. O tempo até fechar é
  um indício, e ele se inverte no pandas.
- Que o resultado vale para o GitHub em geral. São amostras pequenas, de
  poucos repositórios.

## PERGUNTAS QUE PODEM SER FEITAS

**Por que GitHub?**
É a fonte definida na proposta e uma das sugeridas pela disciplina. A API
entrega os dados em JSON, com datas, autor e labels. As labels dos
mantenedores ainda serviram para validar o resultado.

**Por que usar a API e não web scraping?**
A API devolve campos prontos e informa a cota e a próxima página nos
cabeçalhos. As regras da etapa aceitam web scraping ou web API; o
programa usa a API.

**Por que Regex?**
Para duas tarefas em que a forma do texto é previsível: retirar a
formatação do Markdown (22 expressões) e encontrar marcadores como
`TODO`, `FIXME` e "technical debt" (36 padrões).

**Por que spaCy?**
Porque a Regex só acha o que foi escrito literalmente. O spaCy junta as
flexões de uma palavra pelo lema, separa classes gramaticais e descarta
stopwords. O lema `duplicate` reuniu 12 ocorrências onde a Regex achou 8.

**Qual a diferença entre Regex e NLP?**
A Regex trabalha com caracteres; o spaCy, com tokens e gramática. Um
exemplo dos dados: uma Regex ingênua acha "java" dentro de "JavaScript";
para o spaCy são tokens diferentes.

**Como a dívida técnica foi classificada?**
Por regras. Para cada categoria, um padrão explícito da Regex confirma;
sem ele, o vocabulário do tema precisa aparecer três vezes. Com uma ou
duas ocorrências o resultado é "possível". A evidência fica gravada.

**Isso é Machine Learning?**
Não. Não há treinamento nem modelo próprio. É um baseline de regras. O
único modelo treinado no programa é o do spaCy, que já vem pronto.

**Por que não usar Machine Learning?**
Não há dados rotulados por tipo de dívida para treinar. Um conjunto de
regras também é mais fácil de explicar e de conferir.

**Como o sentimento foi calculado?**
Com o VADER, um léxico em que cada palavra tem uma valência. O texto é
dividido em sentenças, cada uma recebe uma pontuação de -1 a +1, e o
documento fica com a média. Termos técnicos tiveram a valência removida.

**Por que o sentimento, se ele não mede a dívida?**
Ele descreve como a dívida é discutida. Nos dados, o tom é
predominantemente neutro: metade das issues.

**Como sabem se o resultado está certo?**
Não há gabarito por tipo. A referência usada foram as labels dos
mantenedores: 29 de 57 issues de dívida identificadas, e 1 alarme em 9
issues de um corpus de controle. Há também 118 testes automatizados.

**Por que só metade das issues é identificada?**
Porque os desenvolvedores raramente usam o vocabulário esperado. Eles
escrevem "Remove" ou "Migrate", não "technical debt". Esse é um resultado
do trabalho.

**Quais são as limitações?**
A classificação não distingue assunto de problema; o NER erra em texto
técnico; o sentimento não entende contexto; textos curtos, como pull
requests e commits, rendem pouco; a análise é só em inglês; e as amostras
são pequenas.

**A proposta falava em commits, pull requests e documentação. Foi tudo
feito?**
Issues, pull requests e commits, sim, pela API. Arquivos de documentação,
o BugRepo e a raspagem com BeautifulSoup ficaram de fora; as regras da
etapa aceitam web scraping ou Web API, e usamos a API.

**Como vocês tratam a "priorização" da pergunta de pesquisa?**
O programa não mede prioridade. Ele mostra um indício: quanto das issues
com e sem dívida já foi fechado, e em quanto tempo. No VS Code a mediana
foi de 1,3 dia com dívida e 4,0 sem; no pandas o padrão se inverte.

**O que foi mais difícil?**
Os falsos positivos que só apareceram com dados reais: "todo" como nome
de recurso do VS Code, a pasta `hack/` do Kubernetes e os textos
gerados por bots.

**Como o projeto poderá evoluir?**
Nas próximas etapas, áudio de podcasts e vídeo de palestras, e ao final
um dashboard. No texto, o caminho natural é rotular uma amostra à mão
para medir a classificação por tipo.

**Por que essa metodologia responde à pergunta de pesquisa?**
A pergunta é como a dívida é identificada, discutida e priorizada. A
Regex e a classificação mostram como ela é identificada e de que tipo;
os termos, as tecnologias e o sentimento mostram como é discutida; a
análise por mês mostra quando; e o fechamento das issues dá um indício,
ainda fraco, de priorização.

**E se o repositório não tiver a label `debt`?**
A label é opcional. Sem ela o programa analisa as issues mais recentes,
como na coleta ao vivo da demonstração.

**Precisa de token do GitHub?**
Não para funcionar. Sem token o limite é de 60 requisições por hora; com
token, 5000.
