from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
import json

agente_treino = Agent(
    name="agente_treino",
    model="gemini-2.5-flash",
    description="Sugere treinos personalizados para as necessidades do usuário",
    instruction=(
        "Dado o objetivo, nível de condicionamento e disponibilidade do usuário, monte um treino semanal. "
        "O treino deve conter aquecimento, exercícios principais e alongamento. "
        "Para cada exercício informe séries, repetições e tempo de descanso. "
        "Responda em português, mantenha a resposta concisa e bem-formatada."
    )
)

session_service = InMemorySessionService()
runner = Runner(
    agent=agente_treino,
    app_name="treino_app",
    session_service=session_service
)
USER_ID = "user_treino"
SESSION_ID = "session_treino"

async def execute(request):
    await session_service.create_session(
        app_name="treino_app",
        user_id=USER_ID,
        session_id=SESSION_ID
    )
    prompt = (
        f"Usuário tem objetivo: {request['objetivo']}, "
        f"nível de condicionamento: {request['condicionamento']}, "
        f"disponibilidade de {request['disponibilidade_dias']} dias por semana "
        f"e {request['disponibilidade_minutos']} minutos por dia. "
        f"Monte um treino diário com aquecimento, exercícios principais e alongamento. "
        f"Responda em JSON usando a chave 'treino' com um objeto onde cada chave é uma fase do treino."
    )
    message = types.Content(role="user", parts=[types.Part(text=prompt)])
    async for event in runner.run_async(user_id=USER_ID, session_id=SESSION_ID, new_message=message):
        if event.is_final_response():
            response_text = event.content.parts[0].text
            try:
                clean = response_text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
                parsed = json.loads(clean)
                if "treino" in parsed and isinstance(parsed["treino"], dict):
                    return {"treino": parsed["treino"]}
                else:
                    print("Chave 'treino' ausente ou formato inválido")
                    return {"treino": response_text}
            except json.JSONDecodeError as e:
                print("Falha ao parsear JSON:", e)
                print("Conteúdo da resposta:", response_text)
                return {"treino": response_text}
