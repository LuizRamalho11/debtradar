# Resultados da Etapa 1

Resultados do DebtRadar sobre todas as coletas reais guardadas em
`data/`. Este arquivo é gerado por `python tools/gerar_resultados.py`
a partir dos resumos em `data/results/`; não deve ser editado à mão.

Para refazer qualquer linha, reanalise a coleta correspondente:

```bash
python main.py --file data/raw/<arquivo>
```

## Coletas

| Arquivo em `data/raw/` | Repositório | Fonte | Label | Coletados | De bots | Analisados | Período |
|---|---|---|---|---|---|---|---|
| `kubernetes_kubernetes_kind-cleanup_issues.json` | kubernetes/kubernetes | issues | `kind/cleanup` | 15 | 0 | 15 | 2026-07-13 a 2026-09-25 |
| `microsoft_vscode_bug_issues.json` | microsoft/vscode | issues | `bug` | 20 | 11 | 9 | 2026-10-06 a 2026-10-07 |
| `microsoft_vscode_commits.json` | microsoft/vscode | commits | - | 100 | 3 | 97 | 2026-10-06 a 2026-10-08 |
| `microsoft_vscode_debt_issues.json` | microsoft/vscode | issues | `debt` | 30 | 0 | 30 | 2026-07-31 a 2026-10-06 |
| `microsoft_vscode_debt_prs.json` | microsoft/vscode | pull requests | `debt` | 15 | 0 | 15 | 2025-11-10 a 2026-09-21 |
| `pallets_flask_issues.json` | pallets/flask | issues | - | 15 | 0 | 15 | 2026-07-13 a 2026-09-24 |
| `pandas-dev_pandas_refactor_issues.json` | pandas-dev/pandas | issues | `Refactor` | 12 | 0 | 12 | 2023-07-16 a 2026-07-15 |
| `psf_requests_all.json` | psf/requests | issues + pull requests + commits | - | 24 | 14 | 10 | 2026-08-25 a 2026-10-08 |
| `psf_requests_issues.json` | psf/requests | issues | - | 5 | 0 | 5 | 2026-09-23 a 2026-10-08 |

Ao todo, 236 registros coletados e 208 analisados, em 5 repositórios. Duas coletas do `psf/requests` se sobrepõem: os registros de uma estão também na outra.

## Dívida técnica identificada

"Dívida identificada" é ter um padrão explícito da Regex ou ao menos um
tipo confirmado pelas regras.

| Arquivo | Analisados | Padrão explícito | Tipo confirmado | Dívida identificada | Parcela |
|---|---|---|---|---|---|
| `kubernetes_kubernetes_kind-cleanup_issues.json` | 15 | 3 | 8 | 8 | 53% |
| `microsoft_vscode_bug_issues.json` | 9 | 1 | 1 | 1 | 11% |
| `microsoft_vscode_commits.json` | 97 | 3 | 16 | 16 | 16% |
| `microsoft_vscode_debt_issues.json` | 30 | 11 | 13 | 16 | 53% |
| `microsoft_vscode_debt_prs.json` | 15 | 2 | 3 | 3 | 20% |
| `pallets_flask_issues.json` | 15 | 0 | 4 | 4 | 27% |
| `pandas-dev_pandas_refactor_issues.json` | 12 | 2 | 5 | 5 | 42% |
| `psf_requests_all.json` | 10 | 0 | 4 | 4 | 40% |
| `psf_requests_issues.json` | 5 | 0 | 3 | 3 | 60% |

### Por tipo de dívida

Documentos em que cada tipo foi confirmado (`yes`).

| Arquivo | Código | Arquitetura | Testes | Documentação | Dependências |
|---|---|---|---|---|---|
| `kubernetes_kubernetes_kind-cleanup_issues.json` | 4 | 0 | 7 | 0 | 1 |
| `microsoft_vscode_bug_issues.json` | 1 | 0 | 0 | 0 | 0 |
| `microsoft_vscode_commits.json` | 4 | 0 | 12 | 0 | 0 |
| `microsoft_vscode_debt_issues.json` | 7 | 3 | 6 | 0 | 1 |
| `microsoft_vscode_debt_prs.json` | 2 | 0 | 1 | 0 | 0 |
| `pallets_flask_issues.json` | 1 | 0 | 1 | 3 | 0 |
| `pandas-dev_pandas_refactor_issues.json` | 3 | 1 | 2 | 1 | 0 |
| `psf_requests_all.json` | 1 | 0 | 3 | 1 | 0 |
| `psf_requests_issues.json` | 1 | 0 | 3 | 0 | 0 |

### Por fonte, nas coletas com mais de uma

| Arquivo | Tipo de registro | Analisados | Dívida identificada |
|---|---|---|---|
| `psf_requests_all.json` | issue | 8 | 4 |
| `psf_requests_all.json` | pull_request | 1 | 0 |
| `psf_requests_all.json` | commit | 1 | 0 |

## Validação com as labels dos mantenedores

Não há gabarito do tipo de dívida. A referência disponível são as labels
que os mantenedores deram às issues e aos pull requests.

