import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Button } from '../../Producao/components/ui/button';
import { fetchComAuth } from '../../../utils/fetchComAuth';

function Atendimentos() {
  const [atendimentos, setAtendimentos] = useState([]);

  const carregar = async () => {
    try {
      const dados = await fetchComAuth('/comercial/atendimentos');
      setAtendimentos(dados.atendimentos);
    } catch (err) {
      console.error('Erro ao carregar atendimentos', err);
    }
  };

  useEffect(() => {
    carregar();
  }, []);

  const remover = async (id) => {
    if (!window.confirm('Excluir atendimento?')) return;
    await fetchComAuth(`/comercial/atendimentos/${id}`, { method: 'DELETE' });
    carregar();
  };

  return (
    <div>
      <div className="flex justify-end mb-4">
        <Link to="novo" className="bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-700">
          Novo Atendimento
        </Link>
      </div>
      <ul className="space-y-2">
        {atendimentos.map((at) => (
          <li
            key={at.id}
            className="p-2 border rounded bg-gray-50 flex justify-between items-center"
          >
            <Link to={String(at.id)} className="hover:underline flex-1">
              <span className="font-medium">{at.codigo}</span> - {at.cliente}
            </Link>
            <Button size="sm" variant="destructive" onClick={() => remover(at.id)}>
              Excluir
            </Button>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default Atendimentos;
