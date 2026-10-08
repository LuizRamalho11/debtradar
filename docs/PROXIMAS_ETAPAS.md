# Próximas Etapas

O que a disciplina e a proposta do projeto pedem para as etapas 2 e 3, o
que da etapa 1 pode ser reaproveitado e como organizar o trabalho para
que as três etapas formem um só produto.

**Nada deste documento está implementado.** O que aparece como estrutura
ou como lista de bibliotecas é sugestão, a ser confirmada com o conteúdo
das aulas de cada etapa.

## O que está definido

### Pelas regras da disciplina

| Etapa | Assunto exigido |
|---|---|
| 1ª | Processamento de linguagem natural com `re` e spaCy; coleta por raspagem, rede social ou Web API |
| 2ª | Análise de áudio com módulos Python |
| 3ª | Análise de vídeo com módulos Python |

Valem para todas as etapas:

- no máximo 5 minutos de apresentação por integrante, com o mesmo tempo
  para cada um, sem leitura de anotações;
- sequência da apresentação: tema e teoria, implementação, erros e
  soluções (o diário de bordo, em um slide), programa funcionando com
  todas as opções;
- o arquivo-fonte é mostrado e executado;
- ao menos 50 linhas de código por integrante, ou 30 quando a etapa usa
  tecnologia não apresentada em aula;
- para bibliotecas novas, dizer onde aprender;
- o tema é informado no grupo da disciplina até dois dias antes;
- os slides são entregues em PDF, no padrão `etapaX-DebtRadar.pdf`.

### Pela proposta do projeto

| Etapa | Fonte prevista | Análises previstas |
|---|---|---|
| 2ª, áudio | Podcasts técnicos e entrevistas sobre manutenção, qualidade, dívida técnica e código legado | Duração dos episódios, características acústicas, perfil sonoro e transcrição do conteúdo, para ver quais conceitos de dívida técnica predominam na fala dos profissionais |
| 3ª, vídeo | Palestras e vídeos técnicos sobre dívida técnica | Extração de frames, características visuais (slides, diagramas, trechos de código) e/ou transcrição, para ver como o tema é apresentado visualmente |
| Final | As três modalidades | Um dashboard com tipos de problemas, frequência, tecnologias e características multimodais |

A pergunta de pesquisa é a mesma nas três etapas: como os desenvolvedores
identificam, discutem e priorizam a dívida técnica, e como esse discurso
se manifesta em repositórios, comunidades virtuais e mídias técnicas.

## O que a etapa 1 deixa pronto

### Reaproveitável como está

| Parte | Como serve às próximas etapas |
|---|---|
| Análise de um texto qualquer | `pipeline.explain(texto, settings)` passa uma string pela limpeza, Regex, spaCy, tecnologias, classificação e sentimento. Uma transcrição de áudio ou de vídeo é uma string |
| Formato de registro | Um registro tem título, corpo, autor, datas e comentários. Uma transcrição cabe nele: o título do episódio em `title`, o texto em `body` |
| Análise sem rede | `--file` analisa qualquer arquivo no formato de coleta, venha de onde vier |
| Resumo consolidado | O `..._summary.json` tem a mesma estrutura para qualquer corpus, o que permite comparar texto, áudio e vídeo lado a lado |
| Regras e listas | Os 36 padrões, as 40 tecnologias, o vocabulário dos cinco tipos e os termos neutros valem para qualquer texto em inglês |
| Apoio | `config.py`, `storage.py`, os testes e a forma de tratar erros |

O caminho mais curto para a pergunta de pesquisa nas etapas 2 e 3 é,
portanto, **transcrever e reaproveitar**: o áudio e o vídeo viram texto,
o texto vira uma coleta no formato já existente, e todo o pipeline da
etapa 1 se aplica sem mudança.

### O que não se reaproveita

- A coleta pelo GitHub: as fontes novas são arquivos de áudio e de vídeo.
- As análises próprias de cada modalidade (acústicas, visuais) não
  existem e são o conteúdo novo de cada etapa.
- O relatório de terminal mostra só os blocos da etapa 1.

### Cuidados já aprendidos

Os problemas da etapa 1 que tendem a se repetir com transcrições:

- **Cada fonte tem o seu ruído.** As issues tinham Markdown, os commits
  tinham assinaturas do Git. Transcrições terão vinhetas, anúncios,
  repetições e erros de reconhecimento de termos técnicos.
- **O idioma.** O modelo do spaCy e o léxico de sentimento são para
  inglês. Podcasts em português exigiriam outro modelo, outro
  vocabulário para as regras e outro léxico.
- **Texto falado é diferente de texto escrito.** O vocabulário das regras
  veio de issues. Vale medir, antes de confiar, quanto dele aparece na
  fala.
