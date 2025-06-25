import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { fetchComAuth } from '../../utils/fetchComAuth';

const ListaEmpresas = () => {
  const [empresas, setEmpresas] = useState([]);

  const carregar = async () => {
    const dados = await fetchComAuth('/empresa');
    if (dados && Array.isArray(dados.empresas)) setEmpresas(dados.empresas);
  };

  useEffect(() => {
    carregar();
  }, []);

  return (
    <div className="space-y-2">
      <h3 className="text-lg font-semibold">Empresas Cadastradas</h3>
      <ul className="space-y-1">
        {empresas.map(e => (
          <li key={e.id} className="flex justify-between items-center border rounded p-2">
            <span>{e.codigo} - {e.nome_fantasia}</span>
            <Link className="text-blue-600 hover:underline" to={`../editar/${e.id}`}>Editar</Link>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default ListaEmpresas;
