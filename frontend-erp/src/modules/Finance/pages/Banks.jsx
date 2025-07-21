import React, { useEffect, useState } from 'react';
import { Button } from '../../Producao/components/ui/button';
import { fetchComAuth } from '../../../utils/fetchComAuth';

function Banks() {
  const [banks, setBanks] = useState([]);
  const [form, setForm] = useState({ code: '', name: '' });
  const [editingId, setEditingId] = useState(null);

  const load = async () => {
    const data = await fetchComAuth('/finance/banks/');
    setBanks(data?.banks || []);
  };

  useEffect(() => {
    load();
  }, []);

  const handle = field => e => setForm(prev => ({ ...prev, [field]: e.target.value }));

  const save = async () => {
    const payload = { ...form };
    if (editingId) {
      await fetchComAuth(`/finance/banks/${editingId}`, { method: 'PUT', body: JSON.stringify(payload) });
    } else {
      await fetchComAuth('/finance/banks/', { method: 'POST', body: JSON.stringify(payload) });
    }
    setForm({ code: '', name: '' });
    setEditingId(null);
    load();
  };

  const edit = bank => {
    setForm({ code: bank.code, name: bank.name });
    setEditingId(bank.id);
  };

  const handleSubmit = e => {
    e.preventDefault();
    save();
  };

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">Bancos</h3>
      <form onSubmit={handleSubmit} className="flex gap-2 items-end">
        <label className="block">
          <span className="text-sm">Código</span>
          <input className="input" value={form.code} onChange={handle('code')} />
        </label>
        <label className="block">
          <span className="text-sm">Nome</span>
          <input className="input" value={form.name} onChange={handle('name')} />
        </label>
        <Button type="button" onClick={handleSubmit}>{editingId ? 'Atualizar' : 'Adicionar'}</Button>
      </form>
      <ul className="space-y-1">
        {banks.map(b => (
          <li key={b.id} className="flex justify-between items-center border rounded p-2">
            <span>{b.code} - {b.name}</span>
            <Button type="button" variant="secondary" onClick={() => edit(b)}>Editar</Button>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default Banks;
