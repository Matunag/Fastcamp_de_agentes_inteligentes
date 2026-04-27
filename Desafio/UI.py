import streamlit as st
import asyncio
import nest_asyncio
from orquestrador import buscar

nest_asyncio.apply()  # Permite reutilizar o event loop já existente no Streamlit

st.title("Chatbot 🤖")

# Inicializa o histórico de mensagens na sessão se ainda não existir
if "mensagens" not in st.session_state:
    st.session_state.mensagens = []

# Carrega as mensagens anteriores
for msg in st.session_state.mensagens:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if prompt := st.chat_input("Digite sua mensagem..."):
    # Adiciona a mensagem do usuário ao histórico e exibe na tela
    st.session_state.mensagens.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # Executa a busca de forma assíncrona reutilizando o event loop do Streamlit
    loop = asyncio.get_event_loop()
    resposta = loop.run_until_complete(buscar(prompt, user_id="usuario_streamlit"))

    # Adiciona a resposta do assistente ao histórico e exibe na tela
    st.session_state.mensagens.append({"role": "assistant", "content": resposta})
    with st.chat_message("assistant"):
        st.write(resposta)