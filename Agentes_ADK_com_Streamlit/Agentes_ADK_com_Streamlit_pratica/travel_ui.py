import streamlit as st
import requests

st.set_page_config(page_title="ADK-Powered Travel Planner", page_icon="✈️")
st.title("🌍 ADK-Powered Travel Planner")
objetivo = st.text_input("Qual é seu objeto?", placeholder="ex: emagrecer")
orcamento = st.text_input("Orçamento:", placeholder="ex: 400 reais")
limitacao = st.text_input("Limitação:", placeholder="ex: celíaco")
disponibilidade_dias = st.number_input("Dias na semana:", placeholder="ex: 4")
disponibilidade_minutos = st.number_input("Minutos no dia:", placeholder="ex: 60")
condicionamento = st.text_input("Limitação:", placeholder="ex: celíaco")
if st.button("Faça meu planejamento:"):
    if not all([objetivo, orcamento, limitacao, disponibilidade_dias, disponibilidade_minutos, ]):
        st.warning("Please fill in all the details.")
    else:
        payload = {
            "origin": origin,
            "destination": destination,
            "start_date": str(start_date),
            "end_date": str(end_date),
            "budget": budget
        }
        response = requests.post("http://localhost:8000/run", json=payload)
        if response.ok:
            data = response.json()
            st.subheader("✈️ Flights")
            st.markdown(data["flights"])
            st.subheader("🏨 Stays")
            st.markdown(data["stay"])
            st.subheader("🗺️ Activities")
            st.markdown(data["activities"])
        else:
            st.error("Failed to fetch travel plan. Please try again.")