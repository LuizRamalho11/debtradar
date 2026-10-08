# Registro de Decisões

As decisões de projeto que moldaram o DebtRadar, com o motivo de cada uma
e a evidência que a sustentou. Serve para duas coisas: explicar por que o
código é como é, e evitar que uma etapa futura desfaça, sem saber, algo
que foi decidido de propósito.

Cada entrada tem o contexto, o que foi decidido, o que foi considerado no
lugar e a evidência. Os números vêm de execuções reais sobre dados do
GitHub; os problemas que levaram a muitas dessas decisões estão contados
em [etapa1/DIARIO_DE_BORDO.md](etapa1/DIARIO_DE_BORDO.md).

## Índice

| Nº | Decisão | Área |
|---|---|---|
| D01 | Corpus em inglês | Dados |
| D02 | Web API em vez de raspagem de páginas | Coleta |
| D03 | Coleta gravada em disco, análise separada | Arquitetura |
| D04 | Issues, pull requests e commits em um formato único | Coleta |
| D05 | Textos de bots ficam de fora | Dados |
| D06 | Blocos de código são separados, não apagados | Limpeza |
| D07 | A caixa do texto é preservada | Limpeza |
| D08 | Padrões explícitos e padrões de contexto | Regex |
| D09 | Marcadores de comentário exigem maiúsculas ou sintaxe | Regex |
| D10 | Cada trecho do texto conta uma vez | Regex |
| D11 | Tecnologias por lista própria, não pelo NER | spaCy |
| D12 | Modelo pequeno do spaCy | spaCy |
| D13 | Só substantivos, adjetivos e verbos nas frequências | spaCy |
| D14 | Classificação por regras, com três resultados | Classificação |
| D15 | Três ocorrências confirmam um tipo | Classificação |
| D16 | "Dívida identificada" é a união de dois critérios | Classificação |
| D17 | VADER por sentença, com léxico ajustado | Sentimento |
| D18 | O fechamento de issues é indício, não medida | Estatísticas |
| D19 | O relatório lê só o resumo | Arquitetura |
| D20 | Sem pandas e sem gráficos | Dependências |
| D21 | Testes sem rede | Testes |
| D22 | Código em inglês, textos em português | Convenções |
| D23 | Nomes de arquivo com todos os parâmetros, e cópia de segurança | Dados |
| D24 | E-mails mascarados na coleta | Dados |

## D01 — Corpus em inglês

- **Contexto:** a proposta e a apresentação são em português, mas as
  issues do GitHub são majoritariamente em inglês.
- **Decisão:** analisar textos em inglês, com o modelo `en_core_web_sm` e
  um léxico de sentimento para inglês. A documentação é em português.
- **Alternativa:** restringir a coleta a repositórios em português, o que
  reduziria muito os dados disponíveis.
- **Consequência:** o programa não serve para textos em outros idiomas
  sem trocar o modelo, o vocabulário das regras e o léxico.

## D02 — Web API em vez de raspagem de páginas

- **Contexto:** as regras da etapa aceitam raspagem com BeautifulSoup,
  dados de rede social ou Web API. A proposta citava a API e a raspagem.
- **Decisão:** usar só a API REST do GitHub.
- **Motivo:** a API entrega os campos prontos (datas, autor, labels,
  estado), informa a cota e a próxima página nos cabeçalhos, e não quebra
  quando o site muda de aparência.
- **Consequência:** a raspagem e o BugRepo, citados na proposta, não
  foram implementados. Isso precisa ser dito na apresentação.

## D03 — Coleta gravada em disco, análise separada

- **Contexto:** sem token, a API permite 60 requisições por hora, e a
  demonstração é ao vivo.
- **Decisão:** a coleta é gravada em `data/raw/` assim que termina, e a
  opção `--file` refaz toda a análise a partir do arquivo.
- **Evidência:** todas as rodadas de ajuste das regras foram feitas sem
  gastar cota. A análise de 30 issues leva cerca de dois segundos.
- **Consequência:** a demonstração não depende de internet.

## D04 — Issues, pull requests e commits em um formato único

- **Contexto:** a proposta fala nas três fontes; a primeira versão só
  coletava issues.
- **Decisão:** as três fontes viram o mesmo formato de registro, com o
  campo `type`. Um commit é tratado como um registro cujo título é a
  primeira linha da mensagem, sem estado, labels nem comentários.
- **Alternativa:** um pipeline para cada fonte, o que triplicaria o
  código das etapas seguintes.
- **Evidência:** nenhuma etapa de análise precisou ser alterada para
  aceitar as fontes novas; só a coleta e a limpeza.
- **Consequência:** a lista de registros continua se chamando `issues`
  nos arquivos, para as coletas antigas seguirem válidas.

## D05 — Textos de bots ficam de fora

- **Contexto:** a pergunta de pesquisa é sobre como desenvolvedores
  discutem a dívida técnica.
- **Decisão:** registros e comentários de contas terminadas em `[bot]`,
  ou listadas em `KNOWN_BOTS`, são ignorados.
