# Guia de Desenvolvimento

Como preparar o ambiente, rodar e testar o DebtRadar, e como fazer as
alterações mais comuns sem quebrar o que já funciona. É o documento para
abrir antes de mexer no código.

## Preparar o ambiente

```bash
git clone https://github.com/LuizRamalho11/debtradar.git
cd debtradar
python3 -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install --only-binary=:all: -r requirements.txt
python -m spacy download en_core_web_sm
cp .env.example .env                 # depois cole o token em GITHUB_TOKEN=
python main.py --check
```

O último comando deve terminar com "Ambiente pronto". Testado no macOS
com Python 3.14.7 e 3.9.6.

| Variável do `.env` | Padrão | Para quê |
|---|---|---|
| `GITHUB_TOKEN` | vazio | Sobe o limite da API de 60 para 5000 requisições por hora |
| `SPACY_MODEL` | `en_core_web_sm` | Modelo do spaCy |
| `DEFAULT_ISSUES` | `100` | Quantidade sugerida no modo interativo |

O `.env` nunca vai para o repositório. Para criar o token, siga a seção
"Configuração" do [README](../README.md).

## Comandos do dia a dia

| Quero | Comando |
|---|---|
| Conferir o ambiente | `python main.py --check` |
| Coletar e analisar, respondendo perguntas | `python main.py` |
| Coletar e analisar, sem perguntas | `python main.py --owner microsoft --repo vscode --limit 30 --label debt` |
| Coletar pull requests ou commits | `python main.py --owner microsoft --repo vscode --limit 100 --source commits` |
| Coletar as três fontes | `python main.py --owner psf --repo requests --limit 8 --source all` |
| Reanalisar uma coleta salva, sem rede | `python main.py --file data/raw/microsoft_vscode_debt_issues.json` |
| Ver cada etapa em uma frase | `python main.py --text "This needs refactoring and has no tests."` |
| Rodar os testes | `python -m pytest` |
| Rodar um arquivo de testes | `python -m pytest tests/test_regex_analyzer.py -q` |
| Rodar um teste pelo nome | `python -m pytest -k "trailers" -q` |

Depois de alterar uma regra, o ciclo é sempre o mesmo: rodar os testes e
reanalisar as coletas salvas com `--file`, comparando o resultado com o
anterior. Nenhum dos dois gasta cota da API.

## Onde fica cada coisa

```text
main.py                 interface de linha de comando
src/                    um módulo por etapa (ver REFERENCIA_MODULOS.md)
tests/                  testes automatizados
tools/                  geradores de documentação
data/raw/               coletas, como vieram da API
data/raw/backup/        coletas substituídas
data/processed/         documentos com todas as análises
data/results/           resumos consolidados
docs/                   documentação do projeto
docs/etapa1/            material da primeira etapa
requirements.txt        dependências
pytest.ini              configuração dos testes
.env.example            modelo do arquivo de configuração
```

## Os testes

São 118 testes, que rodam em cerca de um segundo e não acessam a rede.

| Arquivo | Testes | O que cobre |
|---|---|---|
| `tests/test_text_preprocessor.py` | 13 | Limpeza do Markdown, blocos de código, links, tags, assinaturas do Git, bots |
| `tests/test_regex_analyzer.py` | 53 | Um caso por padrão, os falsos positivos conhecidos, contagem única, posições |
| `tests/test_nlp_and_classification.py` | 20 | Lemas, sentenças, entidades, tecnologias, regra de classificação, sentimento |
| `tests/test_github_collector.py` | 21 | Normalização, máscara de e-mails, paginação, fontes, erros HTTP, limite da API, token, nomes de arquivo |
| `tests/test_pipeline.py` | 11 | Pipeline completo, resumo, relatório, `--text`, arquivos inválidos, configuração |
| `tests/conftest.py` | — | Dados de exemplo e recursos compartilhados |

Como os testes evitam a rede:

- **Coleta:** a classe `FakeSession`, em `test_github_collector.py`,
  substitui a sessão HTTP e devolve respostas montadas à mão, na ordem
  pedida. Dá para simular páginas, erros e o limite da API.
- **Pipeline:** `SAMPLE_ISSUES`, em `conftest.py`, é uma coleta pequena
  escrita para o teste. A função `make_issue` monta um registro de
  qualquer tipo.
