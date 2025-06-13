// radha-erp/frontend-erp/src/modules/MarketingDigitalIA/index.jsx
import React from 'react';
import { Routes, Route, Link, Outlet, useResolvedPath, useMatch } from 'react-router-dom';
import Chat from './pages/Chat';
import NovaCampanha from './pages/NovaCampanha';
import NovaPublicacao from './pages/NovaPublicacao';
import PublicosAlvo from './pages/PublicosAlvo';

// Componente de layout para o módulo de Marketing Digital IA
function MarketingDigitalIALayout() {
  const resolved = useResolvedPath(''); // O caminho base para este módulo
  // Para o link "Assistente Sara" ser ativo quando estiver na raiz do módulo
  const matchChat = useMatch(`${resolved.pathname}`);
  const matchCampanha = useMatch(`${resolved.pathname}/nova-campanha`);
  const matchPublicacao = useMatch(`${resolved.pathname}/nova-publicacao`);
  const matchPublicos = useMatch(`${resolved.pathname}/publicos-alvo`);

  return (
    <div className="p-4 bg-white rounded shadow-md">
      <h2 className="text-xl font-bold mb-4 text-purple-700">Módulo: Marketing Digital IA</h2>
      <nav className="flex gap-4 mb-4 border-b pb-2">
        <Link
          to="." // Relativo ao path do módulo (MarketingDigitalIA)
          className={`px-3 py-1 rounded ${matchChat ? 'bg-purple-200 text-purple-800' : 'text-purple-600 hover:bg-purple-100'}`}
        >
          Assistente Sara
        </Link>
        <Link
          to="nova-campanha" // Relativo ao path do módulo
          className={`px-3 py-1 rounded ${matchCampanha ? 'bg-purple-200 text-purple-800' : 'text-purple-600 hover:bg-purple-100'}`}
        >
          Nova Campanha
        </Link>
        <Link
          to="nova-publicacao" // Relativo ao path do módulo
          className={`px-3 py-1 rounded ${matchPublicacao ? 'bg-purple-200 text-purple-800' : 'text-purple-600 hover:bg-purple-100'}`}
        >
          Nova Publicação
        </Link>
        <Link
          to="publicos-alvo" // Relativo ao path do módulo
          className={`px-3 py-1 rounded ${matchPublicos ? 'bg-purple-200 text-purple-800' : 'text-purple-600 hover:bg-purple-100'}`}
        >
          Públicos Alvo
        </Link>
      </nav>
      <Outlet /> {/* Renderiza as rotas aninhadas aqui */}
    </div>
  );
}

function MarketingDigitalIA() {
  return (
    <Routes>
      <Route path="/" element={<MarketingDigitalIALayout />}>
        <Route index element={<Chat />} /> {/* Rota padrão do módulo */}
        <Route path="nova-campanha" element={<NovaCampanha />} />
        <Route path="nova-publicacao" element={<NovaPublicacao />} />
        <Route path="publicos-alvo" element={<PublicosAlvo />} />
      </Route>
    </Routes>
  );
}

export default MarketingDigitalIA;