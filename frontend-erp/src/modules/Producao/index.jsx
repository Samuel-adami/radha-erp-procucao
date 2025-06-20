// radha-erp/frontend-erp/src/modules/Producao/index.jsx
import React from 'react';
import { Routes, Route, Link, Outlet, useResolvedPath, useMatch } from 'react-router-dom';
// Importa os componentes renomeados do AppProducao.jsx
import { HomeProducao, LoteProducao, EditarPecaProducao, Pacote, Apontamento, ApontamentoVolume, EditarFerragem } from './AppProducao';

function ProducaoLayout() {
  const resolved = useResolvedPath(''); // O caminho base para este módulo
  const matchHome = useMatch({ path: `${resolved.pathname}`, end: true });
  // Para o link "Início Produção" ser ativo quando estiver na raiz do módulo
  const matchLote = useMatch(`${resolved.pathname}/lote/*`); // Matches /producao/lote/qualquer_nome
  const matchApontamento = useMatch({ path: `${resolved.pathname}/apontamento`, end: true });
  const matchVolume = useMatch({ path: `${resolved.pathname}/apontamento-volume`, end: true });

  return (
    <div className="p-4 bg-white rounded shadow-md">
      <h2 className="text-xl font-bold mb-4 text-blue-700">Módulo: Produção</h2>
      <nav className="flex gap-4 mb-4 border-b pb-2">
        <Link
          to="." // Relativo ao path do módulo (Producao)
          className={`px-3 py-1 rounded ${matchHome ? 'bg-blue-200 text-blue-800' : 'text-blue-600 hover:bg-blue-100'}`}
        >
          Início Produção
        </Link>
        <Link
          to="apontamento"
          className={`px-3 py-1 rounded ${matchApontamento ? 'bg-blue-200 text-blue-800' : 'text-blue-600 hover:bg-blue-100'}`}
        >
          Apontamento
        </Link>
        <Link
          to="apontamento-volume"
          className={`px-3 py-1 rounded ${matchVolume ? 'bg-blue-200 text-blue-800' : 'text-blue-600 hover:bg-blue-100'}`}
        >
          Apontamento Volume
        </Link>
        {/* Adicionar mais links de navegação interna do módulo, se necessário */}
      </nav>
      <Outlet /> {/* Renderiza as rotas aninhadas aqui */}
    </div>
  );
}

function Producao() {
  return (
    <Routes>
      <Route path="/" element={<ProducaoLayout />}>
        <Route index element={<HomeProducao />} /> {/* Rota padrão do módulo */}
        <Route path="lote/:nome" element={<LoteProducao />} />
        <Route path="lote/:nome/pacote/:indice" element={<Pacote />} />
        <Route path="lote/:nome/peca/:peca" element={<EditarPecaProducao />} />
        <Route path="lote/:nome/ferragem/:id" element={<EditarFerragem />} />
        <Route path="apontamento" element={<Apontamento />} />
        <Route path="apontamento-volume" element={<ApontamentoVolume />} />
      </Route>
    </Routes>
  );
}

export default Producao;