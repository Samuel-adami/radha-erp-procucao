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


class LeadInfoDB(Base):
    """Informações adicionais sobre os leads importados."""

    __tablename__ = "leads_info"

    id = Column(Integer, primary_key=True)
    rd_id = Column(String, unique=True, nullable=False)
    estagio = Column(String, default="Lead Novo")
    descricao = Column(String)
    arquivos_json = Column(String)
    vendedor_id = Column(Integer)
    cliente_id = Column(Integer)
    atendimento_id = Column(Integer)


class RDStationTokenDB(Base):
    __tablename__ = "rdstation_tokens"

    id = Column(Integer, primary_key=True)
    account_id = Column(String, unique=True, nullable=False)
    access_token = Column(String)
    refresh_token = Column(String)
    expires_at = Column(Integer)
