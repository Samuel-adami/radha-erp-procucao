// radha-erp/frontend-erp/src/modules/MarketingDigitalIA/index.jsx
import React from 'react';
import { Routes, Route, Link, Outlet, useResolvedPath, useMatch } from 'react-router-dom';
import { useUsuario } from '../../UserContext';
import Chat from './pages/Chat';
import NovaCampanha from './pages/NovaCampanha';
import NovaPublicacao from './pages/NovaPublicacao';
import PublicosAlvo from './pages/PublicosAlvo';
import GestaoLeads from './pages/GestaoLeads';
import LeadConversao from './pages/LeadConversao';

// Componente de layout para o módulo de Marketing Digital IA
function MarketingDigitalIALayout() {
  const resolved = useResolvedPath(''); // O caminho base para este módulo
  // Para o link "Assistente Sara" ser ativo quando estiver na raiz do módulo
  const matchChat = useMatch(`${resolved.pathname}`);
  const matchCampanha = useMatch(`${resolved.pathname}/nova-campanha`);
  const matchPublicacao = useMatch(`${resolved.pathname}/nova-publicacao`);
  const matchPublicos = useMatch(`${resolved.pathname}/publicos-alvo`);
  const matchLeads = useMatch(`${resolved.pathname}/gestao-leads`);
  const usuario = useUsuario();
  const possuiPermissao = p => usuario?.permissoes?.includes(p);

  return (
    <div className="p-4 bg-white rounded shadow-md">
      <h2 className="text-xl font-bold mb-4 text-blue-700">Módulo: Marketing Digital IA</h2>
      <nav className="flex gap-4 mb-4 border-b pb-2">
        {possuiPermissao('marketing-ia/chat') && (
          <Link
            to="." // Relativo ao path do módulo (MarketingDigitalIA)
            className={`px-3 py-1 rounded ${matchChat ? 'bg-blue-200 text-blue-800' : 'text-blue-600 hover:bg-blue-100'}`}
          >
            Assistente Sara
          </Link>
        )}
        {possuiPermissao('marketing-ia/nova-campanha') && (
          <Link
            to="nova-campanha" // Relativo ao path do módulo
            className={`px-3 py-1 rounded ${matchCampanha ? 'bg-blue-200 text-blue-800' : 'text-blue-600 hover:bg-blue-100'}`}
          >
            Nova Campanha
          </Link>
        )}
        {possuiPermissao('marketing-ia/nova-publicacao') && (
          <Link
            to="nova-publicacao" // Relativo ao path do módulo
            className={`px-3 py-1 rounded ${matchPublicacao ? 'bg-blue-200 text-blue-800' : 'text-blue-600 hover:bg-blue-100'}`}
          >
            Nova Publicação
          </Link>
        )}
        {possuiPermissao('marketing-ia/publicos-alvo') && (
          <Link
            to="publicos-alvo" // Relativo ao path do módulo
            className={`px-3 py-1 rounded ${matchPublicos ? 'bg-blue-200 text-blue-800' : 'text-blue-600 hover:bg-blue-100'}`}
          >
            Públicos Alvo
          </Link>
        )}
        {possuiPermissao('marketing-ia/gestao-leads') && (
          <Link
            to="gestao-leads"
            className={`px-3 py-1 rounded ${matchLeads ? 'bg-blue-200 text-blue-800' : 'text-blue-600 hover:bg-blue-100'}`}
          >
            Gestão de Leads
          </Link>
        )}
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
        <Route path="gestao-leads" element={<GestaoLeads />} />
        <Route path="gestao-leads/converter/:id" element={<LeadConversao />} />
      </Route>
    </Routes>
  );
}

export default MarketingDigitalIA;
