# Classe usando o pydantic para padronização de entradas.
from pydantic import BaseModel
class TravelRequest(BaseModel):
    destination: str
    start_date: str
    end_date: str
    budget: float