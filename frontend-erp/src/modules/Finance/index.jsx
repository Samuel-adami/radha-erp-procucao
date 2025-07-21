import React from 'react';
import { Routes, Route, Link, Outlet, useResolvedPath, useMatch } from 'react-router-dom';
import { useUsuario } from '../../UserContext';
import Banks from './pages/Banks';
import Accounts from './pages/Accounts';
import Payables from './pages/Payables';
import Receivables from './pages/Receivables';
import FiscalConfig from './pages/FiscalConfig';

function FinanceLayout() {
  const resolved = useResolvedPath('');
  const matchBanks = useMatch(`${resolved.pathname}/bancos`);
  const matchAccounts = useMatch(`${resolved.pathname}/contas`);
  const matchPayables = useMatch(`${resolved.pathname}/contas-pagar`);
  const matchReceivables = useMatch(`${resolved.pathname}/contas-receber`);
  const matchFiscal = useMatch(`${resolved.pathname}/config-fiscal`);
  const usuario = useUsuario();
  const possuiPermissao = p => usuario?.permissoes?.includes(p);

  return (
    <div className="p-4 bg-white rounded shadow-md">
      <h2 className="text-xl font-bold mb-4 text-blue-700">Módulo: Financeiro</h2>
      <nav className="flex gap-4 mb-4 border-b pb-2">
        {possuiPermissao('finance/bancos') && (
          <Link to="bancos" className={`px-3 py-1 rounded ${matchBanks ? 'bg-blue-200 text-blue-800' : 'text-blue-600 hover:bg-blue-100'}`}>Bancos</Link>
        )}
        {possuiPermissao('finance/contas') && (
          <Link to="contas" className={`px-3 py-1 rounded ${matchAccounts ? 'bg-blue-200 text-blue-800' : 'text-blue-600 hover:bg-blue-100'}`}>Contas</Link>
        )}
        {possuiPermissao('finance/contas-pagar') && (
          <Link to="contas-pagar" className={`px-3 py-1 rounded ${matchPayables ? 'bg-blue-200 text-blue-800' : 'text-blue-600 hover:bg-blue-100'}`}>Contas a Pagar</Link>
        )}
        {possuiPermissao('finance/contas-receber') && (
          <Link to="contas-receber" className={`px-3 py-1 rounded ${matchReceivables ? 'bg-blue-200 text-blue-800' : 'text-blue-600 hover:bg-blue-100'}`}>Contas a Receber</Link>
        )}
        {possuiPermissao('finance/config-fiscal') && (
          <Link to="config-fiscal" className={`px-3 py-1 rounded ${matchFiscal ? 'bg-blue-200 text-blue-800' : 'text-blue-600 hover:bg-blue-100'}`}>Configuração Fiscal</Link>
        )}
      </nav>
      <Outlet />
    </div>
  );
}

function Finance() {
  return (
    <Routes>
      <Route path="/" element={<FinanceLayout />}>
        <Route index element={<p>Selecione uma opção</p>} />
        <Route path="bancos" element={<Banks />} />
        <Route path="contas" element={<Accounts />} />
        <Route path="contas-pagar" element={<Payables />} />
        <Route path="contas-receber" element={<Receivables />} />
        <Route path="config-fiscal" element={<FiscalConfig />} />
      </Route>
    </Routes>
  );
}

export default Finance;
