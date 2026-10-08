"""Coleta de issues, pull requests e commits pela API REST do GitHub.

O coletor busca os registros de um repositório, junta os comentários das
issues e dos pull requests e devolve tudo em um formato único, usado
pelos módulos de análise. O campo "type" de cada registro diz o que ele
é: "issue", "pull_request" ou "commit".

Documentação da API: https://docs.github.com/rest/issues
"""
import re
from datetime import datetime, timezone
from urllib.parse import quote

import requests

from src import config
from src.storage import save_json

PER_PAGE = 100                # máximo de itens por página aceito pela API
MAX_COMMENTS_PER_ISSUE = 100  # evita gastar requisições com issues gigantes

# Fontes que podem ser coletadas, na ordem em que aparecem no resultado.
SOURCES = ("issues", "prs", "commits")

# Endereço de e-mail. O (?![:\w]) deixa de fora endereços de repositório
# como git@github.com:org/repo; a exigência de letras no fim deixa de fora
# versões de pacote como react@18.2.0.
EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}\b(?![:\w])")
MASKED_EMAIL = "redacted@example.com"


class GitHubError(Exception):
    """Erro na coleta com mensagem pronta para mostrar ao usuário."""


class RateLimitError(GitHubError):
    """A API recusou a requisição porque o limite foi atingido."""


def mask_emails(text):
    """Troca endereços de e-mail por um endereço fictício.

    Os textos coletados são gravados em disco e podem ser publicados; os
    e-mails de terceiros não interessam à análise. O substituto continua
    sendo um token só para o spaCy, então as contagens não mudam.
    """
    return EMAIL.sub(MASKED_EMAIL, text)


def normalize_issue(raw):
    """Converte uma issue da API para o formato do DebtRadar.

    Campos de texto ausentes ou nulos viram string vazia, assim os módulos
    seguintes não precisam tratar None.
    """
    label_names = [_label_name(label) for label in raw.get("labels") or []]
    return {
        # Para a API todo pull request é uma issue com o campo "pull_request".
        "type": "pull_request" if "pull_request" in raw else "issue",
        "id": f"#{raw.get('number')}",
        "number": raw.get("number"),
        "title": mask_emails(raw.get("title") or ""),
        "body": mask_emails(raw.get("body") or ""),
        "author": _login(raw.get("user")),
        "state": raw.get("state") or "",
        "labels": [name for name in label_names if name],
        "created_at": raw.get("created_at") or "",
        "updated_at": raw.get("updated_at") or "",
        "closed_at": raw.get("closed_at") or "",
        "url": raw.get("html_url") or "",
        "comments_count": raw.get("comments") or 0,
        "comments": [],
        "comments_collected": False,
    }


def normalize_commit(raw):
    """Converte um commit da API para o mesmo formato das issues.

    A primeira linha da mensagem vira o título e o restante, o corpo.
    Commits não têm número, estado, labels nem comentários.
    """
    commit = raw.get("commit") or {}
    git_author = commit.get("author") or {}
    title, _, body = mask_emails(commit.get("message") or "").partition("\n")
    sha = raw.get("sha") or ""
    date = git_author.get("date") or ""
    return {
        "type": "commit",
        "id": sha[:7],
        "number": None,
        "title": title.strip(),
        "body": body.strip(),
        # Conta do GitHub, quando existe; senão, o nome gravado no commit.
        "author": _login(raw.get("author")) or git_author.get("name") or "",
        "state": "",
        "labels": [],
        "created_at": date,
        "updated_at": date,
        "closed_at": "",
        "url": raw.get("html_url") or "",
        "comments_count": 0,
        "comments": [],
        "comments_collected": True,
    }


def normalize_comment(raw):
    """Converte um comentário da API para o formato do DebtRadar."""
    return {
        "author": _login(raw.get("user")),
        "body": mask_emails(raw.get("body") or ""),
        "created_at": raw.get("created_at") or "",
        "url": raw.get("html_url") or "",
    }


def _login(user):
    """Nome do usuário; contas apagadas chegam como null na API."""
    return (user or {}).get("login") or ""