- **Sentimento em textos longos.** A média por sentença já resolve a
  saturação, mas uma transcrição sem pontuação não tem sentenças; a
  divisão precisará de outro critério.
- **Medir antes de ajustar.** Toda regra da etapa 1 foi conferida nos
  dados, e as hipóteses que não se confirmaram foram descartadas.

## Estrutura sugerida

Hoje os módulos estão todos em `src/`, e todos tratam de texto. Para as
próximas etapas, a sugestão é dar a cada modalidade a sua pasta, sem
mover o que já existe enquanto não for preciso:

```text
src/
├── (módulos atuais da etapa 1, sem alteração)
├── audio/                      # etapa 2
│   ├── audio_collector.py      # obter e organizar os arquivos de áudio
│   ├── audio_features.py       # duração e características acústicas
│   └── transcriber.py          # áudio -> texto, no formato de registro
└── video/                      # etapa 3
    ├── video_collector.py
    ├── frame_extractor.py      # frames e características visuais
    └── transcriber.py
data/
├── raw/        coletas de texto (como hoje)
├── audio/      arquivos de áudio e suas transcrições
├── video/      arquivos de vídeo, frames e transcrições
├── processed/  documentos analisados, de qualquer modalidade
└── results/    resumos, de qualquer modalidade
docs/
├── etapa1/
├── etapa2/     diário de bordo, documentação acadêmica e apresentação
└── etapa3/
```

Pontos a decidir no início da etapa 2:

- **Arquivos grandes.** Áudio e vídeo não devem ir para o repositório
  git. O `.gitignore` precisa excluí-los, e o que fica versionado são as
  transcrições e as características extraídas.
- **Um campo para a modalidade.** Os registros já têm `type`
  (`issue`, `pull_request`, `commit`). Um valor novo, como
  `audio_transcript`, permite que o resumo conte por modalidade sem
  outra mudança: basta incluí-lo em `TYPE_NAMES`.
- **Onde fica a interface.** O `main.py` pode ganhar opções para as
  novas modalidades, ou cada etapa pode ter o seu ponto de entrada. As
  regras pedem "o programa funcionando com todas as suas opções".
- **Características que não são texto.** Duração, medidas acústicas e
  frames não cabem no documento de texto. Elas precisam de um formato
  próprio, a ser descrito em `FORMATO_DOS_DADOS.md`.

## Bibliotecas

As regras dizem "módulos Python" para áudio e para vídeo, sem nomear
quais; os módulos apresentados em aula têm prioridade, e bibliotecas
fora das aulas reduzem a exigência de linhas de código, mas pedem a
indicação de onde aprender.

Nenhuma biblioteca de áudio ou de vídeo foi instalada ou testada neste
projeto. Antes de escolher, vale conferir se ela instala na versão do
Python em uso: a etapa 1 mostrou que isso não é garantido (o spaCy mais
novo não tinha pacote pronto para o Python 3.9).

## Pendências que seguem da etapa 1

| Pendência | Por que importa nas próximas etapas |
|---|---|
| Token do GitHub ainda não configurado | Só afeta novas coletas de texto |
| Sem gabarito do tipo de dívida | A classificação das transcrições herdará a mesma incerteza; uma amostra rotulada à mão serviria às três etapas |
| A classificação não distingue assunto de problema | Em fala, onde o vocabulário se repete mais, o efeito pode ser maior |
| NER pouco confiável em texto técnico | As tecnologias continuam vindo da lista do projeto |
| Amostras pequenas | Vale decidir cedo o tamanho do corpus de áudio e de vídeo |
| Documentação dos repositórios, BugRepo e raspagem de páginas | Citados na proposta para o texto e não implementados |
| Sem visualização gráfica | O dashboard final precisará de uma biblioteca; hoje o projeto não tem nenhuma |

## Como começar a etapa 2

1. Reler as regras da disciplina e a parte de áudio da proposta.
2. Confirmar com as aulas quais módulos de áudio serão usados.
3. Decidir as fontes: quais podcasts, quantos episódios, em que idioma.
4. Criar `docs/etapa2/` com um diário de bordo desde o primeiro dia,
   registrando só problemas que de fato acontecerem.
5. Criar um ramo `etapa2` no git e marcar o estado atual com
   `git tag etapa1`.
6. Fazer primeiro o caminho inteiro com um único arquivo de áudio:
   obter, extrair características, transcrever, gerar o registro e
   passar pelo pipeline com `--file`.
7. Só então ampliar o corpus e ajustar regras, sempre conferindo nos
   dados.
8. Manter o padrão da etapa 1: testes sem rede, números da documentação
   copiados de arquivos gerados, e limitações escritas em vez de
   escondidas.
