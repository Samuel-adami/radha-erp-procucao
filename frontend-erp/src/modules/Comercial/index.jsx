import React from 'react';
import { Routes, Route, Link, Outlet, useResolvedPath, useMatch } from 'react-router-dom';
import { useUsuario } from '../../UserContext';
import Atendimentos from './pages/Atendimentos';
import AtendimentoForm from './pages/AtendimentoForm';

function ComercialLayout() {
  const resolved = useResolvedPath('');
  const matchAtendimentos = useMatch({ path: `${resolved.pathname}`, end: true });
  const usuario = useUsuario();
  const possuiPermissao = p => usuario?.permissoes?.includes(p);

  return (
    <div className="p-4 bg-white rounded shadow-md">
      <h2 className="text-xl font-bold mb-4 text-blue-700">Módulo: Comercial</h2>
      <nav className="flex gap-4 mb-4 border-b pb-2">
        {possuiPermissao('comercial/atendimentos') && (
          <Link
            to="."
            className={`px-3 py-1 rounded ${matchAtendimentos ? 'bg-blue-200 text-blue-800' : 'text-blue-600 hover:bg-blue-100'}`}
          >
            Atendimentos
          </Link>
        )}
      </nav>
      <Outlet />
    </div>
  );
}

function Comercial() {
  return (
    <Routes>
      <Route path="/" element={<ComercialLayout />}>
        <Route index element={<Atendimentos />} />
        <Route path="novo" element={<AtendimentoForm />} />
      </Route>
    </Routes>
  );
}

export default Comercial;
