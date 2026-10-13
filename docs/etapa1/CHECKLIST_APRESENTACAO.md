# Checklist da Apresentação — DebtRadar (1ª etapa)

Apresentação em **14/10/2026** (era 08/10/2026 e foi adiada). Os itens
marcados com `[x]` foram verificados em 13/10/2026 na máquina de
desenvolvimento. Os demais dependem dos integrantes.

Quem fala o quê: **Luy** é o primeiro a falar (slides 1 a 6 e 10);
**Luiz** fica com os slides 7 a 9, a demonstração e o encerramento.

## Programa

- [x] **Código funcionando.** O pipeline roda de ponta a ponta nas nove
  coletas salvas em `data/raw/`, com issues, pull requests e commits, e
  os nove resumos saem idênticos aos guardados.
- [x] **Programa testado.** `python -m pytest` termina com
  `119 passed`.
- [x] **Ambiente recriado depois da mudança de pasta.** Em um terminal
  novo, `source .venv/bin/activate` e `python main.py --check` respondem
  "Ambiente pronto".
- [x] **Coleta ao vivo testada** em 13/10/2026, sem token: os dois
  comandos da demonstração que usam a rede funcionaram (ver o guia).
- [ ] **Dependências instaladas na máquina da apresentação**, se for
  outra, e na do Luy. Seguir a seção "Instalação" do README e rodar
  `python main.py --check`.
- [ ] **GitHub Token configurado.** O arquivo `.env` já existe, com a
  linha `GITHUB_TOKEN=` vazia; falta colar o token. Sem ele o limite é
  de 60 requisições por hora **por endereço IP**: na rede da faculdade a
  cota pode ser gasta por outras pessoas. O passo a passo está no
  README.
- [ ] **Coleta com token testada**, caso o token seja configurado. Esse
  caminho nunca foi exercitado com um token real.

## Documentação

- [x] **README atualizado.**
- [x] **Diário de bordo atualizado** (`DIARIO_DE_BORDO.md`, 29 problemas).
- [x] **Documentação acadêmica** (`DOCUMENTACAO_ACADEMICA.md`), com as
  referências.
- [x] **Guia da apresentação** (`GUIA_APRESENTACAO.md`) e **estrutura dos
  slides** (`ESTRUTURA_SLIDES.md`), com os nomes de quem fala.

## Slides e entrega

- [x] **Slides preparados**, conforme `ESTRUTURA_SLIDES.md`: 12 slides em
  https://claude.ai/artifact/W2tHprsQx3iEGwcJaSpZ8v (link privado da
  conta do Luiz; para o Luy abrir, compartilhar pelo menu Share da
  página).
- [x] **Números dos slides conferidos** contra os dados em 13/10/2026.
- [x] **Diário de bordo em um slide**, com três problemas (slide 10).
- [ ] **Slides compartilhados com o Luy** e revisados pelos dois.
- [ ] **Arquivo PDF exportado de novo**, pela página dos slides. Os
  slides 5 e 11 e as anotações mudaram em 13/10/2026; um PDF baixado
  antes disso está desatualizado.
- [ ] **Nome do arquivo conforme a regra da disciplina:**
  `etapa1-DebtRadar.pdf`.
- [ ] **PDF submetido no SIGAA** na data determinada.
- [x] **Tema informado no grupo de WhatsApp da disciplina** (confirmado
  pelo Luiz em 13/10/2026).
- [ ] **Data da apresentação conferida no SIGAA.**

## Ensaio

- [ ] **Demonstração ensaiada**, com e sem internet (plano B do guia).
  Na pergunta da label, só Enter.
- [ ] **`git checkout -- data` depois de cada ensaio**, para as coletas
  versionadas voltarem ao estado dos slides.
- [ ] **Cada integrante sabe a sua parte** e fala sem ler os slides.
- [ ] **Tempo cronometrado:** 5 minutos para cada um, 10 no total; a
  demonstração em 1:40.
- [ ] **Cada integrante sabe abrir e explicar os seus trechos de
  código** (tabela "Código" do guia).
- [ ] **Perguntas do guia respondidas em voz alta** ao menos uma vez.

## No dia

- [ ] Terminal aberto na pasta do projeto, com o ambiente ativado.
- [ ] Fonte do terminal e do editor grande; janela com 80 colunas ou
  mais.
- [ ] Arquivos de código abertos em abas, na ordem do roteiro.
- [ ] `python main.py --check` executado minutos antes.
- [ ] Os cinco comandos da demonstração já no histórico do terminal.
- [ ] Cota da API conferida, se for usar a coleta ao vivo: a
  demonstração gasta cerca de 8 requisições.
- [ ] Captura de tela da saída guardada como reserva.
- [ ] Nenhuma cola em mãos; os dois presentes do começo ao fim da aula.

## Requisitos da disciplina já atendidos pelo código

- [x] Coleta por Web API (GitHub REST API).
- [x] Processamento de linguagem natural com `re` e spaCy.
- [x] Mais de 50 linhas de código por integrante: o projeto tem 2.145
  linhas em `main.py` e `src/`, sem contar os testes.
- [x] O programa pode ser mostrado e executado no interpretador.
- [x] A demonstração usa todas as opções do programa: modo interativo,
  `--owner`, `--repo`, `--limit`, `--label`, `--source`, `--file`,
  `--text` e `--check`.
