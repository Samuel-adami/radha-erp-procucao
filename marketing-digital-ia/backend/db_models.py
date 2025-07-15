from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    password = Column(String)
    email = Column(String)
    nome = Column(String)
    cargo = Column(String)
    permissoes = Column(String)


class PublicoAlvoDB(Base):
    __tablename__ = "publicos_alvo"

    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False)
    descricao = Column(String)
    idade_min = Column(Integer)
    idade_max = Column(Integer)
    genero = Column(String)
    interesses = Column(String)
    localizacao = Column(String)
