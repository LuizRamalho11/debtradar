# Diário de Bordo — DebtRadar (1ª etapa)

Problemas encontrados de fato durante o desenvolvimento, na ordem em que
apareceram. Os números citados vêm das execuções reais do programa sobre
issues coletadas do GitHub.

## Problema 1 — Coletas do mesmo repositório se sobrescreviam

- **Problema:** uma coleta sem label apagaria a coleta com a label `debt`
  do mesmo repositório.
- **Causa:** o nome do arquivo usava só o owner e o repositório.
- **Como foi identificado:** ao planejar o segundo teste de coleta no
  `microsoft/vscode`, antes de executá-lo.
- **Solução:** a label passou a fazer parte do nome do arquivo. Depois, a
  coleta anterior passou a ser movida para `data/raw/backup/`.
- **Resultado:** as duas coletas passaram a coexistir.
- **Aprendizado:** todo parâmetro que muda o resultado precisa aparecer no
  nome do arquivo gerado.

## Problema 2 — Pull requests misturados às issues

- **Problema:** a listagem de issues da API também devolve pull requests.
- **Causa:** para a API do GitHub, todo pull request é uma issue.
- **Como foi identificado:** previsto na documentação da API e medido no
  teste de paginação: no `microsoft/vscode`, 36 de 50 itens eram pull
  requests.
- **Solução:** itens com o campo `pull_request` são descartados, e a
  paginação continua até completar a quantidade pedida.
- **Resultado:** 12 issues obtidas em 10 páginas de 5 itens, sem
  duplicatas e sem pull requests.
- **Aprendizado:** a quantidade pedida ao usuário não é a quantidade de
  itens pedida à API.

## Problema 3 — Limite de 60 requisições por hora

- **Problema:** sem token, a API permite 60 requisições por hora, e cada
  issue com comentários custa uma requisição a mais.
- **Causa:** o desenvolvimento foi feito sem `GITHUB_TOKEN`.
- **Como foi identificado:** ao consultar a cota antes do primeiro teste
  (59 requisições restantes).
- **Solução:** a coleta é gravada em disco e pode ser reanalisada com
  `--file`; se o limite acaba no meio, as issues já coletadas são
  mantidas e o programa avisa. O esgotamento do limite foi testado com
  uma resposta simulada, para não bloquear a máquina por uma hora.
- **Resultado:** todos os testes couberam na cota. A coleta de 15 issues
  do Kubernetes, com 136 comentários, custou 21 requisições.
- **Aprendizado:** separar a coleta da análise permite repetir a análise
  quantas vezes for preciso sem depender da rede.

## Problema 4 — Blocos de código com quatro crases

- **Problema:** sobravam crases soltas no texto limpo.
- **Causa:** a Regex esperava cercas de exatamente três crases; 44 blocos
  do corpus de controle usavam quatro.
- **Como foi identificado:** uma contagem de resíduos de Markdown no
  texto limpo acusou 28 crases.
- **Solução:** a Regex passou a aceitar três ou mais crases e a exigir,
  com uma referência retroativa (`\1`), que o bloco feche com a mesma
  cerca que abriu. Crases duplas de código inline também foram tratadas.
- **Resultado:** nenhum resíduo de crase nos corpora.
- **Aprendizado:** medir o que sobra depois da limpeza encontra erros que
  a leitura de alguns exemplos não encontra.

## Problema 5 — Links com colchetes no texto

- **Problema:** links como `[... content[].text ...](url)` deixavam
  `[...]( )` no texto limpo.
- **Causa:** a Regex de link não aceitava colchetes dentro do texto do
  link.
- **Como foi identificado:** ao ler o contexto de uma ocorrência de
  "workaround", que trazia um colchete sem par.
- **Solução:** a Regex passou a aceitar um nível de colchetes internos.
- **Resultado:** 106 links no corpus de controle e nenhum resíduo.
- **Aprendizado:** texto técnico tem símbolos de código dentro da prosa;
  as Regex de Markdown precisam contar com isso.

