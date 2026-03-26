import streamlit as st
import json
import os
import re
import asyncio
from datetime import datetime
from pydantic import BaseModel, ValidationError, field_validator
from dotenv import load_dotenv
import os

from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types

from Agentes.agente_medico import agente_medico

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
ARQUIVO = "pacientes.json"

session_service = InMemorySessionService()
runner = Runner(
    agent=agente_medico,
    app_name="chat_medico_app",
    session_service=session_service
)

def carregar_dados():
    if not os.path.exists(ARQUIVO):
        return {}
    try:
        with open(ARQUIVO, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def salvar_dados(dados):
    with open(ARQUIVO, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

def parse_data_hora(valor):
    try:
        return datetime.strptime(valor, "%d/%m/%Y %H:%M")
    except (TypeError, ValueError):
        return None

def validar_cpf(cpf):
    cpf_digits = re.sub(r"\D", "", cpf or "")
    if len(cpf_digits) != 11:
        raise ValueError("CPF deve ter 11 dígitos.")
    if cpf_digits == cpf_digits[0] * 11:
        raise ValueError("CPF inválido.")

    soma = sum(int(cpf_digits[i]) * (10 - i) for i in range(9))
    dig1 = (soma * 10) % 11
    dig1 = 0 if dig1 == 10 else dig1

    soma = sum(int(cpf_digits[i]) * (11 - i) for i in range(10))
    dig2 = (soma * 10) % 11
    dig2 = 0 if dig2 == 10 else dig2

    if cpf_digits[-2:] != f"{dig1}{dig2}":
        raise ValueError("CPF inválido.")

    return cpf_digits

def padronizar_whatsapp(whatsapp):
    digits = re.sub(r"\D", "", whatsapp or "")
    if digits == "":
        return ""
    if digits.startswith("55"):
        numero = digits[2:]
        if len(numero) not in (10, 11):
            raise ValueError("WhatsApp deve ter DDD + número.")
        return f"+55{numero}"
    if len(digits) not in (10, 11):
        raise ValueError("WhatsApp deve ter DDD + número.")
    return f"+55{digits}"

async def chamar_agente_medico(mensagem: str, user_id: str = "medico_ui") -> str:
    session_id = f"sessao_{user_id}"

    try:
        await session_service.create_session(
            app_name="chat_medico_app",
            user_id=user_id,
            session_id=session_id
        )
    except:
        pass

    message = types.Content(role="user", parts=[types.Part(text=mensagem)])

    agen = runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=message
    )
    try:
        async for event in agen:
            if event.is_final_response():
                content = getattr(event, "content", None)
                if content and getattr(content, "parts", None):
                    for part in content.parts:
                        texto = getattr(part, "text", None)
                        if texto:
                            return texto
                return "Nao foi possivel obter resposta do agente."
    finally:
        await agen.aclose()

    return "Nao foi possivel obter resposta do agente."

def executar_corrotina(coro):
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        tarefa = loop.create_task(coro)
        return loop.run_until_complete(tarefa)
    finally:
        loop.close()

class PacienteInput(BaseModel):
    nome: str
    cpf: str
    idade: int
    whatsapp: str
    sexo: str
    historico: str

    @field_validator("nome", "sexo", "historico")
    def campo_nao_vazio(cls, v):
        if not v or not v.strip():
            raise ValueError("Campo obrigatório.")
        return v.strip()

    @field_validator("cpf")
    def cpf_valido(cls, v):
        return validar_cpf(v)

    @field_validator("whatsapp")
    def whatsapp_padronizado(cls, v):
        return padronizar_whatsapp(v)

dados = carregar_dados()

st.title("Sistema de Registro de Pacientes")

menu = st.sidebar.selectbox(
    "Menu",
    [
        "Criar novo paciente",
        "Acessar paciente existente",
        "Chatbot do medico"
    ]
)

if menu == "Criar novo paciente":

    st.header("Novo Registro de Paciente")

    nome = st.text_input("Nome do paciente")
    cpf = st.text_input("CPF")
    idade = st.number_input("Idade", 0, 120)
    whatsapp = st.text_input("WhatsApp")
    sexo = st.selectbox("Sexo", ["Masculino", "Feminino", "Outro"])
    historico = st.text_area("Histórico médico relevante")

    if st.button("Criar registro"):
        try:
            paciente_input = PacienteInput(
                nome=nome,
                cpf=cpf,
                idade=idade,
                whatsapp=whatsapp,
                sexo=sexo,
                historico=historico
            )
        except ValidationError as exc:
            for erro in exc.errors():
                st.error(erro.get("msg", "Dados inválidos."))
        else:
            cpf_normalizado = paciente_input.cpf
            if cpf_normalizado in dados:
                st.error("Paciente já cadastrado!")
            else:
                dados[cpf_normalizado] = {
                    "nome": paciente_input.nome,
                    "idade": paciente_input.idade,
                    "whatsapp": paciente_input.whatsapp,
                    "sexo": paciente_input.sexo,
                    "historico": paciente_input.historico,
                    "consultas": [],
                    "agendamentos": []
                }

                salvar_dados(dados)
                st.success("Paciente criado com sucesso!")

elif menu == "Acessar paciente existente":

    st.header("Buscar paciente")

    cpf_busca = st.text_input("Digite o CPF do paciente")

    cpf_busca_normalizado = None
    if cpf_busca:
        try:
            cpf_busca_normalizado = validar_cpf(cpf_busca)
        except ValueError as exc:
            st.error(str(exc))

    if cpf_busca_normalizado in dados:

        paciente = dados[cpf_busca_normalizado]

        st.subheader("Informações do Paciente")

        st.write("Nome:", paciente["nome"])
        st.write("Idade:", paciente["idade"])
        st.write("Sexo:", paciente["sexo"])
        st.write("WhatsApp:", paciente.get("whatsapp", ""))
        st.write("Histórico:", paciente["historico"])

        st.divider()

        alertas_medico = paciente.get("alertas_medico", [])
        if alertas_medico:
            st.subheader("Alertas do médico")
            for alerta in reversed(alertas_medico):
                data_registro = alerta.get("data_registro", "Data não informada")
                motivo = alerta.get("motivo", "Motivo não informado")
                st.warning(f"{data_registro} - {motivo}")
            st.divider()

        agendamentos = paciente.get("agendamentos", [])
        agendamentos_futuros = []
        agora = datetime.now()

        for agendamento in agendamentos:
            data_hora = parse_data_hora(agendamento.get("data_hora"))
            if data_hora and data_hora >= agora:
                agendamentos_futuros.append((data_hora, agendamento))

        agendamentos_futuros.sort(key=lambda item: item[0])

        if agendamentos_futuros:
            st.subheader("Próximos agendamentos")
            proximo_dt, proximo_agendamento = agendamentos_futuros[0]
            st.info(
                f"Próxima consulta: {proximo_dt.strftime('%d/%m/%Y %H:%M')} "
                f"- {proximo_agendamento.get('especialidade', '')} "
                f"com {proximo_agendamento.get('profissional', '')}"
            )

            for data_hora, agendamento in agendamentos_futuros[1:3]:
                st.write(
                    f"- {data_hora.strftime('%d/%m/%Y %H:%M')} - "
                    f"{agendamento.get('especialidade', '')} com {agendamento.get('profissional', '')}"
                )

            st.divider()

        tabs = st.tabs(["Registrar consulta", "Marcar consulta", "Histórico"])

        with tabs[0]:
            st.subheader("Registrar nova consulta")

            sintomas = st.text_area("Sintomas relatados")
            diagnostico = st.text_area("Diagnóstico")
            tratamento = st.text_area("Tratamento / Prescrição")
            observacoes = st.text_area("Observações adicionais")

            if st.button("Salvar consulta"):

                consulta = {
                    "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "sintomas": sintomas,
                    "diagnostico": diagnostico,
                    "tratamento": tratamento,
                    "observacoes": observacoes
                }

                dados[cpf_busca_normalizado]["consultas"].append(consulta)

                salvar_dados(dados)

                st.success("Consulta registrada com sucesso!")

        with tabs[1]:
            st.subheader("Marcar uma consulta")

            data_consulta = st.date_input("Data da consulta")
            hora_consulta = st.time_input("Horário da consulta")
            especialidade = st.text_input("Especialidade")
            profissional = st.text_input("Profissional")
            local = st.text_input("Local")
            motivo = st.text_area("Motivo / Observações")

            if st.button("Agendar consulta"):
                data_hora_dt = datetime.combine(data_consulta, hora_consulta)
                data_hora = data_hora_dt.strftime("%d/%m/%Y %H:%M")

                erros = []
                if data_hora_dt < datetime.now():
                    erros.append("A data e horário devem ser no futuro.")
                if not especialidade.strip():
                    erros.append("Informe a especialidade.")
                if not profissional.strip():
                    erros.append("Informe o profissional.")
                if not local.strip():
                    erros.append("Informe o local.")

                conflitos = any(
                    a.get("data_hora") == data_hora
                    for a in dados[cpf_busca_normalizado].get("agendamentos", [])
                )
                if conflitos:
                    erros.append("Já existe uma consulta marcada para esse horário.")

                if erros:
                    for erro in erros:
                        st.error(erro)
                else:
                    agendamento = {
                        "data_hora": data_hora,
                        "especialidade": especialidade,
                        "profissional": profissional,
                        "local": local,
                        "motivo": motivo
                    }

                    dados[cpf_busca_normalizado].setdefault("agendamentos", [])
                    dados[cpf_busca_normalizado]["agendamentos"].append(agendamento)

                    salvar_dados(dados)

                    st.success("Consulta agendada com sucesso!")

        with tabs[2]:
            historico_tabs = st.tabs(["Consultas realizadas", "Consultas agendadas"])

            with historico_tabs[0]:
                st.subheader("Histórico de consultas")

                for consulta in reversed(paciente["consultas"]):
                    with st.expander(f"Consulta - {consulta['data']}"):
                        st.write("Sintomas:", consulta["sintomas"])
                        st.write("Diagnóstico:", consulta["diagnostico"])
                        st.write("Tratamento:", consulta["tratamento"])
                        st.write("Observações:", consulta["observacoes"])

            with historico_tabs[1]:
                st.subheader("Agendamentos")

                for agendamento in reversed(paciente.get("agendamentos", [])):
                    with st.expander(f"Consulta marcada - {agendamento['data_hora']}"):
                        st.write("Especialidade:", agendamento["especialidade"])
                        st.write("Profissional:", agendamento["profissional"])
                        st.write("Local:", agendamento["local"])
                        st.write("Motivo:", agendamento["motivo"])

    elif cpf_busca != "":
        st.error("Paciente não encontrado.")

elif menu == "Chatbot do medico":

    st.header("Chatbot do medico")
    st.caption("Converse com o agente medico sobre o paciente. Inclua o CPF na mensagem.")

    if "chat_medico" not in st.session_state:
        st.session_state.chat_medico = []

    for item in st.session_state.chat_medico:
        with st.chat_message(item["role"]):
            st.write(item["content"])

    mensagem = st.chat_input("Digite sua solicitacao")

    if mensagem:
        st.session_state.chat_medico.append({"role": "user", "content": mensagem})
        with st.chat_message("user"):
            st.write(mensagem)

        resposta = executar_corrotina(
            chamar_agente_medico(mensagem, user_id="medico_streamlit")
        )
        st.session_state.chat_medico.append({"role": "assistant", "content": resposta})
        with st.chat_message("assistant"):
            st.write(resposta)
