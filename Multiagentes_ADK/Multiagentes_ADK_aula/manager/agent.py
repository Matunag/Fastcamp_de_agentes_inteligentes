# Arquivo de criação do agente principal (orquestrador)

# Importa as bibliotecas que serão usadas
from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool

# Importa os agentes e ferramentas que serão usados definidos em outros arquivos.
from .sub_agents.funny_nerd.agent import funny_nerd
from .sub_agents.news_analyst.agent import news_analyst
from .sub_agents.stock_analyst.agent import stock_analyst
from .tools.tools import get_current_time

# Criação em si do agente principal.
root_agent = Agent(
    name="manager", # Tem que ser o mesmo nome da pasta
    model="gemini-2.0-flash",
    description="Manager agent",
    instruction="""
    You are a manager agent that is responsible for overseeing the work of the other agents.

    Always delegate the task to the appropriate agent. Use your best judgement 
    to determine which agent to delegate to.

    You are responsible for delegating tasks to the following agent:
    - stock_analyst
    - funny_nerd

    You also have access to the following tools:
    - news_analyst
    - get_current_time
    """,
    sub_agents=[stock_analyst, funny_nerd],
    tools=[
        AgentTool(news_analyst), # É um agente que vai usar uma built-in tool, mas para isso é preciso definir ela no campo de ferramentas usando um AgentTool()
        get_current_time,
    ],
)