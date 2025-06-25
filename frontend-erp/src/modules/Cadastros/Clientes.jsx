import React, { useState } from 'react';
import { Button } from '../Producao/components/ui/button';
import { useNavigate } from 'react-router-dom';

function Clientes() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ nome: '', documento: '' });

  const handle = campo => e => {
    setForm(prev => ({ ...prev, [campo]: e.target.value }));
  };

  const salvar = e => {
    e.preventDefault();
    // Placeholder: enviar dados para API quando disponível
    alert('Cliente salvo (exemplo).');
    setForm({ nome: '', documento: '' });
  };

  return (
    <form onSubmit={salvar} className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <label className="block">
          <span className="text-sm">Nome</span>
          <input className="input" value={form.nome} onChange={handle('nome')} />
        </label>
        <label className="block">
          <span className="text-sm">Documento</span>
          <input className="input" value={form.documento} onChange={handle('documento')} />
        </label>
      </div>
      <div className="flex gap-2">
        <Button type="submit">Salvar</Button>
        <Button type="button" variant="secondary" onClick={() => navigate('lista')}>Listar Clientes</Button>
      </div>
    </form>
  );
}

export default Clientes;
