import React from 'react';
import { Routes, Route, Link, Outlet, useResolvedPath, useMatch } from 'react-router-dom';
import { useUsuario } from '../../UserContext';
import { Nesting, VisualizacaoNesting, ConfigMaquina } from '../Producao/AppProducao';
import Seccionadora from './components/Seccionadora';

function PlanosProducaoLayout() {
  const resolved = useResolvedPath('');
  const matchNesting = useMatch({ path: `${resolved.pathname}/nesting`, end: true });
  const matchSeccionadora = useMatch({ path: `${resolved.pathname}/seccionadora`, end: true });
  const usuario = useUsuario();
  const possuiPermissao = (p) => usuario?.permissoes?.includes(p);

  return (
    <div className="p-4 bg-white rounded shadow-md">
      <h2 className="text-xl font-bold mb-4 text-green-700">Módulo: Planos de Produção</h2>
      <nav className="flex gap-4 mb-4 border-b pb-2">
        {possuiPermissao('planos-producao/nesting') && (
          <Link
            to="nesting"
            className={`px-3 py-1 rounded ${matchNesting ? 'bg-green-200 text-green-800' : 'text-green-600 hover:bg-green-100'}`}
          >
            Nesting
          </Link>
        )}
        {possuiPermissao('planos-producao/seccionadora') && (
          <Link
            to="seccionadora"
            className={`px-3 py-1 rounded ${matchSeccionadora ? 'bg-green-200 text-green-800' : 'text-green-600 hover:bg-green-100'}`}
          >
            Seccionadora
          </Link>
        )}
      </nav>
      <Outlet />
    </div>
  );
}

function PlanosProducao() {
  return (
    <Routes>
      <Route path="/" element={<PlanosProducaoLayout />}>
        <Route path="nesting" element={<Nesting />} />
        <Route path="nesting/visualizacao" element={<VisualizacaoNesting />} />
        <Route path="nesting/config-maquina" element={<ConfigMaquina />} />
        <Route path="seccionadora" element={<Seccionadora />} />
      </Route>
    </Routes>
  );
}

export default PlanosProducao;
