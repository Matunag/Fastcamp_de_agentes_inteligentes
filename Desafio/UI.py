import streamlit as st
import asyncio
import nest_asyncio
from orquestrador import buscar

nest_asyncio.apply()  # ← permite reusar o event loop do Streamlit

st.title("Chatbot 🤖")

if "mensagens" not in st.session_state:
    st.session_state.mensagens = []

for msg in st.session_state.mensagens:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if prompt := st.chat_input("Digite sua mensagem..."):
    st.session_state.mensagens.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    loop = asyncio.get_event_loop()  # ← pega o loop existente
    resposta = loop.run_until_complete(buscar(prompt, user_id="usuario_streamlit"))  # ← usa ele

    st.session_state.mensagens.append({"role": "assistant", "content": resposta})
    with st.chat_message("assistant"):
        st.write(resposta)