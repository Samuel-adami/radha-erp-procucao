import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../../Producao/components/ui/button';
import { fetchComAuth } from '../../../utils/fetchComAuth';

const PROJETOS = [
  'Cozinha',
  'Banheiro',
  'Lavabo',
  'B. Social',
  'B. Suíte',
  'Lavanderia',
  'D. Casal',
  'Suíte',
  'Closet',
  'Home Office',
  'A. Gourmet',
  'D. Solteiro',
  'D. Hóspedes',
  'D. Infantil',
  'D. Bebê',
  'Ambiente Comercial',
];

function AtendimentoForm() {
  const [form, setForm] = useState({
    cliente: '',
    codigo: '',
    projetos: [],
    previsao_fechamento: '',
    temperatura: '',
    tem_especificador: false,
    especificador_nome: '',
    rt_percent: '',
    historico: '',
  });
  const [sugestoesClientes, setSugestoesClientes] = useState([]);
  const [clienteInfo, setClienteInfo] = useState(null);
  const [sequencial, setSequencial] = useState(1);
  const navigate = useNavigate();

  useEffect(() => {
    const seq = parseInt(localStorage.getItem('atendimentoCodigoSeq') || '1', 10);
    setSequencial(seq);
  }, []);

  useEffect(() => {
    if (clienteInfo) {
      const codigo = `AT-${clienteInfo.codigo}-${String(sequencial).padStart(4, '0')}`;
      setForm(prev => ({ ...prev, codigo }));
    }
  }, [clienteInfo, sequencial]);

  const handle = campo => e => {
    let value = e.target.value;
    if (campo === 'tem_especificador') {
      value = value === 'Sim';
    }
    setForm(prev => ({ ...prev, [campo]: value }));
  };

  const handleProjetosChange = e => {
    const selected = Array.from(e.target.selectedOptions).map(o => o.value);
    setForm(prev => ({ ...prev, projetos: selected }));
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
          projetos: form.projetos.join(','),
          tem_especificador: form.tem_especificador ? 1 : 0,
        }),
      });
      localStorage.setItem('atendimentoCodigoSeq', String(sequencial + 1));
      setSequencial(s => s + 1);
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
          <div>CPF/CNPJ: {clienteInfo.documento}</div>
          <div>Tel: {clienteInfo.telefone1}</div>
          <div>Email: {clienteInfo.email}</div>
          <div>
            {clienteInfo.endereco} {clienteInfo.numero} - {clienteInfo.bairro}
          </div>
          <div>
            {clienteInfo.cidade}/{clienteInfo.estado}
          </div>
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
          <span className="text-sm">Projetos do Atendimento</span>
          <select
            multiple
            className="input h-32"
            value={form.projetos}
            onChange={handleProjetosChange}
          >
            {PROJETOS.map(p => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
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
            <option>Gelado</option>
            <option>Frio</option>
            <option>Morno</option>
            <option>Quente</option>
          </select>
        </label>
        <label className="block">
          <span className="text-sm">Tem Especificador?</span>
          <select
            className="input"
            value={form.tem_especificador ? 'Sim' : 'Não'}
            onChange={handle('tem_especificador')}
          >
            <option>Não</option>
            <option>Sim</option>
          </select>
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
            disabled={!form.tem_especificador}
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
