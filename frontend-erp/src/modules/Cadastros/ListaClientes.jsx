import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

const ListaClientes = () => {
  const [clientes, setClientes] = useState([]);

  const carregar = () => {
    const lista = JSON.parse(localStorage.getItem('clientes') || '[]');
    setClientes(lista);
  };

  useEffect(() => {
    carregar();
  }, []);

  const excluir = id => {
    const lista = JSON.parse(localStorage.getItem('clientes') || '[]').filter(c => c.id !== id);
    localStorage.setItem('clientes', JSON.stringify(lista));
    carregar();
  };

  return (
    <div className="space-y-2">
      <h3 className="text-lg font-semibold">Clientes Cadastrados</h3>
      <ul className="space-y-1">
        {clientes.map(c => (
          <li key={c.id} className="flex justify-between items-center border rounded p-2">
            <span>{c.nome}</span>
            <div className="space-x-2">
              <Link
                className="text-blue-600 hover:underline"
                to={`/cadastros/clientes/editar/${c.id}`}
              >
                Editar
              </Link>
              <button className="text-red-600 hover:underline" onClick={() => excluir(c.id)}>Excluir</button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default ListaClientes;