- **Evidência:** em um corpus do VS Code, 13 de 16 comentários e 11 de 20
  issues eram de um bot. No `psf/requests`, 14 de 24 registros eram do
  `dependabot`.
- **Consequência:** o relatório mostra os registros coletados e os
  analisados, porque os dois números diferem.

## D06 — Blocos de código são separados, não apagados

- **Contexto:** código dentro de uma issue atrapalha a análise
  linguística, mas pode conter `TODO` e `FIXME`.
- **Decisão:** os blocos vão para o campo `code`, onde só os quatro
  marcadores de comentário são procurados.
- **Alternativa:** apagar o código (perde os marcadores) ou deixá-lo no
  texto (polui lemas e entidades com logs e identificadores).

## D07 — A caixa do texto é preservada

- **Decisão:** a limpeza não converte o texto para minúsculas.
- **Motivo:** as Regex já ignoram a caixa quando convém, e o spaCy
  precisa dela para reconhecer nomes próprios. Além disso, em marcadores
  de código a caixa é informação (ver D09).

## D08 — Padrões explícitos e padrões de contexto

- **Contexto:** palavras como "documentation" e "unit test" aparecem em
  qualquer issue, com ou sem dívida.
- **Decisão:** cada padrão é explícito (por si só indica dívida, como
  "code smell") ou de contexto (só indica o assunto). Apenas os
  explícitos ligam `technical_debt_detected`.
- **Alternativa:** tratar todo padrão como sinal de dívida, o que
  marcaria quase toda issue.
- **Evidência:** no corpus de controle, com a label `bug`, 1 de 9 issues
  é marcada.

## D09 — Marcadores de comentário exigem maiúsculas ou sintaxe

- **Contexto:** a busca ignorava maiúsculas e minúsculas em tudo.
- **Decisão:** `TODO`, `FIXME` e `XXX` valem em maiúsculas; em
  minúsculas, só com sintaxe de marcador (`todo:`, `todo(fulano)`).
  Nenhum marcador é contado dentro de um caminho de arquivo. `HACK`
  continua valendo em qualquer caixa, porque "hacky" é vocabulário comum.
- **Evidência:** no VS Code, 4 das 5 ocorrências de "todo" eram o nome de
  um recurso do produto. No Kubernetes, as 6 ocorrências de "hack" eram
  a pasta `hack/`.
- **Atenção:** isso contraria a regra de "ignorar maiúsculas" pedida no
  início do projeto, para esses três marcadores. A função
  `comment_marker` concentra a regra, caso seja preciso reverter.

## D10 — Cada trecho do texto conta uma vez

- **Decisão:** os padrões são aplicados em ordem, e um trecho já contado
  não conta de novo. Expressões específicas vêm antes das genéricas.
- **Exemplo:** "missing documentation" conta como `missing_documentation`
  e não também como `documentation`; "technical debt" não conta também
  como `debt`.

## D11 — Tecnologias por lista própria, não pelo NER

- **Contexto:** o NER do spaCy não foi treinado com texto técnico.
- **Decisão:** as tecnologias vêm de um dicionário do projeto
  (`TECHNOLOGIES`), procurado com o `PhraseMatcher`. As duas listas
  aparecem separadas no resultado.
- **Evidência:** no corpus principal, a lista encontrou 20 menções a
  Copilot e o NER, 12. O NER rotulou `Linux` como lugar e `Claude` como
  pessoa.
- **Consequência:** uma tecnologia que não está na lista não é
  encontrada. A lista foi feita para ser fácil de ampliar.

## D12 — Modelo pequeno do spaCy

- **Decisão:** manter o `en_core_web_sm`.
- **Alternativa testada:** o `en_core_web_md`. Não melhorou as
  entidades: passou a rotular "Host" e "npm" como pessoa e a reconhecer
  menos "VS Code".
- **Consequência:** o modelo é configurável por `SPACY_MODEL`, mas não
  há ganho conhecido em trocá-lo.

## D13 — Só substantivos, adjetivos e verbos nas frequências

- **Decisão:** entram nas frequências os tokens alfabéticos, com três
  letras ou mais, que não são stopwords nem identificadores de código, e
  só dessas três classes gramaticais. Nomes próprios ficam de fora,
  porque já aparecem nas entidades e nas tecnologias.
- **Limite conhecido:** o modelo erra a classe de alguns termos técnicos
  ("token" e "terminal" saem como adjetivos) e o lema de palavras raras
  ("pandas" vira "panda").

## D14 — Classificação por regras, com três resultados

- **Contexto:** não há dados rotulados por tipo de dívida para treinar
  um modelo.
- **Decisão:** um baseline de regras, com `yes`, `possible` e `no` para
  cada um dos cinco tipos, e a evidência de cada decisão gravada junto.
- **Motivo:** é explicável, e a evidência permite conferir cada caso. Foi
  assim que se descobriu que "deprecated" não deveria contar como dívida
  de dependências.
