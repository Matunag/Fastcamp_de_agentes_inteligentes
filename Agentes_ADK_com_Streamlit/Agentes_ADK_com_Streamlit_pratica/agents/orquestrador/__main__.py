from common.a2a_server import create_app
from .task_manager      import run

# cria um objeto anônimo "Agent" com o método execute apontando para run()
# type("Agent", (), {...}) é equivalente a criar uma classe com um atributo
# — truque para adaptar run() à interface esperada por create_app()
app = create_app(agent=type("Agent", (), {"execute": run}))

# bloco executado apenas quando rodamos este arquivo diretamente
# (python -m agents.orquestrador), não quando importado
if __name__ == "__main__":
    import uvicorn
    # uvicorn é o servidor ASGI que roda a app FastAPI assíncrona
    # porta 8000 = endereço acessado pelo Streamlit
    uvicorn.run(app, port=8000)