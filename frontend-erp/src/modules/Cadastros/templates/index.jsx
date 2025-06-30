import React from 'react';
import { Routes, Route, Link, Outlet } from 'react-router-dom';
import ListaTemplates from './ListaTemplates';
import TemplateForm from './TemplateForm';

const tipos = [
  { id: 'orcamento', nome: 'Orçamento' },
  { id: 'pedido', nome: 'Pedido' },
  { id: 'contrato', nome: 'Contrato' },
  { id: 'romaneio', nome: 'Romaneio de Entrega' },
  { id: 'memorial', nome: 'Memorial Descritivo' },
  { id: 'negociacao', nome: 'Negociação' },
];

function TemplatesMenu() {
  return (
    <div className="space-y-2">
      <h3 className="text-lg font-semibold">Tipos de Template</h3>
      <ul className="space-y-1">
        {tipos.map(t => (
          <li key={t.id}>
            <Link className="text-blue-600 hover:underline" to={t.id}>{t.nome}</Link>
          </li>
        ))}
      </ul>
    </div>
  );
}

function TemplatesLayout() {
  return (
    <div className="space-y-4">
      <Outlet />
    </div>
  );
}

function Templates() {
  return (
    <Routes>
      <Route path="/" element={<TemplatesLayout />}>
        <Route index element={<TemplatesMenu />} />
        <Route path=":tipo" element={<ListaTemplates />} />
        <Route path=":tipo/novo" element={<TemplateForm />} />
        <Route path=":tipo/editar/:id" element={<TemplateForm />} />
      </Route>
    </Routes>
  );
}

export default Templates;
