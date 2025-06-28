import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { fetchComAuth } from '../../utils/fetchComAuth';

const ListaCondicoesPagamento = () => {
  const [condicoes, setCondicoes] = useState([]);

  const carregar = async () => {
    try {
      const dados = await fetchComAuth('/comercial/condicoes-pagamento');
      setCondicoes(dados.condicoes);
    } catch (err) {
      console.error('Erro ao carregar condições', err);
    }
  };

  useEffect(() => {
    carregar();
  }, []);

  const excluir = async id => {
    if (!window.confirm('Excluir esta condição?')) return;
    await fetchComAuth(`/comercial/condicoes-pagamento/${id}`, { method: 'DELETE' });
    carregar();
  };

  return (
    <div className="space-y-2">
      <h3 className="text-lg font-semibold">Condições de Pagamento</h3>
      <ul className="space-y-1">
        {condicoes.map(c => (
          <li key={c.id} className="flex justify-between items-center border rounded p-2">
            <span>{c.nome}</span>
            <div className="space-x-2">
              <Link className="text-blue-600 hover:underline" to={`/cadastros/condicoes-pagamento/editar/${c.id}`}>Editar</Link>
              <button className="text-red-600 hover:underline" onClick={() => excluir(c.id)}>Excluir</button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default ListaCondicoesPagamento;
