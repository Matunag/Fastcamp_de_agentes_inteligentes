from __future__ import annotations

from typing import Any, Dict

from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext

from .pacientes_store import carregar_pacientes


def get_contexto_paciente(cpf: str, tool_context: ToolContext) -> Dict[str, Any]:
    """
    Ferramenta principal deste agente: busca um paciente pelo CPF e
    retorna seus dados de forma padronizada para outros agentes consumirem.
    """
    # Carrega todos os pacientes do arquivo JSON
    dados = carregar_pacientes()

    # Tenta localizar o paciente pelo CPF fornecido
    paciente = dados.get(cpf)

    # Retorna erro padronizado se o CPF não for encontrado
    if not paciente:
        return {
            "status": "erro",
            "mensagem": "Paciente nao encontrado.",
        }

    # Extrai listas de consultas e observações (padrão [] se ausentes)
    consultas = paciente.get("consultas", [])
    observacoes = paciente.get("observacoes_paciente", [])

    # Monta e retorna o contexto estruturado do paciente
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


# Definição do agente de contexto usando o Google ADK.
# Este agente é usado como subagente pelos agentes médico e paciente
# sempre que precisam de dados estruturados do prontuário.
agente_contexto = Agent(
    name="agente_contexto",
    model="gemini-2.5-flash",
    description="Agente que recupera informacoes do registro do paciente de forma padronizada.",
    instruction="""
    Voce e o agente responsavel por recuperar informacoes do registro do paciente
    de maneira padronizada e unificada para outros agentes.

    Use a ferramenta 'get_contexto_paciente' sempre que precisarem dos dados do paciente.
    """,
    tools=[get_contexto_paciente],  # Expõe apenas a ferramenta de busca
)


__all__ = ["agente_contexto", "get_contexto_paciente"]
