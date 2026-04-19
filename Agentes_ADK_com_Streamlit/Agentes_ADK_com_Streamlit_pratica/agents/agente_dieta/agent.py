from google.adk.agents  import Agent
from google.adk.runners  import Runner
from google.adk.sessions import InMemorySessionService
from google.genai         import types
import json

# instrução fixa que molda o comportamento do agente em todas as chamadas
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
runner = Runner(agent=agente_dieta, app_name="dieta_app", session_service=session_service)
USER_ID    = "user_dieta"
SESSION_ID = "session_dieta"

async def execute(request):
    # await aqui pois create_session é assíncrono neste agente
    await session_service.create_session(
        app_name="dieta_app", user_id=USER_ID, session_id=SESSION_ID
    )

    # prompt específico para dieta — pede resposta em JSON estruturado
    prompt = (
        f"Usuário tem orçamento de R${request['orcamento']}, objetivo: {request['objetivo']} "
        f"e limitações: {request['limitacoes']}. Monte uma dieta diária com 5 refeições e 2-3 "
        f"opções por refeição. Responda em JSON com a chave 'dieta'."
    )
    message = types.Content(role="user", parts=[types.Part(text=prompt)])

    async for event in runner.run_async(
            user_id=USER_ID, session_id=SESSION_ID, new_message=message):
        if event.is_final_response():
            response_text = event.content.parts[0].text

            try:
                # remove marcadores de bloco de código que o modelo pode incluir
                # ex: ```json ... ``` → texto limpo
                clean = (response_text.strip()
                         .removeprefix("```json")
                         .removeprefix("```")
                         .removesuffix("```")
                         .strip())

                parsed = json.loads(clean)   # converte string JSON em dict

                # valida que a estrutura esperada existe na resposta
                if "dieta" in parsed and isinstance(parsed["dieta"], dict):
                    return {"dieta": parsed["dieta"]}
                else:
                    print("Chave 'dieta' ausente ou formato inválido")
                    return {"dieta": response_text}   # fallback: texto bruto

            except json.JSONDecodeError as e:
                # se o modelo não retornar JSON válido, loga e devolve texto bruto
                print("Falha ao parsear JSON:", e)
                print("Conteúdo da resposta:", response_text)
                return {"dieta": response_text}
