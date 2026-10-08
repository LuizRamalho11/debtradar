# Checklist da Apresentação — DebtRadar (1ª etapa)

Os itens marcados com `[x]` foram verificados em 08/10/2026 na máquina
de desenvolvimento. Os demais dependem dos integrantes.

## Programa

- [x] **Código funcionando.** O pipeline roda de ponta a ponta nas nove
  coletas salvas em `data/raw/`, com issues, pull requests e commits.
- [x] **Programa testado.** `python -m pytest` termina com
  `118 passed`.
- [x] **Dependências instaladas** nesta máquina (`python main.py --check`
  responde "Ambiente pronto").
- [ ] **Dependências instaladas na máquina da apresentação**, se for
  outra, e na do segundo integrante. Seguir a seção "Instalação" do
  README e rodar `python main.py --check`.
- [ ] **GitHub Token configurado.** O arquivo `.env` já existe, com a
  linha `GITHUB_TOKEN=` vazia; falta colar o token. A demonstração
  funciona sem ele; o token só amplia o limite de 60 para 5000
  requisições por hora. O passo a passo está no README.
- [ ] **Coleta com token testada**, caso o token seja configurado. Esse
  caminho nunca foi exercitado com um token real.

## Documentação

- [x] **README atualizado.**
- [x] **Diário de bordo atualizado** (`DIARIO_DE_BORDO.md`, 27 problemas).
- [x] **Documentação acadêmica** (`DOCUMENTACAO_ACADEMICA.md`).
- [x] **Guia da apresentação** (`GUIA_APRESENTACAO.md`) e **estrutura dos
  slides** (`ESTRUTURA_SLIDES.md`).

## Slides e entrega

- [x] **Slides preparados**, seguindo `ESTRUTURA_SLIDES.md`: 12 slides em
  https://claude.ai/artifact/W2tHprsQx3iEGwcJaSpZ8v (link privado da
  conta que os criou; para o outro integrante abrir, compartilhar pelo
  menu Share da página).
- [ ] **Slides revisados pelos dois integrantes** e ajustados ao jeito de
  falar de cada um.
- [ ] **Números dos slides conferidos** contra a saída de
  `python main.py --file data/raw/microsoft_vscode_debt_issues.json`.
- [ ] **Diário de bordo em um slide**, com três problemas escolhidos.
- [ ] **Arquivo PDF preparado**, baixado da página dos slides.
- [ ] **Nome do arquivo conforme a regra da disciplina:**
  `etapa1-DebtRadar.pdf`.
- [ ] **PDF submetido no SIGAA** na data determinada.
- [ ] **Tema informado no grupo de WhatsApp da disciplina** até dois dias
  antes da apresentação.
- [ ] **Data da apresentação conferida no SIGAA.**

## Ensaio

- [ ] **Demonstração ensaiada**, com e sem internet (plano B do guia).
- [ ] **Cada integrante sabe a sua parte** e fala sem ler os slides.
- [ ] **Tempo cronometrado:** 5 minutos para cada um, 10 no total.
- [ ] **Cada integrante sabe abrir e explicar os seus trechos de
  código** (tabela "Código" do guia).
- [ ] **Perguntas do guia respondidas em voz alta** ao menos uma vez.

## No dia

- [ ] Terminal aberto na pasta do projeto, com o ambiente ativado.
- [ ] Fonte do terminal e do editor grande; janela com 80 colunas ou
  mais.
- [ ] Arquivos de código abertos em abas, na ordem do roteiro.
- [ ] `python main.py --check` executado minutos antes.
- [ ] Cota da API conferida, se for usar a coleta ao vivo: cada coleta
  de 5 issues gasta cerca de 6 requisições.
- [ ] Captura de tela da saída guardada como reserva.
- [ ] Nenhuma cola em mãos; os dois presentes do começo ao fim da aula.

## Requisitos da disciplina já atendidos pelo código

- [x] Coleta por Web API (GitHub REST API).
- [x] Processamento de linguagem natural com `re` e spaCy.
- [x] Mais de 50 linhas de código por integrante: o projeto tem 2.132
  linhas em `main.py` e `src/`, sem contar os testes.
- [x] O programa pode ser mostrado e executado no interpretador.
