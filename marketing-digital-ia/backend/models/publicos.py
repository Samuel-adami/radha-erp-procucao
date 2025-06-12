from pydantic import BaseModel

class PublicoAlvo(BaseModel):
    nome: str
    descricao: str