- **Consequência:** o programa não aprende com os dados e não deve ser
  apresentado como Machine Learning.

## D15 — Três ocorrências confirmam um tipo

- **Decisão:** sem padrão explícito, um tipo é `yes` quando o vocabulário
  do tema aparece três vezes ou mais.
- **Alternativa testada:** exigir dois termos diferentes. Foi descartada:
  derrubava 5 acertos claros (como "Stale repos" em dependências) para
  remover 4 casos duvidosos.
- **Limite conhecido:** repetir um termo ambíguo, como `test`, basta
  para confirmar a categoria.

## D16 — "Dívida identificada" é a união de dois critérios

- **Decisão:** um documento tem dívida identificada se tem um padrão
  explícito da Regex **ou** ao menos um tipo `yes`. A função `has_debt`
  é a única definição, usada em todo o projeto.
- **Evidência:** no corpus principal, 11 issues atendem ao primeiro
  critério e 13 ao segundo; a união dá 16 de 30.
- **Atenção:** o segundo critério identifica o assunto, não
  necessariamente um problema. O número não é acurácia.

## D17 — VADER por sentença, com léxico ajustado

- **Decisão:** o sentimento é a média do `compound` das sentenças, e 37
  termos técnicos, mais a palavra "no", têm a valência removida.
- **Evidência:** aplicado ao documento inteiro, o VADER deixava 11 de 30
  documentos acima de 0,9 em módulo. No léxico original, "shared" somava
  +95 pontos em 68 ocorrências.
- **Consequência:** o sentimento é uma característica complementar. Ele
  não entra na classificação.

## D18 — O fechamento de issues é indício, não medida

- **Contexto:** a pergunta de pesquisa fala em priorização, e o GitHub
  não tem um campo de prioridade.
- **Decisão:** o resumo compara, para issues e pull requests com e sem
  dívida, quantos foram fechados e a mediana de dias até fechar.
- **Evidência:** no VS Code a mediana foi de 1,3 dia com dívida e 4,0
  sem; no pandas, 666 e 108. O padrão não se repete.
- **Consequência:** o resultado é apresentado como indício, sem
  conclusão geral.

## D19 — O relatório lê só o resumo

- **Decisão:** `report.py` não recebe os documentos, apenas o resumo
  consolidado.
- **Motivo:** tudo o que aparece na tela fica também em um arquivo, e uma
  interface futura pode ler o mesmo arquivo.

## D20 — Sem pandas e sem gráficos

- **Decisão:** as estatísticas usam só a biblioteca padrão, e o
  resultado é mostrado em texto, com barras de caracteres.
- **Motivo:** as contagens são simples, e `pandas` e `matplotlib`
  ficaram sem uso depois de planejados; saíram do `requirements.txt`.
- **Consequência:** o dashboard da etapa final precisará escolher a sua
  própria biblioteca de visualização.

## D21 — Testes sem rede

- **Decisão:** os testes automatizados não acessam a API. A coleta é
  testada com respostas simuladas, e o pipeline com uma coleta pequena
  escrita para o teste.
- **Motivo:** os testes precisam passar sempre, em menos de um segundo, e
  sem gastar cota.
- **Complemento:** o comportamento com dados reais foi conferido à parte,
  nas coletas guardadas em `data/`.

## D22 — Código em inglês, textos em português

- **Decisão:** nomes de arquivos, funções, variáveis e chaves dos
  arquivos de dados em inglês; docstrings, comentários, mensagens ao
  usuário e documentação em português.
- **Motivo:** os nomes seguem o padrão sugerido para a estrutura do
  projeto, e os textos seguem o idioma da apresentação.

## D23 — Nomes de arquivo com todos os parâmetros, e cópia de segurança

- **Decisão:** o nome do arquivo de coleta traz owner, repositório,
  label e fonte. Ao repetir uma coleta, a anterior vai para
  `data/raw/backup/`.
- **Motivo:** uma coleta sem label quase apagou a coleta com a label
  `debt` do mesmo repositório, e uma coleta degradada pelo limite da API
  poderia substituir uma completa na véspera da apresentação.

## D24 — E-mails mascarados na coleta

- **Contexto:** as coletas ficam no repositório, que é público, e os
  textos do GitHub às vezes trazem endereços de e-mail, sobretudo nas
  assinaturas das mensagens de commit.
- **Decisão:** o coletor troca todo endereço de e-mail por
  `redacted@example.com` antes de gravar.
- **Motivo:** os endereços não servem à análise, e republicá-los não tem
  justificativa.
- **Evidência:** as nove coletas guardadas tinham 89 campos com e-mail,
  quase todos nos commits. Depois da máscara, os nove resumos ficaram
  idênticos, porque o substituto continua sendo um token só para o spaCy.
- **Consequência:** `data/raw/` não é mais uma cópia fiel da resposta da
  API nesse ponto. Logins de usuário, que são identificadores públicos do
  GitHub, continuam nos dados.
