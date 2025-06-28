import React, { useState, useEffect } from 'react';
import { Button } from '../Producao/components/ui/button';
import { useNavigate, useParams } from 'react-router-dom';
import { fetchComAuth } from '../../utils/fetchComAuth';

function CondicaoPagamento() {
  const navigate = useNavigate();
  const { id } = useParams();
  const initialForm = {
    nome: '',
    numero_parcelas: 1,
    juros_parcela: '',
    dias_vencimento: ['0'],
    ativa: true,
  };
  const [form, setForm] = useState(initialForm);

  useEffect(() => {
    if (id) {
      fetchComAuth(`/comercial/condicoes-pagamento/${id}`)
        .then(d => {
          const c = d.condicao;
          if (c) {
            setForm({
              nome: c.nome,
              numero_parcelas: c.numero_parcelas,
              juros_parcela: c.juros_parcela,
              dias_vencimento: c.dias_vencimento ? c.dias_vencimento.split(',') : [],
              ativa: !!c.ativa,
            });
          }
        })
        .catch(() => {});
    }
  }, [id]);

  const handle = campo => e => {
    const value = e.target.type === 'checkbox' ? e.target.checked : e.target.value;
    setForm(prev => ({ ...prev, [campo]: value }));
  };

  const handleDiasChange = (index, value) => {
    setForm(prev => {
      const dias = [...prev.dias_vencimento];
      dias[index] = value;
      return { ...prev, dias_vencimento: dias };
    });
  };

  const adicionarDia = () => {
    setForm(prev => ({ ...prev, dias_vencimento: [...prev.dias_vencimento, ''] }));
  };

  const removerDia = index => {
    setForm(prev => ({
      ...prev,
      dias_vencimento: prev.dias_vencimento.filter((_, i) => i !== index),
    }));
  };

  const salvar = async () => {
    const parcelas = parseInt(form.numero_parcelas, 10);
    const juros = parseFloat(form.juros_parcela);

    const body = {
      nome: form.nome,
      numero_parcelas: Number.isFinite(parcelas) ? parcelas : 1,
      juros_parcela: Number.isFinite(juros) ? juros : 0,
      dias_vencimento: form.dias_vencimento,
      ativa: form.ativa ? 1 : 0,
    };
    const url = id ? `/comercial/condicoes-pagamento/${id}` : '/comercial/condicoes-pagamento';
    const metodo = id ? 'PUT' : 'POST';
    await fetchComAuth(url, { method: metodo, body: JSON.stringify(body) });
  };

  const handleSubmit = async e => {
    e.preventDefault();
    await salvar();
    if (id) {
      navigate('../lista');
    } else {
      setForm(initialForm);
    }
  };

  const cancelar = () => {
    setForm(initialForm);
  };

  const sair = () => {
    navigate('..');
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <label className="block">
          <span className="text-sm">Nome/Descrição</span>
          <input className="input" value={form.nome} onChange={handle('nome')} />
        </label>
        <label className="block">
          <span className="text-sm">Número de Parcelas</span>
          <input
            type="number"
            className="input"
            value={form.numero_parcelas}
            onChange={handle('numero_parcelas')}
          />
        </label>
        <label className="block">
          <span className="text-sm">Juros % por Parcela</span>
          <input
            type="number"
            step="0.01"
            className="input"
            value={form.juros_parcela}
            onChange={handle('juros_parcela')}
          />
        </label>
        <label className="inline-flex items-center gap-1">
          <input type="checkbox" checked={form.ativa} onChange={handle('ativa')} />
          Ativa
        </label>
        <div className="md:col-span-2 space-y-2">
          <span className="text-sm block">Dias de Vencimento</span>
          {form.dias_vencimento.map((dia, idx) => (
            <div key={idx} className="flex items-center gap-2">
              <input
                type="number"
                className="input flex-1"
                value={dia}
                onChange={e => handleDiasChange(idx, e.target.value)}
              />
              <button
                type="button"
                className="text-red-600 hover:underline"
                onClick={() => removerDia(idx)}
              >
                Remover
              </button>
            </div>
          ))}
          <Button type="button" variant="secondary" onClick={adicionarDia}>
            Adicionar Dia
          </Button>
        </div>
      </div>
      <div className="flex gap-2">
        <Button type="submit">Salvar</Button>
        <Button type="button" variant="secondary" onClick={cancelar}>
          Cancelar
        </Button>
        <Button type="button" variant="secondary" onClick={sair}>
          Sair
        </Button>
      </div>
    </form>
  );
}

export default CondicaoPagamento;
