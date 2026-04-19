# httpx é a versão assíncrona do requests — necessária dentro
# de funções async (como as do FastAPI e ADK)
import httpx

# função assíncrona: pode ser "pausada" enquanto aguarda a
# resposta HTTP sem bloquear o restante do programa
async def call_agent(url, payload):

    # cria um cliente HTTP assíncrono e garante que ele seja
    # fechado corretamente ao sair do bloco (with)
    async with httpx.AsyncClient() as client:

        # envia POST para a URL do agente-destino
        # timeout=60 evita que o programa trave se o agente demorar demais
        response = await client.post(url, json=payload, timeout=60.0)

        # lança exceção se o servidor retornar erro (4xx ou 5xx)
        response.raise_for_status()

        # retorna a resposta já convertida de JSON para dict Python
        return response.json()