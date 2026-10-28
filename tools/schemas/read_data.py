
from pydantic import BaseModel, Field

NAME = "read_data"
DESCRIPTION = """Legge un file CSV semplice e restituisce i dati come una lista
    di dizionari. Il file deve avere una prima riga con i nomi delle 
    colonne e campi separati da virgole, senza virgole all'interno 
    dei valori. Se il file è vuoto, restituisce una lista vuota."""


class Parameters(BaseModel):
    percorso_file: str = Field(
        description="Percorso del file CSV da leggere."
    )
