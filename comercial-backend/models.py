from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, Float

Base = declarative_base()

class Atendimento(Base):
    __tablename__ = "atendimentos"

    id = Column(Integer, primary_key=True)
    cliente = Column(String)
    codigo = Column(String)
    projetos = Column(String)
    previsao_fechamento = Column(String)
    temperatura = Column(String)
    tem_especificador = Column(Integer)
    especificador_nome = Column(String)
    rt_percent = Column(Float)
    entrega_diferente = Column(Integer)
    historico = Column(String)
    arquivos_json = Column(String)
    procedencia = Column(String)
    vendedor = Column(String)
    telefone = Column(String)
    email = Column(String)
    rua = Column(String)
    numero = Column(String)
    complemento = Column(String)
    bairro = Column(String)
    cidade = Column(String)
    estado = Column(String)
    cep = Column(String)
    data_cadastro = Column(String)

class AtendimentoTarefa(Base):
    __tablename__ = "atendimento_tarefas"

    id = Column(Integer, primary_key=True)
    atendimento_id = Column(Integer)
    nome = Column(String)
    concluida = Column(Integer)
    dados = Column(String)
    data_execucao = Column(String)

class CondicaoPagamento(Base):
    __tablename__ = "condicoes_pagamento"

    id = Column(Integer, primary_key=True)
    nome = Column(String)
    numero_parcelas = Column(Integer)
    juros_parcela = Column(Float)
    dias_vencimento = Column(String)
    ativa = Column(Integer)
    parcelas_json = Column(String)

class Template(Base):
    __tablename__ = "templates"

    id = Column(Integer, primary_key=True)
    tipo = Column(String)
    titulo = Column(String)
    campos_json = Column(String)
