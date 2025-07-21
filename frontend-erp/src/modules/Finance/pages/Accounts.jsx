import React, { useEffect, useState } from 'react';
import { Button } from '../../Producao/components/ui/button';
import { fetchComAuth } from '../../../utils/fetchComAuth';

function Accounts() {
  const [accounts, setAccounts] = useState([]);
  const [banks, setBanks] = useState([]);
  const [form, setForm] = useState({ agency: '', account_number: '', initial_balance: '', bank_id: '' });
  const [editingId, setEditingId] = useState(null);

  const load = async () => {
    const acc = await fetchComAuth('/finance/accounts/');
    const bks = await fetchComAuth('/finance/banks/');
    setAccounts(acc?.accounts || []);
    setBanks(bks?.banks || []);
  };

  useEffect(() => { load(); }, []);

  const handle = field => e => setForm(prev => ({ ...prev, [field]: e.target.value }));

  const save = async () => {
    const payload = { ...form, initial_balance: parseFloat(form.initial_balance || 0) };
    if (editingId) {
      await fetchComAuth(`/finance/accounts/${editingId}`, { method: 'PUT', body: JSON.stringify(payload) });
    } else {
      await fetchComAuth('/finance/accounts/', { method: 'POST', body: JSON.stringify(payload) });
    }
    setForm({ agency: '', account_number: '', initial_balance: '', bank_id: '' });
    setEditingId(null);
    load();
  };

  const edit = acc => {
    setForm({ agency: acc.agency, account_number: acc.account_number, initial_balance: acc.initial_balance, bank_id: acc.bank_id });
    setEditingId(acc.id);
  };

  const handleSubmit = e => { e.preventDefault(); save(); };

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">Contas Bancárias</h3>
      <form onSubmit={handleSubmit} className="grid grid-cols-2 md:grid-cols-4 gap-2 items-end">
        <label className="block">
          <span className="text-sm">Agência</span>
          <input className="input" value={form.agency} onChange={handle('agency')} />
        </label>
        <label className="block">
          <span className="text-sm">Conta</span>
          <input className="input" value={form.account_number} onChange={handle('account_number')} />
        </label>
        <label className="block">
          <span className="text-sm">Saldo Inicial</span>
          <input className="input" value={form.initial_balance} onChange={handle('initial_balance')} />
        </label>
        <label className="block">
          <span className="text-sm">Banco</span>
          <select className="input" value={form.bank_id} onChange={handle('bank_id')}>
            <option value="">Selecione</option>
            {banks.map(b => (<option key={b.id} value={b.id}>{b.name}</option>))}
          </select>
        </label>
        <Button type="button" onClick={handleSubmit}>{editingId ? 'Atualizar' : 'Adicionar'}</Button>
      </form>
      <ul className="space-y-1">
        {accounts.map(a => (
          <li key={a.id} className="flex justify-between items-center border rounded p-2">
            <span>{a.agency}-{a.account_number} / {banks.find(b => b.id === a.bank_id)?.name}</span>
            <Button type="button" variant="secondary" onClick={() => edit(a)}>Editar</Button>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default Accounts;
