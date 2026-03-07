from common.a2a_client import call_agent
TREINO_URL = "http://localhost:8001/run"
MOTIVACAO_URL = "http://localhost:8002/run"
DIETA_URL = "http://localhost:8003/run"

async def run(payload):
    print("Incoming payload:", payload)
    treino = await call_agent(TREINO_URL, payload)
    motivacao = await call_agent(MOTIVACAO_URL, payload)
    dieta = await call_agent(DIETA_URL, payload)
    print("treino:", treino)
    print("dieta:", dieta)
    print("motivação:", motivacao)
    treino = treino if isinstance(treino, dict) else {}
    dieta = dieta if isinstance(dieta, dict) else {}
    motivacao = motivacao if isinstance(motivacao, dict) else {}
    return {
        "treino": treino.get("treino", "Treino não retornado."),
        "dieta": dieta.get("dieta", "Dieta não retornado."),
        "motivacao": motivacao.get("motivacao", "Motivação não retornado.")
    }
