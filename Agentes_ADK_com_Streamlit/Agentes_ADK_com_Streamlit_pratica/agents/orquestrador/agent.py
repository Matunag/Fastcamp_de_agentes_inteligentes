from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

orquestrador = Agent(
    name="orquestrador",
    model="gemini-2.5-flash",
    description="Cria uma rotina usando os agentes de dieta, treino e motivação.",
    instruction="You are the host agent responsible for orchestrating trip planning tasks. "
                "You call external agents to gather flights, stays, and activities, then return a final result."
)

session_service = InMemorySessionService()
runner = Runner(
    agent=orquestrador,
    app_name="rotina_app",
    session_service=session_service
)

USER_ID = "usuario_rotina"
SESSION_ID = "sessao_rotina"

async def executar(requisicao):
    session_service.create_session(
        app_name="rotina_app",
        user_id=USER_ID,
        session_id=SESSION_ID
    )

    prompt = (
        f"Crie uma rotina personalizada para {requisicao['nome']}. "
        f"Objetivo: {requisicao['objetivo']}. "
        f"Dias disponíveis por semana: {requisicao['dias_disponiveis']}. "
        f"Restrições alimentares: {requisicao['restricoes_alimentares']}. "
        f"Chame os agentes de dieta, treino e motivação para montar o plano completo."
    )

    message = types.Content(role="user", parts=[types.Part(text=prompt)])

    async for event in runner.run_async(user_id=USER_ID, session_id=SESSION_ID, new_message=message):
        if event.is_final_response():
            return {"rotina": event.content.parts[0].text}