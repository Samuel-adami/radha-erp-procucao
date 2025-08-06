// radha-erp/frontend-erp/src/modules/UniversidadeRadha/index.jsx
import React from 'react';
import { Routes, Route, Outlet, Link } from 'react-router-dom';

import Treinamentos from './Treinamentos';

import GerenciarConteudos from './GerenciarConteudos';


// Layout simples para o módulo de Treinamentos
function UniversidadeRadhaLayout() {
  return (
    <div className="p-4 bg-white rounded shadow-md">
      <h2 className="text-xl font-bold mb-4 text-blue-700">
        Módulo: Treinamentos
      </h2>
      <nav className="mb-4 space-x-4">
        <Link to="" className="text-blue-600 hover:underline">
          Início
        </Link>

        <Link to="treinamentos" className="text-blue-600 hover:underline">
          Treinamentos
        </Link>

        <Link
          to="gerenciar-conteudos"
          className="text-blue-600 hover:underline"
        >
          Gerenciar Conteúdos
        </Link>
      </nav>
      <Outlet />
    </div>
  );
}

function UniversidadeRadhaHome() {
  return <div>Bem-vindo aos Treinamentos!</div>;
}

// Componente principal do módulo
function UniversidadeRadha() {
  return (
    <Routes>
      <Route path="/" element={<UniversidadeRadhaLayout />}>
        <Route index element={<UniversidadeRadhaHome />} />

        <Route path="treinamentos" element={<Treinamentos />} />

        <Route
          path="gerenciar-conteudos"
          element={<GerenciarConteudos />}
        />

      </Route>
    </Routes>
  );
}

export default UniversidadeRadha;

