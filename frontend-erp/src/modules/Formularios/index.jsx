import React from 'react';
import { Routes, Route, Outlet } from 'react-router-dom';
import BriefingVendas from './pages/BriefingVendas';

function FormulariosLayout() {
  return (
    <div className="p-4 bg-white rounded shadow-md">
      <h2 className="text-xl font-bold mb-4 text-blue-700">Módulo: Formulários</h2>
      <Outlet />
    </div>
  );
}

function Formularios() {
  return (
    <Routes>
      <Route path="/" element={<FormulariosLayout />}>
        <Route path="briefing-vendas/:atendimentoId/:tarefaId" element={<BriefingVendas />} />
      </Route>
    </Routes>
  );
}

export default Formularios;
