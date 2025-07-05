from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, Float

Base = declarative_base()

class Chapa(Base):
    __tablename__ = "chapas"

    id = Column(Integer, primary_key=True)
    possui_veio = Column(Integer)
    propriedade = Column(String)
    espessura = Column(Float)
    comprimento = Column(Float)
    largura = Column(Float)

class Lote(Base):
    __tablename__ = "lotes"

    id = Column(Integer, primary_key=True)
    pasta = Column(String)
    criado_em = Column(String)

class Nesting(Base):
    __tablename__ = "nestings"

    id = Column(Integer, primary_key=True)
    lote = Column(String)
    pasta_resultado = Column(String)
    criado_em = Column(String)
