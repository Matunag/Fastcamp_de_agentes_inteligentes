from __future__ import annotations

from typing import Any, Dict

from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext

from .agente_contexto import agente_contexto
from .pacientes_store import carregar_pacientes, salvar_pacientes, agora_fmt


def post_estado(cpf: str, observacao: str, tool_context: ToolContext) -> Dict[str, Any]:
    """
    Ferramenta que registra uma observação do próprio paciente no prontuário.
    """
    dados = carregar_pacientes()
    paciente = dados.get(cpf)

    # Se não achar o paciente
    if not paciente:
        return {
            "status": "erro",
            "mensagem": "Paciente nao encontrado.",
        }

    # Garante que a chave de observações existe antes de adicionar
    if "observacoes_paciente" not in paciente:
        paciente["observacoes_paciente"] = []

    # Cria o item com timestamp e texto da observação
    item = {
        "data": agora_fmt(),
        "observacao": observacao,
    }

    # Adiciona ao histórico e persiste no arquivo JSON
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
    """
    Ferramenta que registra um alerta para o médico no prontuário do paciente.
    Usada quando o agente detecta situações que exigem atenção médica imediata.
    """
    dados = carregar_pacientes()
    paciente = dados.get(cpf)

    if not paciente:
        return {"status": "erro", "mensagem": "Paciente nao encontrado."}

    # Cria o alerta com timestamp e motivo informado
    item = {
        "data_registro": agora_fmt(),
        "motivo": motivo,
    }

    # Garante que a lista de alertas existe antes de adicionar
    if "alertas_medico" not in paciente:
        paciente["alertas_medico"] = []

    # Adiciona o alerta e persiste no arquivo JSON
    paciente["alertas_medico"].append(item)
    salvar_pacientes(dados)

    return {
        "status": "sucesso",
        "mensagem": "Alerta registrado para o medico.",
        "alerta": item,
    }


# Definição do agente do paciente, acionado via webhook do WhatsApp (api.py).
# Atende mensagens do paciente, registra observações e emite alertas ao médico.
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
    sub_agents=[agente_contexto],  # Subagente para consultar dados do prontuário
)


__all__ = ["agente_paciente", "post_estado", "mandar_alerta"]
