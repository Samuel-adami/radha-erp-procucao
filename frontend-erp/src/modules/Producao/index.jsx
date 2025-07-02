// radha-erp/frontend-erp/src/modules/Producao/index.jsx
import React from 'react';
import { Routes, Route, Link, Outlet, useResolvedPath, useMatch } from 'react-router-dom';
import { useUsuario } from '../../UserContext';
// Importa os componentes renomeados do AppProducao.jsx
import { HomeProducao, LoteProducao, EditarPecaProducao, Pacote, Apontamento, ApontamentoVolume, EditarFerragem, Nesting, VisualizacaoNesting, ConfigMaquina, LotesOcorrencia, CadastroMotivos, RelatorioOcorrencias, EditarLoteOcorrencia, PacoteOcorrencia } from './AppProducao';
import CadastroChapas from './components/CadastroChapas';

function ProducaoLayout() {
  const resolved = useResolvedPath(''); // O caminho base para este módulo
  const matchHome = useMatch({ path: `${resolved.pathname}`, end: true });
  // Para o link "Lotes Produção" ser ativo quando estiver na raiz do módulo
  const matchLote = useMatch(`${resolved.pathname}/lote/*`); // Matches /producao/lote/qualquer_nome
  const matchApontamento = useMatch({ path: `${resolved.pathname}/apontamento`, end: true });
  const matchVolume = useMatch({ path: `${resolved.pathname}/apontamento-volume`, end: true });
  const matchNesting = useMatch({ path: `${resolved.pathname}/nesting`, end: true });
  const matchChapas = useMatch({ path: `${resolved.pathname}/chapas`, end: true });
  const matchOcorr = useMatch({ path: `${resolved.pathname}/ocorrencias`, end: false });
  const matchRelatorio = useMatch({ path: `${resolved.pathname}/relatorios/ocorrencias`, end: false });
  const usuario = useUsuario();
  const possuiPermissao = p => usuario?.permissoes?.includes(p);

  return (
    <div className="p-4 bg-white rounded shadow-md">
      <h2 className="text-xl font-bold mb-4 text-blue-700">Módulo: Produção</h2>
      <nav className="flex gap-4 mb-4 border-b pb-2">
        {possuiPermissao('producao') && (
          <Link
            to="." // Relativo ao path do módulo (Producao)
            className={`px-3 py-1 rounded ${matchHome ? 'bg-blue-200 text-blue-800' : 'text-blue-600 hover:bg-blue-100'}`}
          >
            Lotes Produção
          </Link>
        )}
        {possuiPermissao('producao/apontamento') && (
          <Link
            to="apontamento"
            className={`px-3 py-1 rounded ${matchApontamento ? 'bg-blue-200 text-blue-800' : 'text-blue-600 hover:bg-blue-100'}`}
          >
            Apontamento
          </Link>
        )}
        {possuiPermissao('producao/apontamento-volume') && (
          <Link
            to="apontamento-volume"
            className={`px-3 py-1 rounded ${matchVolume ? 'bg-blue-200 text-blue-800' : 'text-blue-600 hover:bg-blue-100'}`}
          >
            Apontamento Volume
          </Link>
        )}
        {possuiPermissao('producao/nesting') && (
          <Link
            to="nesting"
            className={`px-3 py-1 rounded ${matchNesting ? 'bg-blue-200 text-blue-800' : 'text-blue-600 hover:bg-blue-100'}`}
          >
            Nesting
          </Link>
        )}
        {possuiPermissao('producao/chapas') && (
          <Link
            to="chapas"
            className={`px-3 py-1 rounded ${matchChapas ? 'bg-blue-200 text-blue-800' : 'text-blue-600 hover:bg-blue-100'}`}
          >
            Chapas
          </Link>
        )}
        {possuiPermissao('producao/ocorrencias') && (
          <Link
            to="ocorrencias"
            className={`px-3 py-1 rounded ${matchOcorr ? 'bg-blue-200 text-blue-800' : 'text-blue-600 hover:bg-blue-100'}`}
          >
            Lotes Ocorrência
          </Link>
        )}
        {possuiPermissao('producao/relatorios/ocorrencias') && (
          <Link
            to="relatorios/ocorrencias"
            className={`px-3 py-1 rounded ${matchRelatorio ? 'bg-blue-200 text-blue-800' : 'text-blue-600 hover:bg-blue-100'}`}
          >
            Relatórios
          </Link>
        )}
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
        <Route path="nesting" element={<Nesting />} />
        <Route path="nesting/visualizacao" element={<VisualizacaoNesting />} />
        <Route path="nesting/config-maquina" element={<ConfigMaquina />} />
        <Route path="chapas" element={<CadastroChapas />} />
        <Route path="ocorrencias" element={<LotesOcorrencia />} />
        <Route path="ocorrencias/editar/:id" element={<EditarLoteOcorrencia />} />
        <Route path="ocorrencias/pacote/:id" element={<PacoteOcorrencia />} />
        <Route path="ocorrencias/motivos" element={<CadastroMotivos />} />
        <Route path="relatorios/ocorrencias" element={<RelatorioOcorrencias />} />
      </Route>
    </Routes>
  );
}

export default Producao;