def _label_name(label):
    """A API pode devolver a label como objeto ou como texto simples."""
    if isinstance(label, dict):
        return label.get("name") or ""
    return str(label)


class GitHubCollector:
    """Cliente simples da API do GitHub para coletar issues e comentários."""

    def __init__(self, token="", timeout=config.REQUEST_TIMEOUT):
        self.timeout = timeout
        self.authenticated = bool(token)
        self.rate_limit_remaining = None  # requisições que ainda restam
        self.rate_limit_reset = None      # horário (epoch) em que o limite renova
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "DebtRadar",
        })
        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"

    def collect(self, owner, repo, limit, label=None, sources=("issues",)):
        """Coleta até 'limit' registros de cada fonte pedida em owner/repo.

        'sources' escolhe entre "issues", "prs" e "commits". Devolve um
        dicionário com "metadata" (dados da coleta) e "issues" (a lista de
        registros, de qualquer tipo).
        """
        sources = [source for source in SOURCES if source in sources]
        issues = []
        if "issues" in sources or "prs" in sources:
            issues += self._fetch_issues(owner, repo, limit, label, sources)
        # Os commits vêm antes dos comentários: custam uma requisição só, e
        # assim não se perdem se o limite da API acabar nos comentários.
        if "commits" in sources:
            issues += self._fetch_commits(owner, repo, limit)
        warning = self._add_comments(owner, repo, issues)
        metadata = {
            "source": "github",
            "owner": owner,
            "repo": repo,
            "label": label or "",
            "sources": sources,
            "requested": limit,
            "collected": len(issues),
            "collected_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "comments_complete": all(i["comments_collected"] for i in issues),
            "warning": warning,
        }
        return {"metadata": metadata, "issues": issues}

    def _fetch_issues(self, owner, repo, limit, label, sources):
        """Busca issues e pull requests, que a API devolve na mesma listagem."""
        params = {"state": "all", "per_page": PER_PAGE}
        if label:
            params["labels"] = label
        wanted = {"issue": limit if "issues" in sources else 0,
                  "pull_request": limit if "prs" in sources else 0}
        found = {"issue": [], "pull_request": []}
        for raw in self._paginate(f"{self._repo_url(owner, repo)}/issues", params):
            if raw.get("number") is None:
                continue
            record = normalize_issue(raw)
            kind = record["type"]
            # Tipos que não foram pedidos (ou já completos) são descartados.
            if len(found[kind]) < wanted[kind]:
                found[kind].append(record)
            if all(len(found[name]) >= wanted[name] for name in wanted):
                break
        return found["issue"] + found["pull_request"]

    def _fetch_commits(self, owner, repo, limit):
        commits = []
        for raw in self._paginate(f"{self._repo_url(owner, repo)}/commits", {"per_page": PER_PAGE}):
            # Commits de merge só repetem o título de um pull request.
            if len(raw.get("parents") or []) > 1:
                continue
            commits.append(normalize_commit(raw))
            if len(commits) >= limit:
                break
        return commits

    def _add_comments(self, owner, repo, issues):
        """Preenche os comentários de cada issue ou pull request.

        Se a API falhar no meio do caminho (por exemplo, limite atingido),
        as issues já coletadas são mantidas e o motivo é devolvido como aviso.
        """
        for issue in issues:
            if issue["comments_count"] > 0:
                url = f"{self._repo_url(owner, repo)}/issues/{issue['number']}/comments"
                try:
                    issue["comments"] = self._fetch_comments(url)
                except GitHubError as error:
                    return f"Comentários incompletos: {error}"
            issue["comments_collected"] = True
        return ""

    def _fetch_comments(self, url):
        comments = []
        for raw in self._paginate(url, {"per_page": PER_PAGE}):
            comments.append(normalize_comment(raw))
            if len(comments) >= MAX_COMMENTS_PER_ISSUE:
                break
        return comments

    def _paginate(self, url, params):
        """Gera os itens de todas as páginas, uma requisição por página.

        A próxima página vem no cabeçalho "Link" da resposta. Como é um
        gerador, a página seguinte só é pedida se quem chamou continuar lendo.
        """
        while url:
            response = self._get(url, params)
            try:
                items = response.json()
            except ValueError:
                raise GitHubError("A resposta da API não é um JSON válido.") from None
            if not isinstance(items, list):
                raise GitHubError("Resposta inesperada da API (era esperada uma lista).")
            for item in items:
                if isinstance(item, dict):
                    yield item
            url = response.links.get("next", {}).get("url")
            params = None  # a URL da próxima página já traz os parâmetros
            # O token vai no cabeçalho de toda requisição: só segue links da própria API.
            if url and not url.startswith(config.GITHUB_API_URL + "/"):
                raise GitHubError("A API indicou uma próxima página fora do GitHub.")

    def _get(self, url, params):
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
        except requests.Timeout:
            raise GitHubError(
                f"A API do GitHub não respondeu em {self.timeout} segundos."
            ) from None
        except requests.RequestException as error:
            raise GitHubError(f"Falha de conexão com a API do GitHub: {error}") from None
        self._update_rate_limit(response)
        self._check_status(response)
        return response

    def _update_rate_limit(self, response):
        remaining = response.headers.get("X-RateLimit-Remaining", "")
        reset = response.headers.get("X-RateLimit-Reset", "")
        if remaining.isdigit():
            self.rate_limit_remaining = int(remaining)
        if reset.isdigit():
            self.rate_limit_reset = int(reset)

    def _check_status(self, response):
        """Transforma respostas de erro em exceções com mensagens claras."""
        status = response.status_code
        if status < 400:
            return
        limit_reached = (
            response.headers.get("X-RateLimit-Remaining") == "0"
            or "Retry-After" in response.headers
        )
        if status in (403, 429) and limit_reached:
            raise RateLimitError(self._rate_limit_message())
        if status == 401:
            raise GitHubError("GITHUB_TOKEN inválido ou expirado. Confira o valor no .env.")
        if status == 404:
            raise GitHubError(
                "Repositório não encontrado. Confira owner e repository "
                "(repositórios privados exigem um token com acesso)."
            )
        if status == 410:
            raise GitHubError("As issues estão desativadas neste repositório.")
        raise GitHubError(f"A API do GitHub respondeu com erro HTTP {status}.")

    def _rate_limit_message(self):
        message = "Limite de requisições da API do GitHub atingido."
        if self.rate_limit_reset:
            reset_time = datetime.fromtimestamp(self.rate_limit_reset).strftime("%H:%M")
            message += f" O limite renova às {reset_time}."
        if not self.authenticated:
            message += " Configure GITHUB_TOKEN no .env para ter 5000 requisições/hora."
        return message

    @staticmethod
    def _repo_url(owner, repo):
        return f"{config.GITHUB_API_URL}/repos/{quote(owner, safe='')}/{quote(repo, safe='')}"


def save_collection(collection, directory=config.RAW_DIR):
    """Salva a coleta em JSON e devolve o caminho do arquivo.

    O nome do arquivo traz owner, repositório, label (quando usada) e a
    fonte: "issues", "prs", "commits" ou "all" quando há mais de uma.
    Se já existir uma coleta com esse nome, ela é movida para a pasta
    "backup" antes de ser substituída.
    """
    metadata = collection["metadata"]
    parts = [metadata["owner"], metadata["repo"]]
    if metadata["label"]:
        # Labels podem ter espaços e símbolos; no nome do arquivo viram "-".
        parts.append("".join(c if c.isalnum() else "-" for c in metadata["label"]))
    sources = metadata.get("sources", ["issues"])
    parts.append(sources[0] if len(sources) == 1 else "all")
    path = directory / ("_".join(parts) + ".json").lower()
    if path.exists():
        backup_dir = directory / "backup"
        backup_dir.mkdir(exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        path.rename(backup_dir / f"{path.stem}_{stamp}.json")
    save_json(collection, path)
    return path
