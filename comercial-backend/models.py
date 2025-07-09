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


class ProjetoItem(Base):
    """Itens gerados nas etapas de orçamento/projeto."""

    __tablename__ = "projeto_itens"

    id = Column(Integer, primary_key=True)
    atendimento_id = Column(Integer)
    tarefa_id = Column(Integer)
    ambiente = Column(String)
    descricao = Column(String)
    unitario = Column(Float)
    quantidade = Column(Integer)
    total = Column(Float)


class GabsterProjetoItem(Base):
    """Itens originais importados via API Gabster."""

    __tablename__ = "gabster_projeto_itens"

    pk = Column(Integer, primary_key=True)
    atendimento_id = Column(Integer)
    tarefa_id = Column(Integer)
    cd_acabamento = Column(Integer)
    cd_componente = Column(Integer)
    cd_orcamento_cliente = Column(Integer)
    cd_produto = Column(Integer)
    cd_usuario_cadastro = Column(Integer)
    cd_usuario_modificacao = Column(Integer)
    codigo_montagem = Column(Integer)
    comprimento = Column(String)
    datahora_cadastro = Column(String)
    datahora_cancelamento = Column(String)
    datahora_modificacao = Column(String)
    espessura_altura = Column(String)
    guid = Column(String)
    gabster_id = Column("id", Integer)
    largura_profundidade = Column(String)
    quantidade = Column(Integer)
    referencia = Column(String)
    valor = Column(Float)
