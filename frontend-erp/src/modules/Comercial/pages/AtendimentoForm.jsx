import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../../Producao/components/ui/button';
import { fetchComAuth } from '../../../utils/fetchComAuth';

function AtendimentoForm() {
  const [form, setForm] = useState({
    cliente: '',
    codigo: '',
    projetos: '',
    previsao_fechamento: '',
    temperatura: '',
    tem_especificador: false,
    especificador_nome: '',
    rt_percent: '',
    historico: '',
  });
  const [sugestoesClientes, setSugestoesClientes] = useState([]);
  const [clienteInfo, setClienteInfo] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    const carregarCodigo = async () => {
      try {
        const resp = await fetchComAuth('/comercial/atendimentos/proximo-codigo');
        setForm(prev => ({ ...prev, codigo: resp.codigo }));
      } catch (err) {
        console.error('Erro ao obter código', err);
      }
    };
    carregarCodigo();
  }, []);

  const handle = campo => e => {
    const value =
      campo === 'tem_especificador' ? e.target.checked : e.target.value;
    setForm(prev => ({ ...prev, [campo]: value }));
  };

  const handleClienteChange = e => {
    const value = e.target.value;
    setForm(prev => ({ ...prev, cliente: value }));
    const lista = JSON.parse(localStorage.getItem('clientes') || '[]');
    if (value.length >= 3) {
      const termo = value.toLowerCase();
      setSugestoesClientes(
        lista.filter(c => c.nome && c.nome.toLowerCase().startsWith(termo))
      );
    } else {
      setSugestoesClientes([]);
    }
    const encontrado = lista.find(c => c.nome === value);
    setClienteInfo(encontrado || null);
  };

  const handleSubmit = async e => {
    e.preventDefault();
    try {
      await fetchComAuth('/comercial/atendimentos', {
        method: 'POST',
        body: JSON.stringify({
          ...form,
          tem_especificador: form.tem_especificador ? 1 : 0,
        }),
      });
      navigate('..');
    } catch (err) {
      console.error('Erro ao criar atendimento', err);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {clienteInfo && (
        <div className="p-2 bg-gray-100 rounded text-sm space-y-1">
          <div className="font-semibold">{clienteInfo.nome}</div>
          <div>{clienteInfo.endereco} {clienteInfo.numero} - {clienteInfo.bairro}</div>
          <div>{clienteInfo.cidade}/{clienteInfo.estado}</div>
          <div>Tel: {clienteInfo.telefone1}</div>
          <div>CPF/CNPJ: {clienteInfo.documento}</div>
        </div>
      )}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <label className="block">
          <span className="text-sm">Cliente</span>
          <input
            className="input"
            list="lista-clientes"
            value={form.cliente}
            onChange={handleClienteChange}
          />
          <datalist id="lista-clientes">
            {sugestoesClientes.map(c => (
              <option key={c.id} value={c.nome} />
            ))}
          </datalist>
        </label>
        <label className="block">
          <span className="text-sm">Código</span>
          <input
            className="input bg-gray-100"
            value={form.codigo}
            readOnly
          />
        </label>
        <label className="block md:col-span-2">
          <span className="text-sm">Projetos</span>
          <input
            className="input"
            value={form.projetos}
            onChange={handle('projetos')}
          />
        </label>
        <label className="block">
          <span className="text-sm">Previsão Fechamento</span>
          <input
            type="date"
            className="input"
            value={form.previsao_fechamento}
            onChange={handle('previsao_fechamento')}
          />
        </label>
        <label className="block">
          <span className="text-sm">Temperatura</span>
          <select
            className="input"
            value={form.temperatura}
            onChange={handle('temperatura')}
          >
            <option value="">Selecione</option>
            <option value="Fria">Fria</option>
            <option value="Morna">Morna</option>
            <option value="Quente">Quente</option>
          </select>
        </label>
        <label className="inline-flex items-center gap-1">
          <input
            type="checkbox"
            checked={form.tem_especificador}
            onChange={handle('tem_especificador')}
          />
          Possui Especificador
        </label>
        <label className="block">
          <span className="text-sm">Nome do Especificador</span>
          <input
            className="input"
            value={form.especificador_nome}
            onChange={handle('especificador_nome')}
            disabled={!form.tem_especificador}
          />
        </label>
        <label className="block">
          <span className="text-sm">% RT</span>
          <input
            type="number"
            step="0.01"
            className="input"
            value={form.rt_percent}
            onChange={handle('rt_percent')}
          />
        </label>
        <label className="block md:col-span-2">
          <span className="text-sm">Histórico</span>
          <textarea
            className="input"
            rows="4"
            value={form.historico}
            onChange={handle('historico')}
          />
        </label>
      </div>
      <Button type="submit">Salvar</Button>
    </form>
  );
}

export default AtendimentoForm;
