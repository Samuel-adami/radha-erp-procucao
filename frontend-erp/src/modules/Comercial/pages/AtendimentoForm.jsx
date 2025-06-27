import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchComAuth } from '../../../utils/fetchComAuth';

function AtendimentoForm() {
  const [cliente, setCliente] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await fetchComAuth('/comercial/atendimentos', {
        method: 'POST',
        body: JSON.stringify({ cliente }),
      });
      navigate('..');
    } catch (err) {
      console.error('Erro ao criar atendimento', err);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block mb-1">Cliente</label>
        <input
          type="text"
          value={cliente}
          onChange={(e) => setCliente(e.target.value)}
          className="border p-1 rounded w-full"
        />
      </div>
      <button type="submit" className="bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-700">
        Salvar
      </button>
    </form>
  );
}

export default AtendimentoForm;
