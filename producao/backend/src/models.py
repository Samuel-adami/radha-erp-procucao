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
    obj_key = Column(String)
    criado_em = Column(String)

class Nesting(Base):
    __tablename__ = "nestings"

    id = Column(Integer, primary_key=True)
    lote = Column(String)
    obj_key = Column(String)
    criado_em = Column(String)


class LoteOcorrencia(Base):
    """Representa um lote de ocorrência gerado pelo backend."""

    __tablename__ = "lotes_ocorrencias"

    id = Column(Integer, primary_key=True)
    lote = Column(String)
    pacote = Column(String)
    oc_numero = Column(Integer)
    obj_key = Column(String)
    criado_em = Column(String)


class OcorrenciaPeca(Base):
    """Peças pertencentes a um lote de ocorrência."""

    __tablename__ = "ocorrencias_pecas"

    id = Column(Integer, primary_key=True)
    oc_id = Column(Integer)
    peca_id = Column(Integer)
    descricao_peca = Column(String)
    motivo_id = Column(String)


class MotivoOcorrencia(Base):
    """Motivos cadastrados para ocorrências."""

    __tablename__ = "motivos_ocorrencia"

    codigo = Column(String, primary_key=True)
    descricao = Column(String)
    tipo = Column(String)
    setor = Column(String)


class ConfigMaquina(Base):
    """Configurações persistidas da máquina de corte."""

    __tablename__ = "config_maquina"

    id = Column(Integer, primary_key=True)
    dados = Column(String)


class ConfigFerramentas(Base):
    """Lista de ferramentas cadastradas para o nesting."""

    __tablename__ = "config_ferramentas"

    id = Column(Integer, primary_key=True)
    dados = Column(String)


class ConfigCortes(Base):
    """Parâmetros de corte padrão utilizados no nesting."""

    __tablename__ = "config_cortes"

    id = Column(Integer, primary_key=True)
    dados = Column(String)


class ConfigLayers(Base):
    """Definições de layers aplicadas aos desenhos DXF."""

    __tablename__ = "config_layers"

    id = Column(Integer, primary_key=True)
    dados = Column(String)
