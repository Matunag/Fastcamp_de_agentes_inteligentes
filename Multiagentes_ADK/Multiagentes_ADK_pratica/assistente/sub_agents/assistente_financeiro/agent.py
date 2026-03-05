# Importa as bibliotecas que serão usadas
from google.adk.agents import Agent
from datetime import datetime
from google.adk.tools import ToolContext


def registrar_despesa(
    valor: float,
    categoria: str,
    descricao: str,
    tool_context: ToolContext
):
    state = tool_context.state

    if "despesas" not in state:
        state["despesas"] = []

    nova_despesa = {
        "valor": valor,
        "categoria": categoria.lower(),
        "descricao": descricao,
        "data": datetime.now().strftime("%Y-%m-%d")
    }

    state["despesas"].append(nova_despesa)

    return {
        "status": "sucesso",
        "mensagem": f"Despesa registrada: R$ {valor:.2f} em {categoria}.",
        "despesa": nova_despesa
    }


def resumo_gastos_mes(tool_context: ToolContext):
    state = tool_context.state

    if "despesas" not in state or not state["despesas"]:
        return {
            "status": "sucesso",
            "mensagem": "Nenhuma despesa registrada.",
            "total_mes": 0,
            "por_categoria": {}
        }

    agora = datetime.now()
    mes_atual = agora.month
    ano_atual = agora.year

    total = 0
    por_categoria = {}

    for despesa in state["despesas"]:
        data_despesa = datetime.strptime(despesa["data"], "%Y-%m-%d")

        if data_despesa.month == mes_atual and data_despesa.year == ano_atual:
            valor = despesa["valor"]
            categoria = despesa["categoria"]

            total += valor

            if categoria not in por_categoria:
                por_categoria[categoria] = 0

            por_categoria[categoria] += valor

    return {
        "status": "sucesso",
        "mes_referencia": f"{mes_atual:02d}/{ano_atual}",
        "total_mes": round(total, 2),
        "por_categoria": {
            cat: round(valor, 2)
            for cat, valor in por_categoria.items()
        }
    }

# Criação do agente.
assistente_financeiro = Agent(
    name="assistente_financeiro",
    model="gemini-2.5-flash",
    description="Agente responsável por auxiliar no controle financeiro pessoal do usuário, registrando despesas e gerando relatórios mensais organizados.",
    instruction="""
    Você é um assistente financeiro pessoal.

    Seu papel é ajudar o usuário a registrar despesas e acompanhar seus gastos mensais.

    Regras de uso das ferramentas:

    1. Quando o usuário quiser registrar um gasto, compra ou pagamento,
       use a função 'registrar_despesa'.
       Sempre extraia:
       - valor
       - categoria
       - descricao

    2. Quando o usuário quiser saber quanto gastou no mês,
       ou pedir um resumo financeiro,
       use a função 'resumo_gastos_mes'.

    Ao responder:

    - Seja claro e objetivo.
    - Mostre o total gasto no mês.
    - Mostre a divisão por categoria.
    - Formate valores como moeda brasileira (R$).
    - Se não houver despesas registradas, informe isso claramente.
    """,
    tools=[registrar_despesa, resumo_gastos_mes],
)
