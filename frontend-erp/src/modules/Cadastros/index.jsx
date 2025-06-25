import React from 'react';
import { Routes, Route, Link, Outlet, useResolvedPath, useMatch } from 'react-router-dom';
import DadosEmpresa from './DadosEmpresa';
import './Cadastros.css';

function CadastrosLayout() {
  const resolved = useResolvedPath('');
  const matchDados = useMatch({ path: `${resolved.pathname}`, end: true });
  return (
    <div className="p-4 bg-white rounded shadow-md">
      <h2 className="text-xl font-bold mb-4 text-blue-700">Módulo: Cadastros</h2>
      <nav className="flex gap-4 mb-4 border-b pb-2">
        <Link
          to="." // raiz do módulo
          className={`px-3 py-1 rounded ${matchDados ? 'bg-blue-200 text-blue-800' : 'text-blue-600 hover:bg-blue-100'}`}
        >
          Dados da Empresa
        </Link>
      </nav>
      <Outlet />
    </div>
  );
}

function Cadastros() {
  return (
    <Routes>
      <Route path="/" element={<CadastrosLayout />}>
        <Route index element={<DadosEmpresa />} />
      </Route>
    </Routes>
  );
}

export default Cadastros;