## Problema 6 — Bots contaminando a análise

- **Problema:** textos gerados por bots entravam como se fossem
  discussão de desenvolvedores.
- **Causa:** o repositório do VS Code usa um bot que abre issues de erro
  e comenta com análises automáticas.
- **Como foi identificado:** ao investigar as crases restantes, vimos que
  vinham de um bot. No corpus de controle, 13 dos 16 comentários (99% do
  texto dos comentários) e 11 das 20 issues eram de bot, e um desses
  comentários gerou uma detecção de "refactor".
- **Solução:** comentários e issues de contas terminadas em `[bot]`, ou
  listadas em `KNOWN_BOTS`, são ignorados.
- **Resultado:** o corpus de controle caiu de 20 para 9 issues
  analisadas.
- **Aprendizado:** antes de analisar o que as pessoas dizem, é preciso
  conferir quem escreveu.

## Problema 7 — "todo" como nome de recurso do produto

- **Problema:** a palavra "todo" era contada como marcador `TODO`.
- **Causa:** a busca ignorava maiúsculas e minúsculas, e no VS Code
  "todo" é um recurso do chat ("todo list", "tips + todo").
- **Como foi identificado:** ao listar os contextos reais antes de
  escrever a Regex: 4 das 5 ocorrências não eram comentários de código.
- **Solução:** primeiro, um lookahead negativo para "todo list". Depois,
  a regra final: `TODO`, `FIXME` e `XXX` valem em maiúsculas; em
  minúsculas, só com sintaxe de marcador (`todo:`). A classe gramatical
  do spaCy foi testada e não distingue os casos.
- **Resultado:** `TODO` passou de 3 ocorrências em 2 issues para 1 em 1.
- **Aprendizado:** "ignorar maiúsculas" não serve para todos os padrões;
  em marcadores de código, a caixa é informação.

## Problema 8 — A pasta `hack/` do Kubernetes

- **Problema:** as 6 ocorrências de `HACK` no Kubernetes eram falsas.
- **Causa:** o repositório tem uma pasta chamada `hack/`, citada em
  caminhos como `hack/README.md`.
- **Como foi identificado:** ao conferir os contextos da primeira coleta
  desse repositório.
- **Solução:** lookbehind e lookahead negativos impedem que um marcador
  seja contado quando faz parte de um caminho de arquivo.
- **Resultado:** `HACK` caiu de 6 para 0 e o total de dívida identificada
  nesse corpus, de 10 para 8.
- **Aprendizado:** cada repositório novo traz um falso positivo novo; as
  Regex precisam ser testadas em mais de um projeto.

## Problema 9 — O vocabulário explícito de dívida é raro

- **Problema:** das 30 issues que os mantenedores do VS Code rotularam
  como `debt`, só 12 tinham um padrão explícito, e 9 não tinham padrão
  nenhum.
- **Causa:** os desenvolvedores escrevem "Remove", "Migrate", "unify";
  quase nunca "technical debt" ou "refactor".
- **Como foi identificado:** ao comparar o resultado das Regex com a
  label dada pelos mantenedores.
- **Solução:** os padrões foram divididos em explícitos e de contexto, e
  a classificação passou a usar também o vocabulário de cada tema,
  contado pelos lemas do spaCy.
- **Resultado:** 16 das 30 issues passaram a ser identificadas. Em três
  repositórios, 29 das 57 issues rotuladas como dívida, limpeza ou
  refatoração.
- **Aprendizado:** Regex encontra o que é dito de forma literal; a maior
  parte da dívida técnica é descrita com outras palavras.

## Problema 10 — O NER do spaCy erra em texto técnico

- **Problema:** o modelo marcou números de issue como `MONEY`, medidas
  em pixels como `DATE` e nomes de arquivo como `PERSON`.
- **Causa:** o `en_core_web_sm` foi treinado com notícias e textos da
  web, não com texto de software.
