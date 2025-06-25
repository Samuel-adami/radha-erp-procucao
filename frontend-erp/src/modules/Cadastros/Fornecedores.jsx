import React, { useState } from 'react';
import { Button } from '../Producao/components/ui/button';
import { useNavigate } from 'react-router-dom';

function Fornecedores() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ nome: '', contato: '' });

  const handle = campo => e => {
    setForm(prev => ({ ...prev, [campo]: e.target.value }));
  };

  const salvar = e => {
    e.preventDefault();
    // Placeholder para envio futuro
    alert('Fornecedor salvo (exemplo).');
    setForm({ nome: '', contato: '' });
  };

  return (
    <form onSubmit={salvar} className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <label className="block">
          <span className="text-sm">Nome</span>
          <input className="input" value={form.nome} onChange={handle('nome')} />
        </label>
        <label className="block">
          <span className="text-sm">Contato</span>
          <input className="input" value={form.contato} onChange={handle('contato')} />
        </label>
      </div>
      <div className="flex gap-2">
        <Button type="submit">Salvar</Button>
        <Button type="button" variant="secondary" onClick={() => navigate('lista')}>Listar Fornecedores</Button>
      </div>
    </form>
  );
}

export default Fornecedores;
