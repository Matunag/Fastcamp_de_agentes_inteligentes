from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


BASE_DIR = Path(__file__).resolve().parents[1]
ARQUIVO_PACIENTES = BASE_DIR / "pacientes.json"


def carregar_pacientes() -> Dict[str, Any]:
    if not ARQUIVO_PACIENTES.exists():
        return {}
    try:
        with ARQUIVO_PACIENTES.open("r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}


def salvar_pacientes(dados: Dict[str, Any]) -> None:
    with ARQUIVO_PACIENTES.open("w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)


def agora_fmt() -> str:
    return datetime.now().strftime("%d/%m/%Y %H:%M")
