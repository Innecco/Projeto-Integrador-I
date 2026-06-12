"""Carregamento de variaveis de ambiente do projeto."""

from __future__ import annotations

import os
from pathlib import Path


def load_project_env(env_path: str | Path | None = None) -> None:
    """Carrega o arquivo .env usando python-dotenv quando disponivel."""
    path = Path(env_path) if env_path else find_env_file()
    if path is None or not path.exists():
        return

    try:
        from dotenv import load_dotenv

        load_dotenv(path)
    except ImportError:
        load_env_without_dependency(path)


def find_env_file() -> Path | None:
    """Procura o .env subindo a partir do diretorio atual."""
    current = Path.cwd().resolve()
    for candidate_dir in [current, *current.parents]:
        candidate = candidate_dir / ".env"
        if candidate.exists():
            return candidate
    return None


def load_env_without_dependency(path: Path) -> None:
    """Fallback pequeno para ambientes onde python-dotenv ainda nao foi instalado."""
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def env_value(name: str, default: str) -> str:
    """Retorna uma variavel de ambiente com valor padrao."""
    return os.environ.get(name, default)

