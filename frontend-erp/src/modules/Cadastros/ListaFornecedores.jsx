import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { fetchComAuth } from '../../utils/fetchComAuth';

const ListaFornecedores = () => {
  const [fornecedores, setFornecedores] = useState([]);

  const carregar = async () => {
    try {
      const data = await fetchComAuth('/fornecedores');
      setFornecedores(data?.fornecedores || []);
    } catch (err) {
      console.error('Erro ao carregar fornecedores', err);
    }
  };

  useEffect(() => {
    carregar();
  }, []);

  const excluir = async id => {
    try {
      await fetchComAuth(`/fornecedores/${id}`, { method: 'DELETE' });
      carregar();
    } catch (err) {
      console.error('Erro ao excluir', err);
    }
  };

  return (
    <div className="space-y-2">
      <h3 className="text-lg font-semibold">Fornecedores Cadastrados</h3>
      <ul className="space-y-1">
        {fornecedores.map(f => (
          <li key={f.id} className="flex justify-between items-center border rounded p-2">
            <span>{f.nome}</span>
            <div className="space-x-2">
              <Link
                className="text-blue-600 hover:underline"
                to={`/cadastros/fornecedores/editar/${f.id}`}
              >
                Editar
              </Link>
              <button className="text-red-600 hover:underline" onClick={() => excluir(f.id)}>Excluir</button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default ListaFornecedores;
