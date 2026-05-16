"""Leitura de configuracoes JSON do projeto."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_json(path: str | Path) -> dict[str, Any]:
    """Carrega um arquivo JSON e retorna um dicionario."""
    json_path = Path(path)
    with json_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError(f"O arquivo {json_path} deve conter um objeto JSON.")

    return data

