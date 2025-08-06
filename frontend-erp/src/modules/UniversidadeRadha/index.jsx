// radha-erp/frontend-erp/src/modules/UniversidadeRadha/index.jsx
import React from 'react';
import { Routes, Route, Outlet } from 'react-router-dom';

// Layout simples para o módulo Universidade Radha
function UniversidadeRadhaLayout() {
  return (
    <div className="p-4 bg-white rounded shadow-md">
      <h2 className="text-xl font-bold mb-4 text-blue-700">
        Módulo: Universidade Radha
      </h2>
      <Outlet />
    </div>
  );
}

function UniversidadeRadhaHome() {
  return <div>Bem-vindo à Universidade Radha!</div>;
}

// Componente principal do módulo
function UniversidadeRadha() {
  return (
    <Routes>
      <Route path="/" element={<UniversidadeRadhaLayout />}>
        <Route index element={<UniversidadeRadhaHome />} />
      </Route>
    </Routes>
  );
}

export default UniversidadeRadha;

