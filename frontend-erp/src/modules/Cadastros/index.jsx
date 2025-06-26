import React from 'react';
import { Routes, Route, Link, Outlet, useResolvedPath, useMatch } from 'react-router-dom';
import DadosEmpresa from './DadosEmpresa';
import ListaEmpresas from './ListaEmpresas';
import Clientes from './Clientes';
import ListaClientes from './ListaClientes';
import Fornecedores from './Fornecedores';
import ListaFornecedores from './ListaFornecedores';
import Usuarios from './Usuarios';
import ListaUsuarios from './ListaUsuarios';
import './Cadastros.css';

function CadastrosLayout() {
  const resolved = useResolvedPath('');
  const matchDados = useMatch({ path: `${resolved.pathname}`, end: true });
  const matchClientes = useMatch(`${resolved.pathname}/clientes`);
  const matchFornecedores = useMatch(`${resolved.pathname}/fornecedores`);
  const matchUsuarios = useMatch(`${resolved.pathname}/usuarios`);
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
        <Link
          to="clientes"
          className={`px-3 py-1 rounded ${matchClientes ? 'bg-blue-200 text-blue-800' : 'text-blue-600 hover:bg-blue-100'}`}
        >
          Clientes
        </Link>
        <Link
          to="fornecedores"
          className={`px-3 py-1 rounded ${matchFornecedores ? 'bg-blue-200 text-blue-800' : 'text-blue-600 hover:bg-blue-100'}`}
        >
          Fornecedores
        </Link>
        <Link
          to="usuarios"
          className={`px-3 py-1 rounded ${matchUsuarios ? 'bg-blue-200 text-blue-800' : 'text-blue-600 hover:bg-blue-100'}`}
        >
          Usuários
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
        <Route path="lista" element={<ListaEmpresas />} />
        <Route path="editar/:id" element={<DadosEmpresa />} />
        <Route path="clientes" element={<Clientes />} />
        <Route path="clientes/lista" element={<ListaClientes />} />
        <Route path="clientes/editar/:id" element={<Clientes />} />
        <Route path="fornecedores" element={<Fornecedores />} />
        <Route path="fornecedores/lista" element={<ListaFornecedores />} />
        <Route path="fornecedores/editar/:id" element={<Fornecedores />} />
        <Route path="usuarios" element={<Usuarios />} />
        <Route path="usuarios/lista" element={<ListaUsuarios />} />
      </Route>
    </Routes>
  );
}

export default Cadastros;
