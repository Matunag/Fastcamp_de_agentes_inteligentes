# Arquivo de criação do agente principal (orquestrador)

# Importa as bibliotecas que serão usadas
from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool
import os

# Importa os agentes e ferramentas que serão usados definidos em outros arquivos.
from .sub_agents.calendario.agent import calendario
from .sub_agents.assistente_financeiro.agent import assistente_financeiro
from .tools.tools import obter_clima

# Criação em si do agente principal.
root_agent = Agent(
    name="assistente", # Tem que ser o mesmo nome da pasta
    model="gemini-2.5-flash",
    description="Agente orquestrador",
    instruction="""
    Você é um assistente pessoal principal, ou seja, coordena com outros agente a melhor maneira de resolver um pedido.

    Sempre que um pedido for direcionado a você, veja se tem os subagentes ou ferramentas para realizar realizá-lo. Se não tiver nenhum dos dois fale que você não tem essa função.

    Os subagentes a seu comando são:
    -calendario
    -assistente_financeiro
    """,
    sub_agents=[calendario, assistente_financeiro],
    tools=[
        obter_clima,
    ],
)