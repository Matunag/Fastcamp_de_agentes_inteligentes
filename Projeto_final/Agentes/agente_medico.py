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

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

# Inicializa o cliente Mistral para geração de embeddings
mistral = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))

# Repassa a chave da Groq para o ambiente (usada internamente pelo ADK)
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")

# Inicializa o cliente Qdrant para busca vetorial de artigos científicos
qdrant = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY"),
    timeout=30  # Timeout de 30s para evitar travamentos em queries lentas
)


def _ultimo_registro(consultas: List[Dict[str, Any]]) -> Dict[str, Any] | None:
    """Auxiliar privado: retorna a última consulta da lista,
    ou None se a lista estiver vazia.
    """
    if not consultas:
        return None
    return consultas[-1]


def dar_resumo(cpf: str, tool_context: ToolContext) -> Dict[str, Any]:
    """
    Ferramenta que gera um resumo clínico textual do paciente.
    Inclui dados gerais, número de consultas, última consulta e observações.
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

    # Obtém a consulta mais recente para incluir no resumo
    ultima = _ultimo_registro(consultas)

    # Monta o texto de resumo com dados gerais do paciente
    resumo = (
        f"Paciente {paciente.get('nome')} ({paciente.get('idade')} anos, {paciente.get('sexo')}). "
        f"Historico: {paciente.get('historico')}. "
        f"Consultas registradas: {len(consultas)}. "
        f"Observacoes recentes do paciente: {len(observacoes)}."
    )

    # Acrescenta detalhes da última consulta, se existir
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
    Ferramenta que gera sugestões de próximos passos clínicos para o médico,
    com base no histórico registrado e possíveis alertas urgentes.
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

    # Sugestão diferente se não há nenhuma consulta registrada
    if not consultas:
        sugestao = (
            "Nao ha consultas registradas. Recomenda-se realizar uma avaliacao inicial "
            "e registrar sintomas, exames e plano terapeutico."
        )
    else:
        # Sugestão padrão de acompanhamento para pacientes com histórico
        sugestao = (
            "Sugestao inicial: revisar o tratamento atual, monitorar sintomas nas "
            "proximas 48-72h e considerar exames complementares se houver piora. "
            "Avaliar aderencia ao tratamento e fatores de risco."
        )

    # Adiciona alerta se houver observações recentes do paciente
    if observacoes:
        sugestao += " Ha observacoes recentes do paciente que podem exigir contato proativo."

    # Verifica se a última consulta contém marcador de urgência nas observações
    if ultima and "urg" in str(ultima.get("observacoes", "")).lower():
        sugestao += " Observacao de ultima consulta indica alerta; reavaliar prontamente."

    return {
        "status": "sucesso",
        "sugestao": sugestao,
    }


def buscar_artigos(query: str) -> Dict[str, Any]:
    """
    Ferramenta de busca semântica: converte a query em embedding usando a LLM Mistral
    e retorna os 3 artigos mais relevantes armazenados no Qdrant.
    """
    # Gera o embedding vetorial da query do médico
    result = mistral.embeddings.create(
        model="mistral-embed",
        inputs=[query]
    )
    embedding_query = result.data[0].embedding

    # Realiza a busca na coleção "Estudos"
    resultados = qdrant.query_points(
        collection_name="Estudos",
        query=embedding_query,
        limit=3  # Retorna os 3 artigos mais próximos semanticamente
    )

    # Formata os resultados extraindo score e texto do abstract
    artigos = []
    for r in resultados.points:
        artigos.append({
            "score": round(r.score, 4),       # Relevância do artigo (0 a 1)
            "abstract": r.payload.get("texto", ""),  # Texto do chunk indexado
        })

    return {"artigos": artigos}


# Definição do agente médico com suas 3 ferramentas e o subagente de contexto.
# Este agente é acionado pela UI (Streamlit) via chatbot do médico.
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
    sub_agents=[agente_contexto],  # Subagente para recuperação padronizada de dados
)


__all__ = ["agente_medico", "dar_resumo", "dar_sugestao", "buscar_artigos"]
