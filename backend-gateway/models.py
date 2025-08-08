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


class Cliente(Base):
    """Cadastro de clientes."""

    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True)
    codigo = Column(String)
    nome = Column(String)
    documento = Column(String)

    # Campos enviados pelo frontend em camelCase
    rgIe = Column("rg_ie", String)
    sexo = Column(String)
    dataNascimento = Column("data_nascimento", String)

    telefone1 = Column(String)
    telefone2 = Column(String)
    pais = Column(String)
    profissao = Column(String)
    cep = Column(String)
    cidade = Column(String)
    estado = Column(String)
    endereco = Column(String)
    numero = Column(String)
    complemento = Column(String)
    bairro = Column(String)
    email = Column(String)

    # Novos campos de origem e status do imóvel
    procedencia = Column(String)
    estadoImovel = Column("estado_imovel", String)
    previsaoFechamento = Column("previsao_fechamento", String)


class Fornecedor(Base):
    """Cadastro de fornecedores."""

    __tablename__ = "fornecedores"

    id = Column(Integer, primary_key=True)
    nome = Column(String)
    contato = Column(String)


class User(Base):
    """Tabela de usuários para autenticação."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    password = Column(String)
    email = Column(String)
    nome = Column(String)
    cargo = Column(String)
    permissoes = Column(String)


class DocumentoTreinamento(Base):
    """Armazena os documentos de treinamento enviados pela Universidade Radha."""

    __tablename__ = "documentos_treinamento"

    id = Column(Integer, primary_key=True)
    titulo = Column(String)
    autor = Column(String)
    data = Column(String)
    caminho = Column(String)


class LoteOcorrencia(Base):
    """Armazena lotes de ocorrências e metadados dos arquivos gerados."""

    __tablename__ = "lotes_ocorrencias"

    id = Column(Integer, primary_key=True)
    lote = Column(String)
    pacote = Column(String)
    oc_numero = Column(Integer)
    dados = Column(String)  # JSON com peças e outras informações estruturadas
    arquivo_key = Column(String)

