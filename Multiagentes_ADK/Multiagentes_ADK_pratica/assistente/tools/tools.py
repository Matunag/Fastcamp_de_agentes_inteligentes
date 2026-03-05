# para rodar essa ferramenta é necessário dar um pip install requests no terminal

import requests
from datetime import datetime
from google.adk.tools import ToolContext


OPENWEATHER_API_KEY = "CHAVE_API"


def obter_clima(cidade: str, tool_context: ToolContext):
    """
    Retorna o clima atual de uma cidade usando OpenWeatherMap.
    """

    url = "https://api.openweathermap.org/data/2.5/weather"

    params = {
        "q": cidade,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
        "lang": "pt_br"
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        dados = response.json()

        clima = {
            "cidade": dados["name"],
            "temperatura_c": dados["main"]["temp"],
            "sensacao_termica_c": dados["main"]["feels_like"],
            "umidade_percentual": dados["main"]["humidity"],
            "descricao": dados["weather"][0]["description"],
            "vento_m_s": dados["wind"]["speed"],
            "atualizado_em": datetime.fromtimestamp(
                dados["dt"]
            ).strftime("%Y-%m-%d %H:%M:%S")
        }

        return {
            "status": "sucesso",
            "clima": clima
        }

    except requests.exceptions.RequestException as e:
        return {
            "status": "erro",
            "mensagem": f"Erro ao consultar API: {str(e)}"
        }

    except KeyError:
        return {
            "status": "erro",
            "mensagem": "Cidade não encontrada ou resposta inválida."
        }