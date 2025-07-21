import React, { useEffect, useState } from 'react';
import { Button } from '../../Producao/components/ui/button';
import { fetchComAuth } from '../../../utils/fetchComAuth';

function Payables() {
  const [payables, setPayables] = useState([]);
  const [form, setForm] = useState({ description: '', amount: '', due_date: '' });

  const load = async () => {
    const data = await fetchComAuth('/finance/payables/');
    setPayables(data?.payables || []);
  };

  useEffect(() => { load(); }, []);

  const handle = field => e => setForm(prev => ({ ...prev, [field]: e.target.value }));

  const save = async () => {
    const payload = { ...form, amount: parseFloat(form.amount || 0) };
    await fetchComAuth('/finance/payables/', { method: 'POST', body: JSON.stringify(payload) });
    setForm({ description: '', amount: '', due_date: '' });
    load();
  };

  const settle = async id => {
    await fetchComAuth(`/finance/payables/${id}/settle`, { method: 'PUT', body: JSON.stringify({}) });
    load();
  };

  const handleSubmit = e => { e.preventDefault(); save(); };

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">Contas a Pagar</h3>
      <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-3 gap-2 items-end">
        <label className="block">
          <span className="text-sm">Descrição</span>
          <input className="input" value={form.description} onChange={handle('description')} />
        </label>
        <label className="block">
          <span className="text-sm">Valor</span>
          <input className="input" value={form.amount} onChange={handle('amount')} />
        </label>
        <label className="block">
          <span className="text-sm">Vencimento</span>
          <input type="date" className="input" value={form.due_date} onChange={handle('due_date')} />
        </label>
        <Button type="button" onClick={handleSubmit}>Adicionar</Button>
      </form>
      <ul className="space-y-1">
        {payables.map(p => (
          <li key={p.id} className="flex justify-between items-center border rounded p-2">
            <span>{p.description} - R$ {p.amount} - {p.status}</span>
            {p.status === 'ABERTO' && (
              <Button type="button" variant="secondary" onClick={() => settle(p.id)}>Baixar</Button>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default Payables;
