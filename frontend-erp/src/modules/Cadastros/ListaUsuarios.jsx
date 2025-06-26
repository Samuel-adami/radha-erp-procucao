import React, { useEffect, useState } from 'react';
import { fetchComAuth } from '../../utils/fetchComAuth';

const ListaUsuarios = () => {
  const [usuarios, setUsuarios] = useState([]);
  const carregar = async () => {
    const dados = await fetchComAuth('/usuarios');
    if (dados && Array.isArray(dados.usuarios)) setUsuarios(dados.usuarios);
  };
  useEffect(() => { carregar(); }, []);

  return (
    <div className="space-y-2">
      <h3 className="text-lg font-semibold">Usuários</h3>
      <ul className="space-y-1">
        {usuarios.map(u => (
          <li key={u.id} className="border rounded p-2 flex justify-between">
            <span>{u.username} - {u.cargo}</span>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default ListaUsuarios;
