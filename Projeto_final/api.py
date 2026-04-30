import os
import ast
from typing import Any, Dict, Tuple

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from Agentes.agente_paciente import agente_paciente

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()


def _normalizar_url(valor: str) -> str:
    """Sanitiza a URL lida do .env, removendo aspas extras, espaços
    e barras finais. Também desempacota listas/tuplas com um único elemento,
    caso o valor tenha sido gravado como representação Python (ex: "['http://...']").
    """
    if not valor:
        return ""
    bruto = valor.strip()
    try:
        # Tenta interpretar como literal Python para detectar listas/tuplas
        parsed = ast.literal_eval(bruto)
        if isinstance(parsed, (list, tuple)) and len(parsed) == 1 and isinstance(parsed[0], str):
            return parsed[0].strip().rstrip("/")
    except Exception:
        pass
    # Fallback: remove aspas e barras finais manualmente
    return bruto.strip().strip('"').strip("'").rstrip("/")


# Configurações do servidor WAHA (WhatsApp HTTP API) lidas do .env
WAHA_URL = _normalizar_url(os.getenv("WAHA_URL", "http://docker.host.internal:3000"))
WAHA_API_KEY = os.getenv("WAHA_API_KEY", "")
WAHA_SESSION = os.getenv("WAHA_SESSION", "default")

# Instancia a aplicação FastAPI
app = FastAPI(title="Paciente Webhook")

# Serviço de sessões em memória — mantém o histórico de cada conversa por user_id
session_service = InMemorySessionService()

# Runner conecta o agente do paciente ao serviço de sessões
runner = Runner(
    agent=agente_paciente,
    app_name="paciente_whatsapp_app",
    session_service=session_service
)


def _extrair_mensagem(dados: Dict[str, Any]) -> Tuple[str, str, bool]:
    """Extrai os campos essenciais do payload recebido pelo webhook.
    """
    payload = dados.get("payload", dados)  # Alguns eventos encapsulam em "payload"
    texto = payload.get("body") or payload.get("text") or payload.get("message") or ""
    chat_id = payload.get("chatId") or payload.get("from") or payload.get("chat_id") or ""
    from_me = payload.get("fromMe") or payload.get("from_me") or False

    # Normaliza o campo fromMe para booleano (pode vir como string "true"/"false")
    if isinstance(from_me, str):
        from_me = from_me.lower() == "true" # Retorna true caso a mensagem for do próprio usuário
    return texto, chat_id, bool(from_me) 


def _enviar_whatsapp(chat_id: str, texto: str) -> None:
    """Envia uma mensagem de texto para o paciente via API WAHA.
    """
    if not WAHA_URL:
        raise RuntimeError("WAHA_URL nao configurado.")

    url = f"{WAHA_URL}/api/sendText"
    payload = {
        "session": WAHA_SESSION,
        "chatId": chat_id,
        "text": texto,
    }

    # Adiciona autenticação por API Key, se configurada
    headers = {}
    if WAHA_API_KEY:
        headers["X-Api-Key"] = WAHA_API_KEY

    resposta = requests.post(url, json=payload, headers=headers, timeout=30)
    resposta.raise_for_status()  # Lança exceção para status 4xx/5xx


async def _chamar_agente_paciente(mensagem: str, user_id: str) -> str:
    """Cria ou reutiliza uma sessão para o usuário e executa o agente de forma
    assíncrona. Itera pelos eventos do runner e retorna o texto da resposta final, assim como nas execuções anteriores.
    """
    session_id = f"sessao_{user_id}"

    try:
        # Tenta criar a sessão; ignora se já existir
        await session_service.create_session(
            app_name="paciente_whatsapp_app",
            user_id=user_id,
            session_id=session_id
        )
    except Exception:
        pass  # Sessão já existe — comportamento esperado em múltiplas mensagens

    # Empacota a mensagem no formato esperado pelo ADK
    message = types.Content(role="user", parts=[types.Part(text=mensagem)])

    # Itera pelos eventos do agente até encontrar a resposta final
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=message
    ):
        if event.is_final_response():
            content = getattr(event, "content", None)
            if content and getattr(content, "parts", None):
                for part in content.parts:
                    texto = getattr(part, "text", None)
                    if texto:
                        return texto
            return "Nao foi possivel obter resposta do agente."

    return "Nao foi possivel obter resposta do agente."

# Configura uma requisição do tipo post nesse caminho.
@app.post("/webhook")
async def webhook(request: Request):
    """Endpoint principal do webhook, chamado pela API WAHA a cada mensagem recebida.
    """
    dados = await request.json()

    # Ignora eventos que não são mensagens (ex: "message.ack", "session.status")
    event = dados.get("event", "")
    if event and event != "message":
        print(f"[WEBHOOK] Ignorando evento: {event}")
        return {"status": "ok"}

    payload = dados.get("payload", dados)

    # Ignora mensagens de mídia sem texto associado (áudio, imagem, vídeo puro)
    if payload.get("hasMedia") and not payload.get("body"):
        print(f"[WEBHOOK] Ignorando mensagem com mídia sem texto (áudio/imagem/vídeo)")
        return {"status": "ok"}

    texto, chat_id, from_me = _extrair_mensagem(dados) # Seleciona os campos essenciais.

    # Payload inválido se não houver texto ou destinatário identificado
    if not texto or not chat_id:
        raise HTTPException(status_code=400, detail="Payload invalido.")

    # Chama o agente e trata erros de processamento sem derrubar o servidor
    try:
        resposta = await _chamar_agente_paciente(texto, user_id=chat_id)
        print(resposta)
    except Exception as exc:
        print(f"[WEBHOOK] Erro ao chamar agente: {exc}")
        return {"status": "error", "detail": "Erro interno ao processar a mensagem"}

    # Envia a resposta ao paciente via WAHA e trata falhas de envio separadamente
    try:
        _enviar_whatsapp(chat_id, resposta)
    except Exception as exc:
        print(f"[WEBHOOK] Erro ao enviar resposta no WhatsApp: {exc}")
        return {"status": "error", "detail": "Falha no envio da resposta"}

    return {"status": "ok"}