| Repositório | Fonte | Label | Analisados | Dívida identificada | Parcela |
|---|---|---|---|---|---|
| kubernetes/kubernetes | issues | `kind/cleanup` | 15 | 8 | 53% |
| microsoft/vscode | issues | `debt` | 30 | 16 | 53% |
| microsoft/vscode | pull requests | `debt` | 15 | 3 | 20% |
| pandas-dev/pandas | issues | `Refactor` | 12 | 5 | 42% |

- **Issues rotulados como dívida:** 29 de 57 identificados (51%).
- **Pull requests rotulados como dívida:** 3 de 15 identificados (20%).
- **Grupo de controle** (`microsoft/vscode`, label `bug`): 1 de 9 marcados.

Esses números não são acurácia: dizem quanto do que os mantenedores
rotularam o programa encontra, e não se o tipo atribuído está certo.

## Sentimento

Rótulo de cada documento, pela média do `compound` das sentenças.

| Arquivo | Positivos | Neutros | Negativos | Média do compound |
|---|---|---|---|---|
| `kubernetes_kubernetes_kind-cleanup_issues.json` | 6 | 8 | 1 | +0,039 |
| `microsoft_vscode_bug_issues.json` | 1 | 8 | 0 | +0,007 |
| `microsoft_vscode_commits.json` | 24 | 55 | 18 | +0,018 |
| `microsoft_vscode_debt_issues.json` | 8 | 15 | 7 | -0,008 |
| `microsoft_vscode_debt_prs.json` | 2 | 10 | 3 | -0,027 |
| `pallets_flask_issues.json` | 2 | 8 | 5 | -0,036 |
| `pandas-dev_pandas_refactor_issues.json` | 7 | 5 | 0 | +0,089 |
| `psf_requests_all.json` | 4 | 5 | 1 | +0,022 |
| `psf_requests_issues.json` | 3 | 1 | 1 | +0,029 |

## Resolução

Issues e pull requests com e sem dívida identificada: quantos foram
fechados e a mediana de dias até o fechamento. É um indício de
priorização, não uma medida. Coletas só de commits não aparecem.

| Arquivo | Com dívida: fechados | Mediana (dias) | Sem dívida: fechados | Mediana (dias) |
|---|---|---|---|---|
| `kubernetes_kubernetes_kind-cleanup_issues.json` | 3 de 8 | 0,8 | 3 de 7 | 4,0 |
| `microsoft_vscode_bug_issues.json` | 1 de 1 | 1,0 | 3 de 8 | 0,4 |
| `microsoft_vscode_debt_issues.json` | 7 de 16 | 1,3 | 7 de 14 | 4,0 |
| `microsoft_vscode_debt_prs.json` | 3 de 3 | 0,1 | 12 de 12 | 0,6 |
| `pallets_flask_issues.json` | 4 de 4 | 0,0 | 10 de 11 | 0,0 |
| `pandas-dev_pandas_refactor_issues.json` | 4 de 5 | 666,3 | 6 de 7 | 108,2 |
| `psf_requests_all.json` | 0 de 4 | - | 4 de 5 | 0,0 |
| `psf_requests_issues.json` | 0 de 3 | - | 1 de 2 | 0,0 |

## Termos, tecnologias e padrões mais frequentes

Entre parênteses, o total de ocorrências no corpus.

### `kubernetes_kubernetes_kind-cleanup_issues.json`

- **Substantivos:** test (150), validation (67), case (58), value (58), check (46), api (43)
- **Verbos:** need (46), add (38), reject (34), merge (32), start (31), leave (29)
- **Expressões:** beta rule (6), declarative validation (6), handwritten check (6), stored object (6)
- **Tecnologias (lista do projeto):** Kubernetes (36), Claude (4), Linux (3), GitHub (2), Git (1)
- **Entidades (NER do modelo):** API [ORG] (23), AI [GPE] (14), LimitRanger [ORG] (12), MilliValue [ORG] (12), TODO [ORG] (11)
- **Padrões de Regex:** todo (29), cleanup (19), unit_test (5), documentation (3), duplication (3), legacy (2)
- **Tokens:** 21473 em 1094 sentenças

### `microsoft_vscode_bug_issues.json`

- **Substantivos:** session (30), model (25), provider (20), tool (20), entry (17), picker (17)
- **Verbos:** open (12), capture (9), expect (8), return (8), select (8), stop (8)
- **Expressões:** agent host (6), agents window (4), background shells preview (4), inline terminal (4)
- **Tecnologias (lista do projeto):** Copilot (25), Git (12), VS Code (10), Windows (6), Claude (3), GitHub (2)
- **Entidades (NER do modelo):** SDK [ORG] (10), Git [PERSON] (9), Copilot [ORG] (7), UTC [ORG] (6), UI [ORG] (5)
- **Padrões de Regex:** workaround (2)
- **Tokens:** 4123 em 269 sentenças

### `microsoft_vscode_commits.json`