- **Como foi identificado:** ao listar as entidades por rótulo: das 632
  entidades, 397 precisaram ser descartadas, e as "pessoas" mais
  frequentes eram "Claude", "Tab", "metadata" e "SCM".
- **Solução:** entidades numéricas e com símbolos de código são
  descartadas, e as tecnologias passaram a ser procuradas com uma lista
  própria e o `PhraseMatcher`. Duas tentativas não funcionaram: tratar
  linhas em branco como fim de sentença melhorou a segmentação, mas não
  mudou as entidades; e o modelo `en_core_web_md` não foi melhor.
- **Resultado:** a lista do projeto encontrou 20 menções a Copilot; o NER
  havia reconhecido 12.
- **Aprendizado:** um modelo pronto precisa ser avaliado no domínio em
  que será usado, e uma hipótese de melhoria precisa ser medida.

## Problema 11 — Erros de classe gramatical e de lema

- **Problema:** substantivos usados como modificadores saíam como
  adjetivos ("token", "terminal", "layout"), e palavras raras recebiam
  lemas errados ("deminifie", "allowliste", "panda" para a biblioteca
  pandas).
- **Causa:** vocabulário de software que o modelo não conhece.
- **Como foi identificado:** nas listas de termos mais frequentes dos
  dados reais.
- **Solução:** não foi corrigido. Identificadores de código e nomes
  próprios ficam fora das frequências, o que reduz o efeito.
- **Resultado:** os erros continuam visíveis nas listas e estão
  registrados nas limitações.
- **Aprendizado:** nem todo erro do modelo vale um ajuste; alguns devem
  ser explicados em vez de escondidos.

## Problema 12 — Tecnologias coladas por barra

- **Problema:** `C++/C#` não era reconhecido.
- **Causa:** o tokenizador do spaCy não separa a barra quando há símbolos
  ou pontos em volta; `C++/Rust` vira um token só.
- **Como foi identificado:** em um teste com frases escritas para isso.
  Não há ocorrência de `C++` nem de `C#` nos corpora reais.
- **Solução:** de início ficou só registrado como limitação. Depois, os
  tokens que contêm barra passaram a ser analisados de novo, com as
  partes separadas.
- **Resultado:** `C++/Rust` e `Node.js/Electron` são reconhecidos. Nos
  dados reais a mudança acrescentou 1 menção em 275, de um caminho de
  pacote do Kubernetes.
- **Aprendizado:** buscar por tokens resolve um problema e cria outro; é
  preciso conhecer as regras do tokenizador e medir o efeito de cada
  correção nos dados.

## Problema 13 — O sentimento saturava em textos longos

- **Problema:** 11 dos 30 documentos ficavam com pontuação acima de 0,9
  em módulo.
- **Causa:** o VADER soma as valências das palavras; em um texto longo a
  soma sempre fica grande.
- **Como foi identificado:** ao aplicar o VADER ao documento inteiro e
  olhar a distribuição das pontuações.
- **Solução:** a pontuação é calculada por sentença e depois se tira a
  média.
- **Resultado:** as médias ficaram entre -0,24 e +0,18, e metade dos
  documentos é classificada como neutra.
- **Aprendizado:** uma ferramenta feita para frases curtas não pode ser
  aplicada a um texto longo sem adaptação.

## Problema 14 — Termos técnicos contados como opinião

- **Problema:** "shared" somava +95 pontos em 68 ocorrências; "approval"
  +38; "values" +20; "no" -43 em 36 ocorrências.
