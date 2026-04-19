from google.adk.agents  import Agent
from google.adk.runners  import Runner
from google.adk.sessions import InMemorySessionService
from google.genai         import types

# cria o agente orquestrador — sem ferramentas nem subagentes
# definidos aqui; a coordenação é feita manualmente no task_manager
orquestrador = Agent(
    name="orquestrador",
    model="gemini-2.5-flash",      # modelo LLM usado pelo agente
    description="Cria uma rotina usando os agentes de dieta, treino e motivação.",
    instruction="You are the host agent responsible for orchestrating trip planning tasks. "
                "You call external agents to gather flights, stays, and activities, then return a final result."
)

# InMemorySessionService armazena o histórico da conversa
# apenas na memória — não persiste entre reinicializações
session_service = InMemorySessionService()

# Runner é o motor que executa o agente dentro de uma sessão
runner = Runner(
    agent=orquestrador,
    app_name="rotina_app",
    session_service=session_service
)

# IDs fixos para identificar o usuário e a sessão nesta aplicação
USER_ID    = "usuario_rotina"
SESSION_ID = "sessao_rotina"

async def executar(requisicao):
    # cria (ou reutiliza) a sessão de conversa para este usuário
    session_service.create_session(
        app_name="rotina_app", user_id=USER_ID, session_id=SESSION_ID
    )

    # monta o prompt com os dados recebidos do frontend via JSON
    # note: há um typo no original ("resquisicao" em vez de "requisicao")
    prompt = (
        f"Construa um treino para o usuário considerando o objetivo: {requisicao['objetivo']}, "
        f"as limitações: {requisicao['limitacoes']}, o condicionamento: {requisicao['condicionamento']}, "
        f"disponibilidade: {requisicao['disponibilidade_dias']} dias e {requisicao['disponibilidade_minutos']} min/dia. "
        f"Construa uma dieta considerando objetivo, limitações e orçamento: {requisicao['orcamento']}. "
        f"Faça frases motivacionais. Chame os agentes de dieta, treino e motivação."
    )

    # empacota o prompt no formato que o ADK espera
    message = types.Content(role="user", parts=[types.Part(text=prompt)])

    # itera sobre os eventos gerados pelo runner de forma assíncrona
    async for event in runner.run_async(
            user_id=USER_ID, session_id=SESSION_ID, new_message=message):

        # is_final_response() indica que este é o último evento
        # — o texto completo da resposta do agente
        if event.is_final_response():
            return {"rotina": event.content.parts[0].text}