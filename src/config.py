"""Configuração central do DebtRadar.

Reúne em um único lugar os caminhos do projeto e os valores lidos do
arquivo ".env". Os outros módulos recebem um objeto Config em vez de
ler variáveis de ambiente por conta própria.
"""
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Caminhos do projeto (não dependem do .env)
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"              # dados brutos vindos da API
PROCESSED_DIR = DATA_DIR / "processed"  # dados já limpos e analisados
RESULTS_DIR = DATA_DIR / "results"      # resumo consolidado de cada corpus

# API do GitHub
GITHUB_API_URL = "https://api.github.com"
REQUEST_TIMEOUT = 15  # segundos de espera por resposta

# Valores usados quando a variável não está no .env
DEFAULT_SPACY_MODEL = "en_core_web_sm"
DEFAULT_ISSUES = 100


class ConfigError(Exception):
    """Erro de configuração com mensagem pronta para mostrar ao usuário."""


@dataclass(frozen=True)
class Config:
    """Valores de configuração usados pelo programa."""

    # repr=False: o token não aparece se a configuração for impressa ou registrada.
    github_token: str = field(repr=False)
    spacy_model: str
    default_issues: int  # quantidade sugerida quando o programa pergunta

    @property
    def has_github_token(self):
        return bool(self.github_token)


def _read_positive_int(name, default):
    """Lê uma variável de ambiente que deve ser um inteiro maior que zero."""
    raw_value = os.getenv(name, "").strip()
    if not raw_value:
        return default
    try:
        value = int(raw_value)
    except ValueError:
        raise ConfigError(
            f"{name} deve ser um número inteiro, mas o valor é '{raw_value}'."
        ) from None
    if value <= 0:
        raise ConfigError(f"{name} deve ser maior que zero, mas o valor é {value}.")
    return value


def load_config():
    """Carrega o .env (se existir) e devolve a configuração validada.

    Variáveis já definidas no terminal têm prioridade sobre o .env.
    """
    load_dotenv(ENV_FILE)
    return Config(
        github_token=os.getenv("GITHUB_TOKEN", "").strip(),
        spacy_model=os.getenv("SPACY_MODEL", "").strip() or DEFAULT_SPACY_MODEL,
        default_issues=_read_positive_int("DEFAULT_ISSUES", DEFAULT_ISSUES),
    )


def ensure_directories():
    """Cria as pastas de dados caso ainda não existam."""
    for directory in (RAW_DIR, PROCESSED_DIR, RESULTS_DIR):
        directory.mkdir(parents=True, exist_ok=True)
