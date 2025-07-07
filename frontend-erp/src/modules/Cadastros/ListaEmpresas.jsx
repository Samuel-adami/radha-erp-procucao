import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { fetchComAuth } from '../../utils/fetchComAuth';

const ListaEmpresas = () => {
  const [empresa, setEmpresa] = useState(null);

  const carregar = async () => {
    try {
      const data = await fetchComAuth('/empresa');
      setEmpresa(data?.empresas ? data.empresas[0] : null);
    } catch (err) {
      console.error('Erro ao carregar empresa', err);
    }
  };

  useEffect(() => {
    carregar();
  }, []);

  const excluir = async () => {
    if (!empresa) return;
    try {
      await fetchComAuth(`/empresa/${empresa.id}`, { method: 'DELETE' });
      setEmpresa(null);
    } catch (err) {
      console.error('Erro ao excluir empresa', err);
    }
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
