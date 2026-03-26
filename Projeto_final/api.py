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

load_dotenv()

def _normalizar_url(valor: str) -> str:
    if not valor:
        return ""
    bruto = valor.strip()
    try:
        parsed = ast.literal_eval(bruto)
        if isinstance(parsed, (list, tuple)) and len(parsed) == 1 and isinstance(parsed[0], str):
            return parsed[0].strip().rstrip("/")
    except Exception:
        pass
    return bruto.strip().strip('"').strip("'").rstrip("/")

WAHA_URL = _normalizar_url(os.getenv("WAHA_URL", "http://docker.host.internal:3000"))
WAHA_API_KEY = os.getenv("WAHA_API_KEY", "")
WAHA_SESSION = os.getenv("WAHA_SESSION", "default")

app = FastAPI(title="Paciente Webhook")

session_service = InMemorySessionService()
runner = Runner(
    agent=agente_paciente,
    app_name="paciente_whatsapp_app",
    session_service=session_service
)


def _extrair_mensagem(dados: Dict[str, Any]) -> Tuple[str, str, bool]:
    payload = dados.get("payload", dados)
    texto = payload.get("body") or payload.get("text") or payload.get("message") or ""
    chat_id = payload.get("chatId") or payload.get("from") or payload.get("chat_id") or ""
    from_me = payload.get("fromMe") or payload.get("from_me") or False
    if isinstance(from_me, str):
        from_me = from_me.lower() == "true"
    return texto, chat_id, bool(from_me)


def _enviar_whatsapp(chat_id: str, texto: str) -> None:
    if not WAHA_URL:
        raise RuntimeError("WAHA_URL nao configurado.")

    url = f"{WAHA_URL}/api/sendText"
    payload = {
        "session": WAHA_SESSION,
        "chatId": chat_id,
        "text": texto,
    }
    headers = {}
    if WAHA_API_KEY:
        headers["X-Api-Key"] = WAHA_API_KEY

    resposta = requests.post(url, json=payload, headers=headers, timeout=30)
    resposta.raise_for_status()


async def _chamar_agente_paciente(mensagem: str, user_id: str) -> str:
    session_id = f"sessao_{user_id}"

    try:
        await session_service.create_session(
            app_name="paciente_whatsapp_app",
            user_id=user_id,
            session_id=session_id
        )
    except Exception:
        pass

    message = types.Content(role="user", parts=[types.Part(text=mensagem)])

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


@app.post("/webhook")
async def webhook(request: Request):
    dados = await request.json()

    # Ignorar eventos que não são mensagens (status, etc)
    event = dados.get("event", "")
    if event and event != "message":
        print(f"[WEBHOOK] Ignorando evento: {event}")
        return {"status": "ok"}

    payload = dados.get("payload", dados)

    # Ignorar mensagens sem texto (áudio, imagem, etc)
    if payload.get("hasMedia") and not payload.get("body"):
        print(f"[WEBHOOK] Ignorando mensagem com mídia sem texto (áudio/imagem/vídeo)")
        return {"status": "ok"}

    texto, chat_id, from_me = _extrair_mensagem(dados)


    if not texto or not chat_id:
        raise HTTPException(status_code=400, detail="Payload invalido.")

    try:
        resposta = await _chamar_agente_paciente(texto, user_id=chat_id)
        print(resposta)
    except Exception as exc:
        print(f"[WEBHOOK] Erro ao chamar agente: {exc}")
        return {"status": "error", "detail": "Erro interno ao processar a mensagem"}

    try:
        _enviar_whatsapp(chat_id, resposta)
    except Exception as exc:
        print(f"[WEBHOOK] Erro ao enviar resposta no WhatsApp: {exc}")
        return {"status": "error", "detail": "Falha no envio da resposta"}

    return {"status": "ok"}
