from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
import json

agente_dieta = Agent(
    name="agente_dieta",
    model="gemini-2.5-flash",
    description="Sugere dietas para as necessidades do usuário",
    instruction=(
        "Dado o orçamento, objetivo e limitações do usuário, monte uma dieta diária. "
        "A dieta diária será composta, preferencialmente, por 5 refeições: café da manhã, almoço, lanche, janta e ceia. "
        "Dê de duas a três opções de refeição para cada uma delas. "
        "Responda em português, mantenha a resposta concisa e bem-formatada."
    )
)

session_service = InMemorySessionService()
runner = Runner(
    agent=agente_dieta,
    app_name="dieta_app",
    session_service=session_service
)
USER_ID = "user_dieta"
SESSION_ID = "session_dieta"

async def execute(request):
    await session_service.create_session(
        app_name="dieta_app",
        user_id=USER_ID,
        session_id=SESSION_ID
    )
    prompt = (
        f"Usuário tem orçamento de R${request['orcamento']}, "
        f"objetivo: {request['objetivo']} e limitações: {request['limitacoes']}. "
        f"Monte uma dieta diária com 5 refeições e 2-3 opções por refeição. "
        f"Responda em JSON usando a chave 'dieta' com um objeto onde cada chave é uma refeição."
    )
    message = types.Content(role="user", parts=[types.Part(text=prompt)])
    async for event in runner.run_async(user_id=USER_ID, session_id=SESSION_ID, new_message=message):
        if event.is_final_response():
            response_text = event.content.parts[0].text
            try:
                clean = response_text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
                parsed = json.loads(clean)
                if "dieta" in parsed and isinstance(parsed["dieta"], dict):
                    return {"dieta": parsed["dieta"]}
                else:
                    print("Chave 'dieta' ausente ou formato inválido")
                    return {"dieta": response_text}
            except json.JSONDecodeError as e:
                print("Falha ao parsear JSON:", e)
                print("Conteúdo da resposta:", response_text)
                return {"dieta": response_text}