- **Causa:** no léxico do VADER essas palavras têm carga emocional; em
  software são termos técnicos ("shared state", "auto-approval", "no
  tests").
- **Como foi identificado:** ao somar a valência acumulada de cada
  palavra do corpus.
- **Solução:** 37 termos técnicos, entre eles o próprio "debt", tiveram a
  valência removida. "no" também, mas continua invertendo a palavra
  seguinte ("no good").
- **Resultado:** a distribuição passou de 10 positivas, 14 neutras e 6
  negativas para 8, 15 e 7.
- **Aprendizado:** um léxico genérico precisa ser ajustado ao domínio, e
  o ajuste deve vir dos dados.

## Problema 15 — "deprecated" contava como dívida de dependências

- **Problema:** uma issue sobre padrões de interface foi classificada
  como dívida de dependências.
- **Causa:** "deprecated" e "outdated" estavam no vocabulário da
  categoria, mas descrevem qualquer coisa antiga ("deprecated patterns").
- **Como foi identificado:** ao ler a evidência de cada uma das 30
  classificações.
- **Solução:** os dois termos saíram da lista; a Regex continua cobrindo
  "outdated dependency" e "deprecated dependency".
- **Resultado:** só a issue da dependência vulnerável ficou na categoria.
- **Aprendizado:** guardar a evidência de cada decisão torna possível
  auditar uma regra.

## Problema 16 — Exemplos da documentação com números não conferidos

- **Problema:** um exemplo de saída no README trazia valores que não
  eram os do arquivo gerado.
- **Causa:** o exemplo foi escrito antes de o arquivo ser lido.
- **Como foi identificado:** ao comparar o exemplo com os valores reais
  impressos pelo programa (451 tokens no arquivo, 483 no exemplo).
- **Solução:** os exemplos passaram a ser preenchidos a partir dos
  arquivos gerados.
- **Resultado:** os exemplos do README correspondem a issues reais,
  identificadas pelo número.
- **Aprendizado:** número em documentação se copia do resultado, não se
  escreve de memória.

## Problema 17 — O `main.py` cresceu demais

- **Problema:** o arquivo chegou a 455 linhas, a maior parte funções de
  impressão.
- **Causa:** cada fase acrescentou um comando e o seu resumo ao mesmo
  arquivo.
- **Como foi identificado:** ao contar as linhas no fim da fase de
  estatísticas.
- **Solução:** a execução das etapas foi para `pipeline.py` e a
  apresentação para `report.py`.
- **Resultado:** o `main.py` ficou com 158 linhas e trata só da
  interface.
- **Aprendizado:** integrar é também o momento de reorganizar.

## Problema 18 — Relatório mais largo que o terminal

- **Problema:** linhas com até 88 colunas, e a quebra automática partia
  itens ao meio ("app" em uma linha, "context" na outra).
- **Causa:** listas de tamanho variável impressas em uma linha só, e uma
  quebra feita por palavra em vez de por item.
- **Como foi identificado:** ao medir a largura da saída da primeira
  execução completa com o Flask.
- **Solução:** a quebra passou a respeitar os itens, e os detalhes
  longos de cada etapa foram para uma linha própria.
- **Resultado:** no máximo 71 colunas nos cinco corpora.
- **Aprendizado:** a apresentação precisa ser testada com dados de
  tamanhos diferentes.

## Problema 19 — Instalação falhava no Python 3.9

- **Problema:** `pip install -r requirements.txt` terminava em erro.
- **Causa:** a versão mais nova do spaCy não tem pacote pronto para o
  Python 3.9, e o pip tentava compilá-la.
- **Como foi identificado:** ao instalar o projeto do zero em um
  ambiente virtual com o Python 3.9.6 do sistema.
- **Solução:** a instalação passou a usar `--only-binary=:all:`, que faz
  o pip escolher uma versão com pacote pronto.
- **Resultado:** os testes passam e a saída é idêntica à do Python 3.14.
- **Aprendizado:** só uma instalação do zero mostra se as instruções
  funcionam em outra máquina.

## Problema 20 — A primeira execução dos testes encontrou um defeito

- **Problema:** 2 dos 103 testes falharam na primeira execução.
- **Causa:** um era defeito do código: a linha divisória de uma tabela
  deixava uma linha em branco que separava o cabeçalho das linhas. O
  outro era erro do teste: a frase de exemplo continha "pay", que tem
  valência negativa legítima.
- **Como foi identificado:** pela própria suíte de testes.
- **Solução:** a Regex do divisor passou a remover também a quebra de
  linha, e a frase do teste foi trocada.
- **Resultado:** todos os testes passam.
- **Aprendizado:** escrever o teste obriga a decidir qual é a saída
  esperada, e isso revela defeitos.

## Problema 21 — Arquivos inesperados derrubavam o programa

- **Problema:** `--file` com uma pasta, ou com um arquivo que não é
  texto, terminava em uma mensagem de erro do Python.
- **Causa:** só o caso "arquivo não encontrado" era tratado.
- **Como foi identificado:** na revisão final, testando as duas entradas.
- **Solução:** erros de leitura e de formato viram uma mensagem clara, e
  os campos de cada issue são conferidos antes da análise.
- **Resultado:** as duas entradas terminam com "Não foi possível ler" ou
  "O arquivo não é uma coleta do DebtRadar".
- **Aprendizado:** tratar o erro esperado não basta; é preciso testar
  entradas absurdas.

## Problema 22 — O token aparecia ao imprimir a configuração

- **Problema:** imprimir o objeto de configuração mostrava o valor do
  `GITHUB_TOKEN`.
- **Causa:** a representação automática da classe inclui todos os
  campos.
- **Como foi identificado:** na revisão de segurança do token.
- **Solução:** o campo foi excluído da representação. O coletor também
  passou a recusar páginas seguintes que não sejam da API do GitHub, já
  que o token vai no cabeçalho de toda requisição.
- **Resultado:** o token não aparece em nenhuma saída nem nos arquivos
  gravados, e há testes para os dois casos.
- **Aprendizado:** segredo não se protege só deixando de imprimi-lo de
  propósito; é preciso fechar os caminhos acidentais.

## Problema 23 — Nome de configuração enganoso

- **Problema:** `MAX_ISSUES` aparecia como "Máx. de issues", mas não era
  um máximo: `--limit` aceitava valores maiores.
- **Causa:** o valor passou a ser só a quantidade sugerida, e o nome não
  acompanhou.
- **Como foi identificado:** na revisão de nomes.
- **Solução:** a variável foi renomeada para `DEFAULT_ISSUES`.
- **Resultado:** o nome descreve o que o valor faz.
- **Aprendizado:** quando o comportamento muda, o nome precisa mudar
  junto.

## Problema 24 — A implementação cobria menos fontes que a proposta

- **Problema:** a proposta do projeto fala em issues, pull requests e
  commits, mas o programa coletava só issues.
- **Causa:** a primeira versão priorizou as issues, e as outras fontes
  não foram retomadas.
- **Como foi identificado:** ao comparar a proposta com o programa pronto,
  antes de preparar a apresentação.
- **Solução:** a opção `--source` passou a coletar pull requests, que a
  API já devolvia na listagem de issues, e mensagens de commit.
- **Resultado:** as três fontes foram testadas com dados reais. No
  VS Code, 16 de 30 issues com a label `debt` têm dívida identificada,
  mas só 3 de 15 pull requests com a mesma label.
- **Aprendizado:** conferir a entrega contra a proposta antes do fim, e
  não só contra o último pedido.

## Problema 25 — Assinaturas do Git nas mensagens de commit

- **Problema:** em 100 commits do VS Code, "Copilot" aparecia 279 vezes
  entre as tecnologias e o verbo "author", 198 vezes.
- **Causa:** as mensagens terminam com linhas `Co-authored-by:`. Havia
  206 delas, 196 creditando o Copilot.
- **Como foi identificado:** os dois números destoavam no primeiro
  resultado da coleta de commits.
- **Solução:** uma Regex remove as assinaturas do Git (`Co-authored-by:`,
  `Signed-off-by:` e semelhantes) no pré-processamento.
- **Resultado:** "Copilot" caiu de 279 para 85 menções, e "author" saiu
  da lista de verbos mais frequentes.
- **Aprendizado:** cada fonte nova tem o seu próprio ruído; a limpeza
  feita para issues não basta para commits.

## Problema 26 — A maior parte de uma coleta era de bots

- **Problema:** no `psf/requests`, 14 dos 24 registros coletados (8
  issues, 8 pull requests e 8 commits) eram de bots.
- **Causa:** o `dependabot` abre pull requests e faz commits de
  atualização de dependências.
- **Como foi identificado:** na primeira coleta das três fontes juntas.
- **Solução:** o filtro de bots, criado para os comentários, já valia
  para o autor de qualquer registro; nada precisou ser alterado.
- **Resultado:** sobraram 10 documentos: 8 issues, 1 pull request e 1
  commit.
- **Aprendizado:** a quantidade pedida não é a quantidade analisada; o
  relatório precisa mostrar as duas.

## Problema 27 — E-mails de terceiros nos dados coletados

- **Problema:** as coletas guardadas traziam endereços de e-mail de
  outras pessoas, e o repositório ia ser publicado.
- **Causa:** os textos do GitHub contêm e-mails, principalmente nas
  linhas `Co-authored-by:` e `Signed-off-by:` das mensagens de commit.
- **Como foi identificado:** em uma varredura dos arquivos antes da
  publicação, que encontrou 89 campos com e-mail.
- **Solução:** o coletor passou a trocar os endereços por um endereço
  fictício, e a mesma regra foi aplicada às coletas já guardadas.
- **Resultado:** nenhum e-mail real nos arquivos, e os nove resumos
  permaneceram idênticos.
- **Aprendizado:** dado público não é dado para republicar; a revisão de
  privacidade vem antes da publicação, e não depois.

## Problema 28 — Coleta vazia sem explicação

- **Problema:** em um ensaio da demonstração, a coleta parou com "Nenhum
  registro encontrado com esses critérios", sem dizer quais critérios.
- **Causa:** quando a label pedida não existe no repositório, a API do
  GitHub devolve uma lista vazia, e não um erro. A própria pergunta do
  programa sugeria a label `debt` como exemplo, e ela existe no
  `microsoft/vscode`, mas não no `psf/requests`.
- **Como foi identificado:** no ensaio de 13/10/2026. A lista vazia foi
  reproduzida com `psf/requests` e a label `debt`: nenhum registro com a
  label, 5 sem ela.
- **Solução:** a mensagem passou a dizer o repositório e a label
  procurados e a indicar a página de labels do repositório. A pergunta
  deixou de sugerir `debt` e avisa que Enter coleta sem label.
- **Resultado:** o erro explica o que fazer, e há um teste para a
  mensagem.
- **Aprendizado:** uma resposta vazia da API não é um erro para ela, mas
  é para o usuário; a mensagem precisa dizer o que foi procurado.

## Problema 29 — O ambiente virtual parou de funcionar ao mover a pasta

- **Problema:** depois que a pasta do projeto mudou de lugar,
  `source .venv/bin/activate` seguido de `python main.py` respondia
  `command not found: python`, e `pytest` falhava com "bad interpreter".
- **Causa:** o ambiente virtual grava o caminho completo da pasta no
  script de ativação e na primeira linha de cada comando instalado.
- **Como foi identificado:** ao ativar o ambiente em um terminal novo.
  No terminal do editor o defeito não aparecia, porque o editor coloca o
  ambiente no caminho de busca por conta própria.
- **Solução:** o `.venv` foi apagado e recriado na pasta nova, com os
  mesmos passos de instalação do README.
- **Resultado:** `python main.py --check` responde "Ambiente pronto" em
  um terminal novo, com as mesmas versões das bibliotecas.
- **Aprendizado:** um ambiente virtual não se move junto com a pasta; e
  "funciona no meu editor" não é o mesmo que "funciona no terminal da
  apresentação".