- **Pastas de dados:** o recurso `data_dirs` aponta `RAW_DIR`,
  `PROCESSED_DIR` e `RESULTS_DIR` para uma pasta temporária.
- **spaCy:** o recurso `nlp` carrega o modelo uma vez por sessão; sem o
  modelo instalado, os testes que dependem dele são pulados.

Regra da casa: **todo defeito encontrado nos dados reais ganha um teste**
com o caso que o revelou. É por isso que há testes para a pasta `hack/`,
para o "todo" do VS Code e para as cercas de quatro crases.

## Convenções

- **Idioma:** nomes de arquivos, funções, variáveis e chaves de dados em
  inglês; docstrings, comentários, mensagens e documentação em português.
- **Docstrings:** a primeira linha diz o que a função faz; a referência
  dos módulos é gerada a partir dela.
- **Comentários:** explicam o porquê, de preferência citando o caso real
  que motivou a regra.
- **Mensagens de erro:** em português, dizendo o que aconteceu e o que
  fazer. Nenhum erro previsto deve terminar em traceback.
- **Etapas não imprimem.** Só `pipeline.py`, `report.py` e `main.py`
  escrevem na tela.
- **Largura:** a saída do programa cabe em 80 colunas.
- **Números na documentação** são copiados de um arquivo gerado ou da
  saída de um comando, nunca escritos de memória.
- **Sem rede nos testes.**
- **Segredos:** só no `.env`. O token não é impresso nem gravado.
- **Dados de terceiros:** os e-mails que aparecem nos textos coletados
  são mascarados na coleta, porque as coletas vão para o repositório.

## Receitas

### Acrescentar um padrão de Regex

1. Em `src/regex_analyzer.py`, inclua uma linha em `PATTERNS`:

   ```python
   DebtPattern("dead_code", "code", True, r"\bdead\s+code\b"),
   ```

   Os campos são nome, categoria, explícito (verdadeiro se a expressão por
   si só indica dívida) e a Regex. Coloque padrões específicos antes dos
   genéricos da mesma categoria.
2. Se for explícito e de uma das cinco categorias de dívida, inclua o
   nome em `STRONG_PATTERNS`, em `src/debt_classifier.py`. Sem isso o
   padrão liga `technical_debt_detected`, mas não confirma a categoria.
3. Acrescente o caso à lista de `test_pattern_matches`, em
   `tests/test_regex_analyzer.py`, e, se houver risco conhecido, um falso
   positivo à lista seguinte.
4. Rode os testes e reanalise as coletas com `--file`.

### Acrescentar uma tecnologia

Em `src/technology_analyzer.py`, inclua uma linha na categoria certa de
`TECHNOLOGIES`:

```python
"FastAPI": ["fast api"],
```

Se o nome também for uma palavra comum do inglês, inclua-o em
`CASE_SENSITIVE`, para valer só com a grafia exata. Se for ambíguo mesmo
com maiúscula, como "Go", inclua-o em `ALIASES_ONLY` e dê um apelido
inequívoco.

### Ampliar o vocabulário de um tipo de dívida

Em `src/debt_classifier.py`, acrescente o termo ao conjunto do tipo em
`TERMS`, **na forma de lema** e em minúsculas: `"refactor"`, não
`"refactoring"`. Para saber o lema que o spaCy dá a uma palavra, use
`python main.py --text "a palavra em uma frase"`.

Antes de acrescentar, veja se a palavra é específica do tema.
"deprecated" já esteve na lista de dependências e saiu, porque descreve
qualquer coisa antiga.

### Neutralizar um termo técnico no sentimento

Em `src/sentiment_analyzer.py`, acrescente a palavra a
`TECHNICAL_NEUTRAL`, em todas as flexões que aparecem: `"merge"`,
`"merges"`, `"merged"`.

### Ignorar uma conta automática

Contas terminadas em `[bot]` já são ignoradas. Para as demais, acrescente
o login, em minúsculas, a `KNOWN_BOTS`, em `src/text_preprocessor.py`.

### Acrescentar uma fonte de dados

O caminho seguido para incluir os commits serve de modelo:

1. Em `src/github_collector.py`, escreva uma função `normalize_…` que
   devolva um registro com **os mesmos campos** dos outros tipos
   (`ISSUE_FIELDS`, em `pipeline.py`, lista os obrigatórios) e um valor
   novo em `type`.
