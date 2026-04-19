from fastapi import FastAPI

# função fábrica: recebe qualquer objeto "agente" que
# tenha o método execute() e devolve uma app FastAPI pronta
def create_app(agent):
    app = FastAPI()   # cria a instância do servidor web

    # decorador que registra a função abaixo como handler
    # do método POST no caminho "/run"
    @app.post("/run")
    async def run(payload: dict):   # payload = JSON recebido no corpo
        # delega a execução ao agente e retorna o resultado
        return await agent.execute(payload)

    return app   # retorna a app configurada para ser usada pelo uvicorn