- **Substantivos:** chat (81), test (72), session (71), tool (47), host (46), client (39)
- **Verbos:** write (65), preserve (47), add (41), exist (32), remove (21), retain (21)
- **Expressões:** agent host (18), mission control (9), copilot sdk (7), tool search (7)
- **Tecnologias (lista do projeto):** Copilot (85), Git (12), VS Code (12), GitHub (11), Windows (8), Codex (6)
- **Entidades (NER do modelo):** Copilot [ORG] (18), MCP [ORG] (18), SDK [ORG] (16), CI [ORG] (9), Git [PERSON] (9)
- **Padrões de Regex:** legacy (13), cleanup (8), unit_test (3), architecture (2), flaky_test (2), integration_test (1)
- **Tokens:** 11204 em 722 sentenças

### `microsoft_vscode_debt_issues.json`

- **Substantivos:** icon (72), file (49), session (42), control (38), state (37), input (35)
- **Verbos:** share (55), exist (41), use (34), change (26), add (23), suggest (23)
- **Expressões:** agent host (19), suggested owner (10), chat input (6), scoped enablement work (6)
- **Tecnologias (lista do projeto):** Copilot (20), VS Code (19), CSS (14), Codex (10), npm (8), Claude (6)
- **Entidades (NER do modelo):** UI [ORG] (25), Copilot [ORG] (11), CSS [ORG] (10), VS Code [PRODUCT] (9), DOM [ORG] (5)
- **Padrões de Regex:** cleanup (11), legacy (11), debt (9), duplication (8), documentation (3), architecture (2)
- **Tokens:** 14830 em 881 sentenças

### `microsoft_vscode_debt_prs.json`

- **Substantivos:** setting (14), extension (10), fix (7), workspace (7), change (6), file (6)
- **Verbos:** remove (18), deprecate (7), set (7), run (6), edit (5), restrict (5)
- **Expressões:** git diff (4), remaining reference (4), built extension (2), component governance (2)
- **Tecnologias (lista do projeto):** VS Code (5), Git (4), HTML (4), npm (4), Copilot (2), CSS (1)
- **Entidades (NER do modelo):** JSON [PERSON] (4), VS Code [PRODUCT] (4), DOM [ORG] (3), CG [ORG] (1), CSS [ORG] (1)
- **Padrões de Regex:** unit_test (2), refactor (1), workaround (1)
- **Tokens:** 1271 em 96 sentenças

### `pallets_flask_issues.json`

- **Substantivos:** server (18), context (17), thread (17), app (14), request (12), doc (11)
- **Verbos:** run (10), add (9), fail (9), need (7), report (7), use (7)
- **Expressões:** high path traversal (6), flask version (5), app context (4), flask class (4)
- **Tecnologias (lista do projeto):** Flask (31), Python (11), PostgreSQL (3), GitHub (1)
- **Entidades (NER do modelo):** Flask [GPE] (12), Werkzeug [GPE] (9), Flask [PRODUCT] (5), Werkzeug [ORG] (4), GC [ORG] (3)
- **Padrões de Regex:** docs (11), documentation (4), update_docs (1)
- **Tokens:** 3359 em 245 sentenças

### `pandas-dev_pandas_refactor_issues.json`

- **Substantivos:** method (31), dtype (21), panda (20), subclass (16), argument (13), geopanda (12)
- **Verbos:** need (16), think (15), override (14), look (12), use (12), remove (10)
- **Expressões:** existing functionality (4), subclass author (3), alternative solutions (2), class object (2)
- **Tecnologias (lista do projeto):** Claude (1)
- **Entidades (NER do modelo):** TimeGrouper [ORG] (11), Series [EVENT] (10), REF [ORG] (8), DataFrame [ORG] (6), EA [ORG] (6)
- **Padrões de Regex:** refactor (6), documentation (4), docs (2)
- **Tokens:** 4297 em 277 sentenças

### `psf_requests_all.json`

- **Substantivos:** test (19), request (18), fix (16), line (12), branch (9), change (7)
- **Verbos:** open (12), pass (9), bypass (8), use (7), match (6), work (6)
- **Expressões:** client timeout (4), src request (4), behave runner (3), pull request (3)
- **Tecnologias (lista do projeto):** Python (6), Windows (5), GitHub (4)
- **Entidades (NER do modelo):** CookieJar [ORG] (7), CPython [ORG] (3), False [PERSON] (3), GitHub [ORG] (3), Windows [NORP] (3)
- **Padrões de Regex:** test_coverage (1)
- **Tokens:** 2069 em 141 sentenças

### `psf_requests_issues.json`

- **Substantivos:** test (18), request (16), fix (12), branch (8), change (7), line (7)
- **Verbos:** pass (9), bypass (8), open (7), match (6), use (6), work (5)
- **Expressões:** client timeout (4), behave runner (3), src request (3), comparison branch (2)
- **Tecnologias (lista do projeto):** Windows (5), GitHub (3), Python (3)
- **Entidades (NER do modelo):** CookieJar [ORG] (7), CPython [ORG] (3), False [PERSON] (3), Windows [NORP] (3), GitHub [ORG] (2)
- **Padrões de Regex:** test_coverage (1)
- **Tokens:** 1679 em 111 sentenças