2. Escreva o método `_fetch_…` e chame-o em `collect`.
3. Inclua o nome em `SOURCES`, no coletor, e o tipo em `TYPE_NAMES`, em
   `src/statistics_analyzer.py`.
4. Nenhuma etapa de análise precisa mudar. Rode uma coleta real e olhe
   as listas de termos e tecnologias: cada fonte traz o seu próprio
   ruído. Os commits traziam assinaturas `Co-authored-by:`.
5. Acrescente testes com `FakeSession`.

Uma fonte que não venha do GitHub, como a transcrição de um áudio, pode
seguir o mesmo formato de registro e entrar pelo `--file`, sem passar
pelo coletor. Veja [PROXIMAS_ETAPAS.md](PROXIMAS_ETAPAS.md).

### Acrescentar uma etapa de análise

1. Crie o módulo em `src/`, com uma função que receba o que precisa e
   devolva um dicionário. O módulo não imprime nada.
2. Em `src/pipeline.py`, escreva a função da etapa, gravando o resultado
   em uma **chave nova** do documento, e chame-a em `analyze`. Ajuste
   `TOTAL_STEPS` e a numeração.
3. Some o resultado em `build_summary`, em
   `src/statistics_analyzer.py`.
4. Mostre-o em um bloco novo de `src/report.py`, lendo só o resumo.
5. Inclua a etapa em `explain`, se fizer sentido para um texto só.
6. Atualize [FORMATO_DOS_DADOS.md](FORMATO_DOS_DADOS.md).

### Acrescentar uma opção de linha de comando

Em `main.py`, declare a opção em `build_parser` e trate-a em `main` ou em
`run_pipeline`. Acrescente-a à tabela de opções do README.

### Atualizar a documentação depois de uma mudança

- Regere a referência dos módulos se nomes, assinaturas ou linhas
  mudaram: `python tools/gerar_referencia.py`. Se houver uma função ou
  constante nova sem descrição, o script para e diz qual é.
- Reanalise as coletas com `--file` e regere os resultados da etapa:
  `python tools/gerar_resultados.py`.
- Se a mudança veio de um problema real, registre-o no diário de bordo
  da etapa.
- Se foi uma escolha de projeto, registre-a em
  [DECISOES.md](DECISOES.md).

## Controle de versão

- O ramo principal é `main`.
- Ficam fora do repositório: `.env`, `.venv/`, caches e os arquivos
  `.docx` de origem (proposta e regras da disciplina).
- As coletas em `data/` **são versionadas**: são elas que permitem
  demonstrar o programa e refazer os resultados sem rede.
- Sugestão para as próximas etapas: um ramo por etapa (`etapa2`,
  `etapa3`), unido ao `main` quando a etapa estiver apresentável, e uma
  marca (`git tag etapa1`) no commit apresentado.

## Problemas comuns

| Sintoma | Causa | O que fazer |
|---|---|---|
| "Limite de requisições da API do GitHub atingido" | Cota de 60 por hora, sem token | Esperar o horário indicado, configurar o token ou usar `--file` |
| "GITHUB_TOKEN inválido ou expirado" | Token errado ou vencido | Gerar outro e colar no `.env` |
| "Repositório não encontrado" | Nome errado, ou repositório privado | Conferir owner e repositório |
| "Nenhum registro encontrado com esses critérios" | A label não existe no repositório | Conferir as labels na página do repositório |
| "modelo 'en_core_web_sm' não encontrado" | Modelo do spaCy não instalado | `python -m spacy download en_core_web_sm` |
| `pip install` tenta compilar o spaCy e falha | Python sem pacote pronto da versão mais nova | Usar `pip install --only-binary=:all: -r requirements.txt` |
| "O arquivo não é uma coleta do DebtRadar" | `--file` apontou para um arquivo de `data/processed/` ou de outro formato | Usar um arquivo de `data/raw/` |
| Aviso `NotOpenSSLWarning`, do urllib3 | Python do sistema no macOS, compilado com LibreSSL | Só um aviso; o programa funciona |
| Aviso `codecs.open() is deprecated` nos testes | O `vaderSentiment` usa uma função obsoleta no Python 3.14 | Só um aviso, já filtrado no `pytest.ini` |
| A coleta veio com menos registros do que o pedido | O repositório tem poucos itens com a label, ou muitos eram de bots | Ver "Registros coletados" e "analisados" no relatório |
