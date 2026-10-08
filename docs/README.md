# Documentação do DebtRadar

Índice de toda a documentação do projeto. A parte geral vale para todas
as etapas; cada etapa da disciplina tem a sua própria pasta.

Para instalar e rodar o programa, comece pelo [README](../README.md) da
raiz.

## Por onde começar

| Eu quero… | Leia |
|---|---|
| Rodar o programa pela primeira vez | [README](../README.md) |
| Entender como o programa está organizado | [ARQUITETURA.md](ARQUITETURA.md) |
| Saber o que faz uma função ou constante | [REFERENCIA_MODULOS.md](REFERENCIA_MODULOS.md) |
| Ler os arquivos que o programa gera | [FORMATO_DOS_DADOS.md](FORMATO_DOS_DADOS.md) |
| Entender por que algo foi feito de certo jeito | [DECISOES.md](DECISOES.md) |
| Alterar o código sem quebrar nada | [GUIA_DE_DESENVOLVIMENTO.md](GUIA_DE_DESENVOLVIMENTO.md) |
| Começar a etapa 2 ou a 3 | [PROXIMAS_ETAPAS.md](PROXIMAS_ETAPAS.md) |
| Ver os resultados obtidos com dados reais | [etapa1/RESULTADOS.md](etapa1/RESULTADOS.md) |
| Preparar ou rever a apresentação da etapa 1 | [etapa1/](etapa1/README.md) |

## Documentação geral

| Documento | Conteúdo | Atualizar quando |
|---|---|---|
| [ARQUITETURA.md](ARQUITETURA.md) | Camadas, pipeline, fluxo dos dados, dependências entre módulos, tratamento de erros, pontos de extensão | Um módulo for criado ou mudar de papel |
| [REFERENCIA_MODULOS.md](REFERENCIA_MODULOS.md) | Um capítulo por arquivo de código: papel, constantes, funções e classes, com números de linha | Qualquer mudança no código; é gerado por `python tools/gerar_referencia.py` |
| [FORMATO_DOS_DADOS.md](FORMATO_DOS_DADOS.md) | Nome dos arquivos e significado de cada campo da coleta, dos documentos e do resumo, com exemplos reais | Um campo for criado, renomeado ou removido |
| [DECISOES.md](DECISOES.md) | 24 decisões de projeto, com contexto, alternativas e evidência | Uma escolha de projeto for feita ou revista |
| [GUIA_DE_DESENVOLVIMENTO.md](GUIA_DE_DESENVOLVIMENTO.md) | Ambiente, comandos, testes, convenções, receitas de alteração, controle de versão, problemas comuns | O jeito de trabalhar mudar |
| [PROXIMAS_ETAPAS.md](PROXIMAS_ETAPAS.md) | O que as etapas 2 e 3 pedem, o que se reaproveita, estrutura sugerida, pendências | Uma etapa começar ou terminar |

## Documentação por etapa

| Etapa | Assunto | Situação | Pasta |
|---|---|---|---|
| 1ª | Texto: GitHub API, Regex e spaCy | Concluída | [etapa1/](etapa1/README.md) |
| 2ª | Áudio | Não iniciada | — |
| 3ª | Vídeo | Não iniciada | — |

Cada pasta de etapa reúne o que é próprio dela: resultados, documentação
acadêmica, diário de bordo e material da apresentação. A sugestão é
repetir a mesma estrutura em `etapa2/` e `etapa3/`.

## Como manter esta documentação

- **Dois documentos são gerados, e não editados à mão:**
  `REFERENCIA_MODULOS.md` (`python tools/gerar_referencia.py`) e
  `etapa1/RESULTADOS.md` (`python tools/gerar_resultados.py`).
- **Números vêm de arquivos gerados.** Qualquer valor citado em um
  documento deve poder ser refeito com um comando.
- **O diário de bordo registra só o que aconteceu.** Problemas previstos
  que não se confirmaram ficam de fora.
- **Limitações são escritas.** O que o programa não faz aparece nos
  documentos, junto com o que ele faz.
- **Os links são relativos**, para funcionarem tanto no GitHub quanto no
  editor.
