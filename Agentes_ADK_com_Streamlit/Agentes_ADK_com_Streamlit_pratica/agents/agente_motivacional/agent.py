agente_motivacional = Agent(
    name="agente_motivacional",
    model="gemini-2.5-flash",
    description="Gera frases motivacionais personalizadas para o usuário",
    instruction=(
        "Dado o objetivo e o nível do usuário, gere frases motivacionais inspiradoras. "
        "As frases devem ser relevantes para o contexto de saúde e bem-estar. "
        "Responda em português, seja encorajador e positivo."
    )
)

session_service = InMemorySessionService()
runner = Runner(agent=agente_motivacional, app_name="motivacional_app", session_service=session_service)
USER_ID    = "user_motivacional"
SESSION_ID = "session_motivacional"

async def execute(request):
    await session_service.create_session(
        app_name="motivacional_app", user_id=USER_ID, session_id=SESSION_ID
    )

    # prompt pede uma lista de strings — estrutura diferente dos outros agentes
    prompt = (
        f"Usuário tem objetivo: {request['objetivo']} e condicionamento: {request['condicionamento']}. "
        f"Gere 3 frases motivacionais personalizadas. "
        f"Responda em JSON com a chave 'frases' contendo uma lista de strings."
    )
    message = types.Content(role="user", parts=[types.Part(text=prompt)])

    async for event in runner.run_async(
            user_id=USER_ID, session_id=SESSION_ID, new_message=message):
        if event.is_final_response():
            response_text = event.content.parts[0].text
            try:
                clean = (response_text.strip()
                         .removeprefix("```json").removeprefix("```")
                         .removesuffix("```").strip())
                parsed = json.loads(clean)

                # valida que "frases" existe E é uma lista (não dict como nos outros)
                if "frases" in parsed and isinstance(parsed["frases"], list):
                    return {"frases": parsed["frases"]}
                else:
                    return {"frases": response_text}
            except json.JSONDecodeError as e:
                print("Falha ao parsear JSON:", e)
                return {"frases": response_text}
