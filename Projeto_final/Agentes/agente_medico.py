from __future__ import annotations

from typing import Any, Dict, List
import os

from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext
from qdrant_client import QdrantClient
from mistralai import Mistral
from dotenv import load_dotenv

from .agente_contexto import agente_contexto
from .pacientes_store import carregar_pacientes

load_dotenv()

mistral = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")

qdrant = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY"),
    timeout=30
)


def _ultimo_registro(consultas: List[Dict[str, Any]]) -> Dict[str, Any] | None:
    if not consultas:
        return None
    return consultas[-1]


def dar_resumo(cpf: str, tool_context: ToolContext) -> Dict[str, Any]:
    """
    Analisa o historico do paciente e gera um resumo.
    """
    dados = carregar_pacientes()
    paciente = dados.get(cpf)

    if not paciente:
        return {
            "status": "erro",
            "mensagem": "Paciente nao encontrado.",
        }

    consultas = paciente.get("consultas", [])
    observacoes = paciente.get("observacoes_paciente", [])
    ultima = _ultimo_registro(consultas)

    resumo = (
        f"Paciente {paciente.get('nome')} ({paciente.get('idade')} anos, {paciente.get('sexo')}). "
        f"Historico: {paciente.get('historico')}. "
        f"Consultas registradas: {len(consultas)}. "
        f"Observacoes recentes do paciente: {len(observacoes)}."
    )

    if ultima:
        resumo += (
            f" Ultima consulta em {ultima.get('data')}: "
            f"sintomas '{ultima.get('sintomas')}', "
            f"diagnostico '{ultima.get('diagnostico')}', "
            f"tratamento '{ultima.get('tratamento')}'."
        )

    return {
        "status": "sucesso",
        "resumo": resumo,
        "consultas": consultas,
        "observacoes_paciente": observacoes,
    }


def dar_sugestao(cpf: str, tool_context: ToolContext) -> Dict[str, Any]:
    """
    Gera uma sugestao inicial para o medico com base no registro.
    """
    dados = carregar_pacientes()
    paciente = dados.get(cpf)

    if not paciente:
        return {
            "status": "erro",
            "mensagem": "Paciente nao encontrado.",
        }

    consultas = paciente.get("consultas", [])
    observacoes = paciente.get("observacoes_paciente", [])
    ultima = _ultimo_registro(consultas)

    if not consultas:
        sugestao = (
            "Nao ha consultas registradas. Recomenda-se realizar uma avaliacao inicial "
            "e registrar sintomas, exames e plano terapeutico."
        )
    else:
        sugestao = (
            "Sugestao inicial: revisar o tratamento atual, monitorar sintomas nas "
            "proximas 48-72h e considerar exames complementares se houver piora. "
            "Avaliar aderencia ao tratamento e fatores de risco."
        )

    if observacoes:
        sugestao += " Ha observacoes recentes do paciente que podem exigir contato proativo."

    if ultima and "urg" in str(ultima.get("observacoes", "")).lower():
        sugestao += " Observacao de ultima consulta indica alerta; reavaliar prontamente."

    return {
        "status": "sucesso",
        "sugestao": sugestao,
    }

def buscar_artigos(query: str) -> Dict[str, Any]:
    """
    Busca os 3 artigos mais relevantes no banco de embeddings com base na query do usuario.
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


agente_medico = Agent(
    name="agente_medico",
    model="gemini-2.5-flash",
    description="Agente que auxilia o medico a visualizar a situacao do paciente.",
    instruction="""
    Voce auxilia o medico com a situacao do paciente.
    Use 'dar_resumo' para fornecer um resumo completo do prontuario.
    Use 'dar_sugestao' para sugerir proximos passos clinicos ao medico.
    Use 'buscar_artigos' quando o medico pedir artigos ou evidencias cientificas.
    Quando precisar de dados estruturados, acione o subagente 'agente_contexto'.
    """,
    tools=[dar_resumo, dar_sugestao, buscar_artigos],
    sub_agents=[agente_contexto],
)


__all__ = ["agente_medico", "dar_resumo", "dar_sugestao", "buscar_artigos"]
