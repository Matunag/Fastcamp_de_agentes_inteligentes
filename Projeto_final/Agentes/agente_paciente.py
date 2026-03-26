from __future__ import annotations

from typing import Any, Dict

from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext

from .agente_contexto import agente_contexto
from .pacientes_store import carregar_pacientes, salvar_pacientes, agora_fmt


def post_estado(cpf: str, observacao: str, tool_context: ToolContext) -> Dict[str, Any]:
    """
    Registra uma observacao do paciente no arquivo de dados.
    """
    dados = carregar_pacientes()
    paciente = dados.get(cpf)

    if not paciente:
        return {
            "status": "erro",
            "mensagem": "Paciente nao encontrado.",
        }

    if "observacoes_paciente" not in paciente:
        paciente["observacoes_paciente"] = []

    item = {
        "data": agora_fmt(),
        "observacao": observacao,
    }

    paciente["observacoes_paciente"].append(item)
    salvar_pacientes(dados)

    return {
        "status": "sucesso",
        "mensagem": "Observacao registrada com sucesso.",
        "observacao": item,
    }


def mandar_alerta(
    cpf: str,
    motivo: str,
    tool_context: ToolContext
) -> Dict[str, Any]:
    dados = carregar_pacientes()
    paciente = dados.get(cpf)

    if not paciente:
        return {"status": "erro", "mensagem": "Paciente nao encontrado."}

    item = {
        "data_registro": agora_fmt(),
        "motivo": motivo,
    }

    if "alertas_medico" not in paciente:
        paciente["alertas_medico"] = []

    paciente["alertas_medico"].append(item)
    salvar_pacientes(dados)

    return {
        "status": "sucesso",
        "mensagem": "Alerta registrado para o medico.",
        "alerta": item,
    }


agente_paciente = Agent(
    name="agente_paciente",
    model="gemini-2.5-flash",
    description="Agente que atende o paciente e registra observacoes no prontuario.",
    instruction="""
    Voce atende o paciente e se comunica via WhatsApp (API Waha).
    Seu papel principal e registrar observacoes no prontuario usando a ferramenta 'post_estado'.
    Use 'mandar_alerta' quando detectar situacoes emergenciais no registro.
    Quando precisar consultar informacoes do paciente, acione o subagente 'agente_contexto'.
    """,
    tools=[post_estado, mandar_alerta],
    sub_agents=[agente_contexto],
)


__all__ = ["agente_paciente", "post_estado", "mandar_alerta"]
