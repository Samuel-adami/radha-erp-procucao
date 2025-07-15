from pydantic import BaseModel
from typing import List, Optional


class PublicoAlvo(BaseModel):
    id: Optional[int] = None
    nome: str
    descricao: str
    idade_min: Optional[int] = None
    idade_max: Optional[int] = None
    genero: Optional[str] = None
    interesses: Optional[List[str]] = None
    localizacao: Optional[str] = None

