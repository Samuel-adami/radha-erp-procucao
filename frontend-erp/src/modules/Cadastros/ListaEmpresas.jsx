import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

const ListaEmpresas = () => {
  const [empresas, setEmpresas] = useState([]);

  const carregar = () => {
    const lista = JSON.parse(localStorage.getItem('empresas') || '[]');
    setEmpresas(lista);
  };

  useEffect(() => {
    carregar();
  }, []);

  const excluir = id => {
    const lista = JSON.parse(localStorage.getItem('empresas') || '[]').filter(e => e.id !== id);
    localStorage.setItem('empresas', JSON.stringify(lista));
    carregar();
  };

  return (
    <div className="space-y-2">
      <h3 className="text-lg font-semibold">Empresas Cadastradas</h3>
      <ul className="space-y-1">
        {empresas.map(e => (
          <li key={e.id} className="flex justify-between items-center border rounded p-2">
            <span>{e.codigo} - {e.nomeFantasia || e.nome_fantasia}</span>
            <div className="space-x-2">
              <Link className="text-blue-600 hover:underline" to={`../editar/${e.id}`}>Editar</Link>
              <button className="text-red-600 hover:underline" onClick={() => excluir(e.id)}>Excluir</button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default ListaEmpresas;
