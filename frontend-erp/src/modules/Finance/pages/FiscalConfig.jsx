import React, { useEffect, useState } from 'react';
import { Button } from '../../Producao/components/ui/button';
import { fetchComAuth } from '../../../utils/fetchComAuth';

function FiscalConfig() {
  const [configs, setConfigs] = useState([]);
  const [form, setForm] = useState({ cfop: '', cst: '', ncm: '', default_tax_rate: '' });
  const [editingId, setEditingId] = useState(null);

  const load = async () => {
    const data = await fetchComAuth('/finance/fiscal-config/');
    setConfigs(data?.configs || []);
  };

  useEffect(() => { load(); }, []);

  const handle = field => e => setForm(prev => ({ ...prev, [field]: e.target.value }));

  const save = async () => {
    const payload = { ...form, default_tax_rate: parseFloat(form.default_tax_rate || 0) };
    if (editingId) {
      await fetchComAuth(`/finance/fiscal-config/${editingId}`, { method: 'PUT', body: JSON.stringify(payload) });
    } else {
      await fetchComAuth('/finance/fiscal-config/', { method: 'POST', body: JSON.stringify(payload) });
    }
    setForm({ cfop: '', cst: '', ncm: '', default_tax_rate: '' });
    setEditingId(null);
    load();
  };

  const edit = cfg => {
    setForm({ cfop: cfg.cfop, cst: cfg.cst, ncm: cfg.ncm, default_tax_rate: cfg.default_tax_rate });
    setEditingId(cfg.id);
  };

  const handleSubmit = e => { e.preventDefault(); save(); };

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">Configurações Fiscais</h3>
      <form onSubmit={handleSubmit} className="grid grid-cols-2 md:grid-cols-5 gap-2 items-end">
        <label className="block">
          <span className="text-sm">CFOP</span>
          <input className="input" value={form.cfop} onChange={handle('cfop')} />
        </label>
        <label className="block">
          <span className="text-sm">CST</span>
          <input className="input" value={form.cst} onChange={handle('cst')} />
        </label>
        <label className="block">
          <span className="text-sm">NCM</span>
          <input className="input" value={form.ncm} onChange={handle('ncm')} />
        </label>
        <label className="block">
          <span className="text-sm">Taxa</span>
          <input className="input" value={form.default_tax_rate} onChange={handle('default_tax_rate')} />
        </label>
        <Button type="button" onClick={handleSubmit}>{editingId ? 'Atualizar' : 'Adicionar'}</Button>
      </form>
      <ul className="space-y-1">
        {configs.map(c => (
          <li key={c.id} className="flex justify-between items-center border rounded p-2">
            <span>{c.cfop} - {c.cst} - {c.ncm} - {c.default_tax_rate}%</span>
            <Button type="button" variant="secondary" onClick={() => edit(c)}>Editar</Button>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default FiscalConfig;
