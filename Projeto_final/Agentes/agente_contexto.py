from __future__ import annotations

from typing import Any, Dict

from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext

from .pacientes_store import carregar_pacientes


def get_contexto_paciente(cpf: str, tool_context: ToolContext) -> Dict[str, Any]:
    """
    Recupera as informacoes padronizadas do registro do paciente.
    """
    dados = carregar_pacientes()
    paciente = dados.get(cpf)

    if not paciente:
        return {
            "status": "erro",
            "mensagem": "Paciente nao encontrado.",
        }

    consultas = paciente.get("consultas", [])
    observacoes = paciente.get("observacoes_paciente", [])

    return {
        "status": "sucesso",
        "paciente": {
            "nome": paciente.get("nome"),
            "idade": paciente.get("idade"),
            "sexo": paciente.get("sexo"),
            "historico": paciente.get("historico"),
        },
        "consultas": consultas,
        "observacoes_paciente": observacoes,
    }


agente_contexto = Agent(
    name="agente_contexto",
    model="gemini-2.5-flash",
    description="Agente que recupera informacoes do registro do paciente de forma padronizada.",
    instruction="""
    Voce e o agente responsavel por recuperar informacoes do registro do paciente
    de maneira padronizada e unificada para outros agentes.

    Use a ferramenta 'get_contexto_paciente' sempre que precisarem dos dados do paciente.
    """,
    tools=[get_contexto_paciente],
)


__all__ = ["agente_contexto", "get_contexto_paciente"]
