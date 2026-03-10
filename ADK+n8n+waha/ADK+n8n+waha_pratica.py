from fastapi import FastAPI
from google.adk.agents import Agent
import requests
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
import uvicorn
from pydantic import BaseModel
app = FastAPI()
   

def send_message(chat_id, payload):
    """
    Envia uma mensagem para o usuário via API WAHA.
    """

    try:
        response = requests.post(
            "http://localhost:3000/api/sendText",
            headers={"X-Api-Key": "chave_api"},
            json={
                "chatId": chat_id,
                "text": payload,
                "session": "default"
            },
            timeout=10
        )

        response.raise_for_status()

        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"Erro ao enviar mensagem: {e}")
        return None


def get_products() -> dict:
    """Retorna a lista de todos os produtos disponíveis na loja."""
    return {
        "produtos": [
            {"id": 1, "nome": "Camiseta Básica", "preco": 49.90, "categoria": "Roupas"},
            {"id": 2, "nome": "Calça Jeans", "preco": 129.90, "categoria": "Roupas"},
            {"id": 3, "nome": "Tênis Esportivo", "preco": 249.90, "categoria": "Calçados"},
            {"id": 4, "nome": "Mochila Casual", "preco": 89.90, "categoria": "Acessórios"},
            {"id": 5, "nome": "Boné Aba Curva", "preco": 39.90, "categoria": "Acessórios"},
        ]
    }


def get_product_by_id(product_id: int) -> dict:
    """
    Retorna as informações detalhadas de um produto pelo ID.
    """
    produtos = {
        1: {"id": 1, "nome": "Camiseta Básica", "preco": 49.90, "categoria": "Roupas", "estoque": 15, "descricao": "Camiseta 100% algodão, disponível em P, M, G e GG"},
        2: {"id": 2, "nome": "Calça Jeans", "preco": 129.90, "categoria": "Roupas", "estoque": 8, "descricao": "Calça jeans slim fit, numeração 36 ao 48"},
        3: {"id": 3, "nome": "Tênis Esportivo", "preco": 249.90, "categoria": "Calçados", "estoque": 5, "descricao": "Tênis para corrida, numeração 37 ao 44"},
        4: {"id": 4, "nome": "Mochila Casual", "preco": 89.90, "categoria": "Acessórios", "estoque": 12, "descricao": "Mochila com compartimento para notebook de até 15 polegadas"},
        5: {"id": 5, "nome": "Boné Aba Curva", "preco": 39.90, "categoria": "Acessórios", "estoque": 20, "descricao": "Boné unissex, tamanho único com ajuste traseiro"},
    }
    
    produto = produtos.get(product_id)
    if not produto:
        return {"erro": f"Produto com ID {product_id} não encontrado."}
    return produto


def get_contacts() -> dict:
    """Retorna a lista de contatos/atendentes disponíveis para redirecionamento."""
    return {
        "contatos": [
            {"id": 1, "nome": "Mariana", "setor": "Compras"},
            {"id": 2, "nome": "João", "setor": "Reclamações"},
            {"id": 3, "nome": "Ana", "setor": "Suporte técnico"},
            {"id": 4, "nome": "Paulo", "setor": "Dúvidas"},
        ]
    }


def redirecionar(contact_id: int) -> dict:
    """
    Redireciona o usuário para o atendente especificado pelo ID.
    """
    contatos = {
        1: {"nome": "Mariana", "setor": "Compras", "contato": "mariana@loja.com"},
        2: {"nome": "João", "setor": "Reclamações", "contato": "joao@loja.com"},
        3: {"nome": "Ana", "setor": "Suporte técnico", "contato": "ana@loja.com"},
        4: {"nome": "Paulo", "setor": "Dúvidas", "contato": "paulo@loja.com"},
    }

    contato = contatos.get(contact_id)
    if not contato:
        return {"erro": f"Contato com ID {contact_id} não encontrado."}
    
    return {
        "mensagem": f"Redirecionando para {contato['nome']} do setor de {contato['setor']}.",
        "contato": contato['contato']
    }


def get_functions() -> dict:
    """Retorna as funcionalidades disponíveis no sistema de chatbot."""
    return {
        "funcionalidades": [
            {"id": 1, "descricao": "Ver lista de produtos disponíveis"},
            {"id": 2, "descricao": "Consultar informações de um produto específico"},
            {"id": 3, "descricao": "Ver lista de atendentes disponíveis"},
            {"id": 4, "descricao": "Ser redirecionado para um atendente"},
        ]
    }



produtos_agente = Agent(
name = "produtos_agente",
model = "gemini-2.5-flash",
description = "agente responsável pelos produtos",
instruction = ("você é um agente parte de um sistema de chatbot para uma loja"
"Sua responsabilidade é dar suporte ao usuário mostrando os produtos"
"Se for pedido uma lista dos produtos disponíveis, use a ferramenta ‘get_products'"
"Se for pedido as informações de um produto específico use a ferramenta ‘get_products_by_id'"
	),
tools = [get_products, get_product_by_id]
)

agente_redirecionador = Agent(
name = "agente_redirecionador",
model = "gemini-2.5-flash",
description = "agente responsável por redirecionar o usuário para outro atendente",
instruction = ("você é um agente parte de um sistema de chatbot para uma loja"
"Sua responsabilidade é passar para outro atendente caso o usuário pedir"
"Se for pedido uma lista dos contatos disponíveis, use a ferramenta 'get_contacts'"
"Se for pedido para você redirecionar para outro contato, use a ferramenta 'redirecionar'"
"Aqui estão os possíveis contatos:"
"ID 1: Atendente para compras (Mariana)"
"ID 2: Reclamações (João)"
"ID 3: Suporte técnico (Ana)"
"ID 4: Dúvidas (Paulo)"
	),
tools=[get_contacts, redirecionar]
)


orquestrador = Agent(
    name="Orquestrador",
    model="gemini-2.5-flash",
    description="Organizador geral do sistema",
    instruction=(
        "Você é um agente orquestrador de um sistema de chatbot no whatsapp para uma loja"
        "Assim que você for chamado use a ferramenta 'get_functions' para mostrar ao usuário o que você pode fazer"
        "Você também tem dois agentes a sua disposição, para cuidar dos produtos use o 'produtos_agente', para cuidar de redirecionamentos de contatos use o 'agente_redirecionador'"
    ),
    tools=[get_functions],
    sub_agents=[produtos_agente, agente_redirecionador]
)

session_service = InMemorySessionService()
runner = Runner(
    agent=orquestrador,
    app_name="chatbot_app",
    session_service=session_service
)

class Payload(BaseModel):
    mensagem: str
    chat_id: str

@app.post("/run")
async def run (payload: Payload):
    session_id = payload.chat_id.replace("@", "_").replace(".", "_")
    try:
        await session_service.create_session(app_name="chatbot_app", user_id=session_id, session_id=session_id)
    except:
        pass
    message = types.Content(role="user", parts=[types.Part(text=payload.mensagem)])
    async for event in runner.run_async(user_id=session_id, session_id=session_id, new_message=message):
        if event.is_final_response():
            resposta = event.content.parts[0].text
            #send_message(chat_id=payload.chat_id, payload=resposta)  estava dando problema então fiz esse passo no n8n.
            return {"resposta": event.content.parts[0].text}