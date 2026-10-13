# Etapa 1 — Texto

Material da primeira etapa do DebtRadar: análise de textos do GitHub com
expressões regulares e spaCy. A documentação que vale para todas as
etapas está na [pasta acima](../README.md).

## Documentos desta etapa

| Documento | Para quê |
|---|---|
| [RESULTADOS.md](RESULTADOS.md) | Todos os números obtidos com dados reais, coleta por coleta. Gerado a partir dos resumos |
| [DOCUMENTACAO_ACADEMICA.md](DOCUMENTACAO_ACADEMICA.md) | Por que cada técnica foi usada e como funciona: Regex, spaCy, GitHub API, classificação, sentimento e limitações |
| [DIARIO_DE_BORDO.md](DIARIO_DE_BORDO.md) | Os 29 problemas encontrados durante o desenvolvimento, com causa, solução e aprendizado |
| [GUIA_APRESENTACAO.md](GUIA_APRESENTACAO.md) | Roteiro de 10 minutos para Luy e Luiz, demonstração com todas as opções, trechos de código e perguntas prováveis |
| [ESTRUTURA_SLIDES.md](ESTRUTURA_SLIDES.md) | O conteúdo de cada um dos 12 slides |
| [CHECKLIST_APRESENTACAO.md](CHECKLIST_APRESENTACAO.md) | O que conferir antes de apresentar |

## O que a etapa entregou

- Coleta de issues, pull requests e commits pela API REST do GitHub.
- Limpeza do Markdown, com 22 expressões regulares.
- Detecção de dívida técnica com 36 padrões de Regex.
- Análise linguística com spaCy: tokens, lemas, classes gramaticais,
  expressões nominais e entidades.
- Identificação de tecnologias por uma lista própria, com 40 nomes.
- Classificação por regras em cinco tipos de dívida.
- Sentimento com VADER, por sentença.
- Estatísticas: frequências, contagens por fonte, evolução temporal e
  indicador de resolução.
- 119 testes automatizados, sem acesso à rede.
- Nove coletas reais, de cinco repositórios, guardadas em `data/`.

## Resultado em uma linha

Das 57 issues que os mantenedores de três repositórios rotularam como
dívida, limpeza ou refatoração, o programa identifica 29; em um grupo de
controle com a label `bug`, 1 de 9. Os números completos estão em
[RESULTADOS.md](RESULTADOS.md).

## Como o trabalho foi conduzido

A etapa foi desenvolvida em fases curtas, cada uma testada com dados
reais antes da seguinte.

| Fase | O que foi feito |
|---|---|
| 0. Auditoria | Levantamento do ambiente e plano; a pasta só tinha a proposta e as regras |
| 1. Fundação | Estrutura do projeto, dependências, configuração pelo `.env` e ponto de entrada |
| 2. Coleta | Coletor de issues pela API, com paginação e tratamento de erros |
| 3. Limpeza e Regex | Pré-processamento do Markdown e padrões de dívida técnica |
| 4. spaCy | Tokens, lemas, entidades e a lista própria de tecnologias |
| 5. Análises | Classificação por regras, sentimento e estatísticas |
| 6. Integração | Um só comando executa todas as etapas e mostra o relatório |
| 7. Revisão | Testes dos cenários de erro, revisão do código, README, diário de bordo e documentação acadêmica |
| 8. Apresentação | Roteiro, estrutura dos slides e checklist |
| Varredura | Correção dos problemas acumulados e criação dos testes automatizados |
| Fechamento | Pull requests e commits como fontes, indicador de resolução, opção `--text`, slides e publicação |
| Revisão final | Ambiente recriado depois da mudança de pasta, mensagem da coleta vazia, demonstração com todas as opções, referências |

Os problemas de cada fase estão no
[diário de bordo](DIARIO_DE_BORDO.md), e as escolhas de projeto, em
[../DECISOES.md](../DECISOES.md).

## Para reproduzir os resultados

```bash
python main.py --file data/raw/microsoft_vscode_debt_issues.json
python tools/gerar_resultados.py
python -m pytest
```

O primeiro comando refaz a análise do corpus principal sem usar a rede; o
segundo regenera o documento de resultados; o terceiro roda os testes.

## Pendências desta etapa

A apresentação, marcada para 08/10/2026, passou para 14/10/2026. O que
falta depende dos integrantes e está em
[CHECKLIST_APRESENTACAO.md](CHECKLIST_APRESENTACAO.md):

- Configurar o token do GitHub e exercitar uma coleta autenticada.
- Exportar os slides em PDF como `etapa1-DebtRadar.pdf` e submeter no
  SIGAA.
- Ensaiar a apresentação, com cronômetro.

As pendências técnicas que seguem para as próximas etapas estão em
[../PROXIMAS_ETAPAS.md](../PROXIMAS_ETAPAS.md).
