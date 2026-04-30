from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


# Pega a raiz do projeto (um nível acima de /Agentes/)
BASE_DIR = Path(__file__).resolve().parents[1]

# Caminho absoluto para o arquivo JSON que armazena todos os pacientes
ARQUIVO_PACIENTES = BASE_DIR / "pacientes.json"


def carregar_pacientes() -> Dict[str, Any]:
    """Lê o arquivo JSON e retorna o dicionário de pacientes.
    """
    if not ARQUIVO_PACIENTES.exists():
        # Arquivo ainda não foi criado — retorna dicionário vazio
        return {}
    try:
        with ARQUIVO_PACIENTES.open("r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        # Arquivo corrompido ou vazio — retorna dicionário vazio para evitar bugs
        return {}


def salvar_pacientes(dados: Dict[str, Any]) -> None:
    """Salva o dicionário de pacientes de volta no arquivo JSON.
    Usa indent=4 para legibilidade e ensure_ascii=False para salvar acentos.
    """
    with ARQUIVO_PACIENTES.open("w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)


def agora_fmt() -> str:
    """Retorna a data e hora atual no formato dd/mm/AAAA HH:MM,
    usado para registrar timestamps em consultas e observações.
    """
    return datetime.now().strftime("%d/%m/%Y %H:%M")
