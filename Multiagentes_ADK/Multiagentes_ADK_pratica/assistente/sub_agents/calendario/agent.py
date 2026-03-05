
from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext
from typing import List, Dict
from datetime import datetime
from google.adk.tools import ToolContext


def ordenar_cronograma(cronograma: List[Dict]) -> List[Dict]:
    return sorted(
        cronograma,
        key=lambda x: datetime.strptime(
            f"{x['data']} {x['horario']}",
            "%Y-%m-%d %H:%M"
        )
    )


def get_cronograma(tool_context: ToolContext):
    state = tool_context.state

    if "cronograma" not in state:
        state["cronograma"] = []

    cronograma = ordenar_cronograma(state["cronograma"])

    if not cronograma:
        return {
            "status": "sucesso",
            "mensagem": "Seu calendário está vazio.",
            "cronograma": []
        }

    return {
        "status": "sucesso",
        "cronograma": cronograma
    }


def post_compromisso(
    data: str,
    horario: str,
    conteudo: str,
    tool_context: ToolContext
):
    """
    Na hora de colocar o compromisso lembre de colocar no formato "%Y-%m-%d %H:%M (ano, mes, dia, hora, minuto)"
    """
    state = tool_context.state

    if "cronograma" not in state:
        state["cronograma"] = []

    novo_compromisso = {
        "data": data,
        "horario": horario,
        "conteudo": conteudo
    }

    state["cronograma"].append(novo_compromisso)

    state["cronograma"] = ordenar_cronograma(state["cronograma"])

    return {
        "status": "sucesso",
        "mensagem": f"Compromisso marcado para {data} às {horario}.",
        "compromisso": novo_compromisso
    }


def delete_compromisso(
    data: str,
    horario: str,
    tool_context: ToolContext
):
    state = tool_context.state

    if "cronograma" not in state or not state["cronograma"]:
        return {
            "status": "erro",
            "mensagem": "Não há compromissos para remover."
        }

    compromisso_removido = None

    for c in state["cronograma"]:
        if (
            c["data"] == data and
            c["horario"] == horario
        ):
            compromisso_removido = c
            break

    if not compromisso_removido:
        return {
            "status": "erro",
            "mensagem": "Compromisso não encontrado."
        }

    state["cronograma"].remove(compromisso_removido)

    state["cronograma"] = ordenar_cronograma(state["cronograma"])

    return {
        "status": "sucesso",
        "mensagem": f"Compromisso removido de {data} às {horario}."
    }

calendario = Agent(
    name="calendario",
    model="gemini-2.5-flash",
    description="Um agente responsável por montar o calendário do usuário, marcando compromissos, entregas, planejamentos, etc nos respectivos dias e horários",
    instruction="""
    Você é um agente que cuida do calendário e planejamento do usuário
    
    Se for pedido para ver quais são os compromissos/ver calendário use a função a 'get_cronograma'
    Se for pedido para marcar um compromisso use a função 'post_compromisso'
    Se for pedido para desmarcar um compromisso use a função 'delete_compromisso'
    """,
    tools=[get_cronograma, post_compromisso, delete_compromisso],
)
