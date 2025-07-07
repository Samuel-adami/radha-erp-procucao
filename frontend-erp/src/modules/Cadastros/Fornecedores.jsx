import React, { useState, useEffect } from 'react';
import { Button } from '../Producao/components/ui/button';
import { useNavigate, useParams } from 'react-router-dom';
import { fetchComAuth } from '../../utils/fetchComAuth';

function Fornecedores() {
  const navigate = useNavigate();
  const { id } = useParams();
  const initialForm = { nome: '', contato: '' };
  const [form, setForm] = useState(initialForm);
  const [dirty, setDirty] = useState(false);

  useEffect(() => {
    if (id) {
      fetchComAuth(`/fornecedores/${id}`)
        .then(data => {
          if (data && data.fornecedor) setForm({ ...initialForm, ...data.fornecedor });
        })
        .catch(err => console.error('Erro ao carregar fornecedor', err));
    }
  }, [id]);

  const handle = campo => e => {
    setForm(prev => ({ ...prev, [campo]: e.target.value }));
    setDirty(true);
  };

  const salvar = async () => {
    const payload = { ...form };
    try {
      if (id) {
        await fetchComAuth(`/fornecedores/${id}`, {
          method: 'PUT',
          body: JSON.stringify(payload),
        });
      } else {
        await fetchComAuth('/fornecedores', {
          method: 'POST',
          body: JSON.stringify(payload),
        });
        setForm(initialForm);
      }
      alert('Fornecedor salvo');
      setDirty(false);
    } catch (err) {
      console.error('Erro ao salvar fornecedor', err);
      alert('Falha ao salvar');
    }
  };

  const handleSubmit = async e => {
    e.preventDefault();
    await salvar();
  };

  const cancelar = () => {
    setForm(initialForm);
    setDirty(false);
  };

  const sair = async () => {
    if (dirty) {
      if (window.confirm('Deseja salvar as informações adicionadas?')) {
        await salvar();
      }
    }
    navigate('..');
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
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
        <Button type="button" onClick={handleSubmit}>Salvar</Button>
        <Button type="button" variant="secondary" onClick={cancelar}>
          Cancelar
        </Button>
        <Button type="button" variant="secondary" onClick={sair}>Sair</Button>
      </div>
    </form>
  );
}

export default Fornecedores;
