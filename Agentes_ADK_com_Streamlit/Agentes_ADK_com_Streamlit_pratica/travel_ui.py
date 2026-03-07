import streamlit as st
import requests

st.set_page_config(page_title="teste")
st.title("Planejamento de rotina de treino e dieta")
objetivo = st.text_input("Qual é seu objetivo?", placeholder="ex: emagrecer")
orcamento = st.text_input("Orçamento:", placeholder="ex: 400 reais")
limitacao = st.text_input("Limitação:", placeholder="ex: celíaco")
disponibilidade_dias = st.text_input("Dias na semana:", placeholder="ex: 4 dias")
disponibilidade_minutos = st.text_input("Minutos no dia:", placeholder="ex: 60 minutos")
condicionamento = st.text_input("Condicionamento:", placeholder="ex: Sedentário")
if st.button("Faça meu planejamento:"):
    if not all([objetivo, orcamento, limitacao, disponibilidade_dias, disponibilidade_minutos, condicionamento]):
        st.warning("Preencha todos os campos.")
    else:
        payload = {
            "objetivo": objetivo,
            "orcamento": orcamento,
            "limitacao": limitacao,
            "disponibilidade_dias": disponibilidade_dias,
            "disponibilidade_minutos": disponibilidade_minutos,
            "condicionamento": condicionamento
        }
        response = requests.post("http://localhost:8000/run", json=payload)
        if response.ok:
            data = response.json()
            st.subheader("🏋️ Treino")
            st.markdown(data["treino"])
            st.subheader("🥗🍗 Dieta")
            st.markdown(data["dieta"])
            st.subheader("✨ Motivação")
            st.markdown(data["motivacao"])
        else:
            st.error("Erro ao montar a rotina, tente novamente.")
