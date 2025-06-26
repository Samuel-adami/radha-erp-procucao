import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

const ListaEmpresas = () => {
  const [empresa, setEmpresa] = useState(null);

  const carregar = () => {
    const obj = JSON.parse(localStorage.getItem('empresa') || 'null');
    setEmpresa(obj);
  };

  useEffect(() => {
    carregar();
  }, []);

  const excluir = () => {
    localStorage.removeItem('empresa');
    carregar();
  };

  return (
    <div className="space-y-2">
      <h3 className="text-lg font-semibold">Empresas Cadastradas</h3>
      <ul className="space-y-1">
        {empresa && (
          <li className="flex justify-between items-center border rounded p-2">
            <span>{empresa.nomeFantasia || empresa.nome_fantasia}</span>
            <div className="space-x-2">
              <Link className="text-blue-600 hover:underline" to="/cadastros">
                Editar
              </Link>
              <button className="text-red-600 hover:underline" onClick={excluir}>Excluir</button>
            </div>
          </li>
        )}
      </ul>
    </div>
  );
};

export default ListaEmpresas;
