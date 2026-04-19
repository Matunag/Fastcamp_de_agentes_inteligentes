# mesma estrutura do agente_dieta — apenas instruction e prompt mudam
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

# sessão e runner independentes — cada agente tem seu próprio contexto
session_service = InMemorySessionService()
runner = Runner(agent=agente_treino, app_name="treino_app", session_service=session_service)
USER_ID    = "user_treino"
SESSION_ID = "session_treino"

async def execute(request):
    await session_service.create_session(
        app_name="treino_app", user_id=USER_ID, session_id=SESSION_ID
    )

    # prompt usa dados de condicionamento e disponibilidade — específicos para treino
    prompt = (
        f"Usuário tem objetivo: {request['objetivo']}, condicionamento: {request['condicionamento']}, "
        f"disponibilidade de {request['disponibilidade_dias']} dias/semana "
        f"e {request['disponibilidade_minutos']} min/dia. "
        f"Monte um treino com aquecimento, exercícios principais e alongamento. "
        f"Responda em JSON com a chave 'treino'."
    )
    message = types.Content(role="user", parts=[types.Part(text=prompt)])

    async for event in runner.run_async(
            user_id=USER_ID, session_id=SESSION_ID, new_message=message):
        if event.is_final_response():
            response_text = event.content.parts[0].text
            try:
                # mesma limpeza de markdown e parse JSON do agente_dieta
                clean = (response_text.strip()
                         .removeprefix("```json").removeprefix("```")
                         .removesuffix("```").strip())
                parsed = json.loads(clean)
                if "treino" in parsed and isinstance(parsed["treino"], dict):
                    return {"treino": parsed["treino"]}
                else:
                    return {"treino": response_text}
            except json.JSONDecodeError as e:
                print("Falha ao parsear JSON:", e)
                return {"treino": response_text}
