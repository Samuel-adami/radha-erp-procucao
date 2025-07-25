import React from 'react';

const AUTO_OPTIONS = [
  // Atendimento
  { value: 'atendimento.cliente', label: 'Atendimento - Cliente' },
  { value: 'atendimento.codigo', label: 'Atendimento - Código' },
  { value: 'atendimento.procedencia', label: 'Atendimento - Procedência' },
  { value: 'atendimento.vendedor', label: 'Atendimento - Vendedor' },
  { value: 'atendimento.telefone', label: 'Atendimento - Telefone' },
  { value: 'atendimento.email', label: 'Atendimento - Email' },
  { value: 'atendimento.rua', label: 'Atendimento - Rua' },
  { value: 'atendimento.numero', label: 'Atendimento - Número' },
  { value: 'atendimento.cidade', label: 'Atendimento - Cidade' },
  { value: 'atendimento.estado', label: 'Atendimento - Estado' },
  { value: 'atendimento.cep', label: 'Atendimento - CEP' },
  { value: 'atendimento.projetos', label: 'Atendimento - Projetos' },
  { value: 'atendimento.previsao_fechamento', label: 'Atendimento - Previsão de Fechamento' },
  { value: 'atendimento.temperatura', label: 'Atendimento - Temperatura' },
  { value: 'atendimento.tem_especificador', label: 'Atendimento - Tem Especificador?' },
  { value: 'atendimento.especificador_nome', label: 'Atendimento - Nome do Especificador' },
  { value: 'atendimento.rt_percent', label: 'Atendimento - % RT' },
  { value: 'atendimento.entrega_diferente', label: 'Atendimento - Endereço de Entrega' },
  { value: 'atendimento.historico', label: 'Atendimento - Histórico' },
  // Empresa
  { value: 'empresa.razaoSocial', label: 'Empresa - Razão Social' },
  { value: 'empresa.nomeFantasia', label: 'Empresa - Nome Fantasia' },
  { value: 'empresa.cnpj', label: 'Empresa - CNPJ' },
  { value: 'empresa.inscricaoEstadual', label: 'Empresa - Inscrição Estadual' },
  { value: 'empresa.cep', label: 'Empresa - CEP' },
  { value: 'empresa.rua', label: 'Empresa - Rua' },
  { value: 'empresa.numero', label: 'Empresa - Número' },
  { value: 'empresa.bairro', label: 'Empresa - Bairro' },
  { value: 'empresa.cidade', label: 'Empresa - Cidade' },
  { value: 'empresa.estado', label: 'Empresa - Estado' },
  { value: 'empresa.telefone1', label: 'Empresa - Telefone 1' },
  { value: 'empresa.telefone2', label: 'Empresa - Telefone 2' },
  { value: 'empresa.dados_completos', label: 'Empresa - Dados Completos' },
  { value: 'empresa.cabecalho', label: 'Cabeçalho Empresa' },
  { value: 'cliente.cabecalho_com_cpf', label: 'Cabeçalho Cliente c/ CPF' },
  { value: 'cliente.cabecalho_sem_cpf', label: 'Cabeçalho Cliente s/ CPF' },
  // Negociação
  { value: 'negociacao.pontuacao', label: 'Negociação - Pontuação' },
  { value: 'negociacao.desconto1', label: 'Negociação - Desconto 1' },
  { value: 'negociacao.desconto2', label: 'Negociação - Desconto 2' },
  { value: 'negociacao.entrada', label: 'Negociação - Entrada' },
  { value: 'negociacao.numParcelas', label: 'Negociação - Nº Parcelas' },
  { value: 'negociacao.condicao', label: 'Negociação - Condição Pagamento' },
  { value: 'negociacao.total', label: 'Negociação - Total' },
  { value: 'negociacao.descricao_pagamento', label: 'Negociação - Descrição Pagamento' },
  { value: 'negociacao.tabela', label: 'Tabela Negociação' },
];

function AutoFieldSelect({ value, onChange }) {
  return (
    <select className="input" value={value || ''} onChange={e => onChange(e.target.value)}>
      <option value="">Selecione</option>
      {AUTO_OPTIONS.map(opt => (
        <option key={opt.value} value={opt.value}>{opt.label}</option>
      ))}
    </select>
  );
}

export default AutoFieldSelect;
