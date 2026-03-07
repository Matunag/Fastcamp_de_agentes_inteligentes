from fastapi import FastAPI
def create_app(agent): # Função para criar aplicação
    app = FastAPI()
    @app.post("/run") # Quando uma requisição do tipo post acontece no caminho /run
    async def run(payload: dict): # Isso vai ser executado
        return await agent.execute(payload)
    return app

# No final, cria uma instância do FastAPI configurada com um "post"