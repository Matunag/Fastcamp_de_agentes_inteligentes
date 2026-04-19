import streamlit as st   # biblioteca que cria a interface web
import requests            # biblioteca para fazer requisições HTTP

# configura o título exibido na aba do navegador
st.set_page_config(page_title="teste")

# título principal exibido na página
st.title("Planejamento de rotina de treino e dieta")

# cada st.text_input cria um campo de texto na interface.
# o valor digitado pelo usuário fica armazenado na variável.
objetivo             = st.text_input("Qual é seu objetivo?", placeholder="ex: emagrecer")
orcamento            = st.text_input("Orçamento:",           placeholder="ex: 400 reais")
limitacoes           = st.text_input("Limitação:",           placeholder="ex: celíaco")
disponibilidade_dias = st.text_input("Dias na semana:",      placeholder="ex: 4 dias")
disponibilidade_min  = st.text_input("Minutos no dia:",      placeholder="ex: 60 minutos")
condicionamento      = st.text_input("Condicionamento:",     placeholder="ex: Sedentário")

# st.button retorna True apenas quando o usuário clicar no botão
if st.button("Faça meu planejamento:"):

    # all([...]) verifica se nenhum campo está vazio
    if not all([objetivo, orcamento, limitacoes,
                disponibilidade_dias, disponibilidade_min, condicionamento]):
        st.warning("Preencha todos os campos.")   # aviso se algo faltou
    else:
        # monta o dicionário que será serializado como JSON e
        # enviado ao servidor do orquestrador
        payload = {
            "objetivo":             objetivo,
            "orcamento":            orcamento,
            "limitacoes":           limitacoes,
            "disponibilidade_dias": disponibilidade_dias,
            "disponibilidade_minutos": disponibilidade_min,
            "condicionamento":      condicionamento
        }

        # faz a requisição POST para o orquestrador (porta 8000)
        # passando os dados como JSON no corpo da requisição
        response = requests.post("http://localhost:8000/run", json=payload)

        if response.ok:               # código HTTP 2xx = sucesso
            data = response.json()   # converte a resposta JSON em dict Python

            # renderiza cada seção da resposta usando Markdown
            st.subheader("🏋️ Treino")
            st.markdown(data["treino"])

            st.subheader("🥗🍗 Dieta")
            st.markdown(data["dieta"])

            st.subheader("✨ Motivação")
            st.markdown(data["motivacao"])
        else:
            st.error("Erro ao montar a rotina, tente novamente.")