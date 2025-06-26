import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { fetchComAuth } from '../../utils/fetchComAuth';

const ListaUsuarios = () => {
  const [usuarios, setUsuarios] = useState([]);
  const carregar = async () => {
    const dados = await fetchComAuth('/usuarios');
    if (dados && Array.isArray(dados.usuarios)) setUsuarios(dados.usuarios);
  };
  useEffect(() => { carregar(); }, []);

  const excluir = async id => {
    await fetchComAuth(`/usuarios/${id}`, { method: 'DELETE' }).catch(() => {});
    carregar();
  };

  return (
    <div className="space-y-2">
      <h3 className="text-lg font-semibold">Usuários</h3>
      <ul className="space-y-1">
        {usuarios.map(u => (
          <li key={u.id} className="border rounded p-2 flex justify-between items-center">
            <span>{u.username} - {u.cargo}</span>
            <div className="space-x-2">
              <Link className="text-blue-600 hover:underline" to={`../editar/${u.id}`}>Editar</Link>
              <button className="text-red-600 hover:underline" onClick={() => excluir(u.id)}>Excluir</button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default ListaUsuarios;
