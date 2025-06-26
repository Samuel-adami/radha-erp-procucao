import React, { useState, useEffect } from 'react';
import { Button } from '../Producao/components/ui/button';
import { useNavigate, useParams } from 'react-router-dom';

function Fornecedores() {
  const navigate = useNavigate();
  const { id } = useParams();
  const initialForm = { nome: '', contato: '' };
  const [form, setForm] = useState(initialForm);

  useEffect(() => {
    if (id) {
      const lista = JSON.parse(localStorage.getItem('fornecedores') || '[]');
      const existente = lista.find(f => String(f.id) === String(id));
      if (existente) setForm(existente);
    }
  }, [id]);

  const handle = campo => e => {
    setForm(prev => ({ ...prev, [campo]: e.target.value }));
  };

  const salvar = e => {
    e.preventDefault();
    const lista = JSON.parse(localStorage.getItem('fornecedores') || '[]');
    if (id) {
      const idx = lista.findIndex(f => String(f.id) === String(id));
      if (idx >= 0) lista[idx] = { ...form, id };
    } else {
      const novo = { ...form, id: Date.now() };
      lista.push(novo);
    }
    localStorage.setItem('fornecedores', JSON.stringify(lista));
    alert('Fornecedor salvo');
    if (!id) setForm(initialForm);
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
