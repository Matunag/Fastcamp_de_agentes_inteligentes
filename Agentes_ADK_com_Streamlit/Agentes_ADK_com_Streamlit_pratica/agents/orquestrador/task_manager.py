from common.a2a_client import call_agent

# endereços HTTP de cada agente especializado
# cada um roda em sua própria porta do localhost
TREINO_URL   = "http://localhost:8001/run"
MOTIVACAO_URL = "http://localhost:8002/run"
DIETA_URL    = "http://localhost:8003/run"

async def run(payload):
    print("Incoming payload:", payload)   # log para depuração

    # chama cada agente em sequência, passando o mesmo payload recebido do frontend
    # cada chamada aguarda (await) a resposta antes de continuar
    treino    = await call_agent(TREINO_URL,    payload)
    motivacao = await call_agent(MOTIVACAO_URL, payload)
    dieta     = await call_agent(DIETA_URL,     payload)

    print("treino:", treino)
    print("dieta:", dieta)
    print("motivação:", motivacao)

    # garante que cada resposta é um dicionário;
    # se o agente retornar algo inesperado, usa dict vazio como fallback
    treino    = treino    if isinstance(treino,    dict) else {}
    dieta     = dieta     if isinstance(dieta,     dict) else {}
    motivacao = motivacao if isinstance(motivacao, dict) else {}

    # consolida os três resultados em um único dict que o Streamlit vai exibir
    # .get() evita KeyError: usa a mensagem padrão se a chave não existir
    return {
        "treino":   treino.get("treino",    "Treino não retornado."),
        "dieta":    dieta.get("dieta",      "Dieta não retornada."),
        "motivacao": motivacao.get("motivacao", "Motivação não retornada.")
    }