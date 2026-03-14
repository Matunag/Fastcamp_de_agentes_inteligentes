from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
from qdrant_client import QdrantClient
from mistralai import Mistral
from dotenv import load_dotenv
import os
load_dotenv()

mistral = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")

qdrant = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY"),
    timeout=30
)


def buscar_artigos(query: str) -> dict:
    """
    Busca os 3 artigos mais relevantes no banco de embeddings com base na query do usuário.
    """
    result = mistral.embeddings.create(
        model="mistral-embed",
        inputs=[query]
    )

    embedding_query = result.data[0].embedding

    resultados = qdrant.query_points(
        collection_name="Estudos",
        query=embedding_query,
        limit=3
    )

    artigos = []

    for r in resultados.points:
        artigos.append({
            "score": round(r.score, 4),
            "abstract": r.payload.get("texto", ""),
        })

    return {"artigos": artigos}


agente_busca = Agent(
    name="agente_busca",
    model="gemini-2.5-flash",
    description="Agente responsável por buscar artigos científicos relevantes usando embeddings.",
    instruction=(
        "Você é um agente especializado em busca de artigos científicos. "
        "Quando receber uma query do usuário, use a ferramenta 'buscar_artigos' para encontrar os 3 artigos mais relevantes. "
        "Apresente os resultados de forma clara, mostrando título, autores, ano e um resumo do abstract de cada artigo. "
        "Ordene do mais relevante para o menos relevante com base no score de similaridade."
    ),
    tools=[buscar_artigos]
)


orquestrador = Agent(
    name="orquestrador",
    model="gemini-2.5-flash",
    description="Orquestrador do sistema de busca de artigos científicos.",
    instruction=(
        "Você é um assistente especializado em pesquisa científica. "
        "Seu objetivo é ajudar o usuário a encontrar artigos relevantes para sua pesquisa. "
        "Quando o usuário fizer uma pergunta ou informar um tema, delegue a busca para o 'agente_busca'. "
        "Após receber os resultados, apresente os artigos de forma organizada e ofereça ao usuário a opção de refinar a busca."
    ),
    sub_agents=[agente_busca]
)


session_service = InMemorySessionService()

runner = Runner(
    agent=orquestrador,
    app_name="busca_artigos_app",
    session_service=session_service
)


async def buscar(query: str, user_id: str = "usuario_001"):

    session_id = f"sessao_{user_id}"

    try:
        await session_service.create_session(
            app_name="busca_artigos_app",
            user_id=user_id,
            session_id=session_id
        )
    except:
        pass

    message = types.Content(role="user", parts=[types.Part(text=query)])

    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=message
    ):
        if event.is_final_response():
            return event.content.parts[0].text