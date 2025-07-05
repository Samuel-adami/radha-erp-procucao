from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, LargeBinary

Base = declarative_base()

class Empresa(Base):
    __tablename__ = "empresa"

    id = Column(Integer, primary_key=True)
    codigo = Column(String)
    razao_social = Column(String)
    nome_fantasia = Column(String)
    cnpj = Column(String)
    inscricao_estadual = Column(String)
    cep = Column(String)
    rua = Column(String)
    numero = Column(String)
    complemento = Column(String)
    bairro = Column(String)
    cidade = Column(String)
    estado = Column(String)
    telefone1 = Column(String)
    telefone2 = Column(String)
    slogan = Column(String)
    logo = Column(LargeBinary)
