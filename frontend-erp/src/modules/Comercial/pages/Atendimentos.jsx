import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Button } from '../../Producao/components/ui/button';
import { fetchComAuth } from '../../../utils/fetchComAuth';
import { formatDateBr } from '../../../utils/formatDateBr';

function Atendimentos() {
  const [atendimentos, setAtendimentos] = useState([]);
  const [coluna, setColuna] = useState('Todas');
  const [ordenar, setOrdenar] = useState({ col: 'dataCadastroRaw', dir: 'asc' });
  const [filtroTexto, setFiltroTexto] = useState('');
  const [filtroInicio, setFiltroInicio] = useState('');
  const [filtroFim, setFiltroFim] = useState('');

  const colunas = [
    { id: 'dataCadastro', label: 'Data de Cadastro', sortKey: 'dataCadastroRaw' },
    { id: 'codigo', label: 'Código', sortKey: 'codigo' },
    { id: 'cliente', label: 'Cliente', sortKey: 'cliente' },
    { id: 'setor', label: 'Setor', sortKey: 'setor' },
    { id: 'status', label: 'Status', sortKey: 'status' },
    {
      id: 'ultimaAtualizacao',
      label: 'Última Atualização',
      sortKey: 'ultimaAtualizacaoRaw',
    },
  ];

  const carregar = async () => {
    try {
      const dados = await fetchComAuth('/comercial/atendimentos');
      const lista = await Promise.all(
        dados.atendimentos.map(async (at) => {
          try {
            const t = await fetchComAuth(`/comercial/atendimentos/${at.id}/tarefas`);
            const tarefas = t.tarefas.map((tt) => {
              let dadosT;
              try {
                dadosT = tt.dados ? JSON.parse(tt.dados) : {};
              } catch {
                dadosT = {};
              }
              return { ...tt, dados: dadosT };
            });
            const first = tarefas.find((x) => x.dados?.data || x.data_execucao);
            const lastDoneIndex = tarefas.map((x) => Number(x.concluida)).lastIndexOf(1);
            const next = tarefas[lastDoneIndex + 1];
            const last = tarefas[lastDoneIndex];
            const dataCadastroRaw = at.data_cadastro || first?.dados?.data || first?.data_execucao || '';
            const ultimaRaw = last?.dados?.data || last?.data_execucao || '';
            return {
              ...at,
              dataCadastro: formatDateBr(dataCadastroRaw),
              dataCadastroRaw,
              setor: 'Comercial',
              status: next ? next.nome : 'Finalizado',
              ultimaAtualizacao: formatDateBr(ultimaRaw),
              ultimaAtualizacaoRaw: ultimaRaw,
            };
          } catch {
            return { ...at, setor: 'Comercial' };
          }
        })
      );
      setAtendimentos(lista);
    } catch (err) {
      console.error('Erro ao carregar atendimentos', err);
    }
  };

  useEffect(() => {
    carregar();
  }, []);

  useEffect(() => {
    setFiltroTexto('');
    setFiltroInicio('');
    setFiltroFim('');
  }, [coluna]);

  const remover = async (id) => {
    if (!window.confirm('Excluir atendimento?')) return;
    await fetchComAuth(`/comercial/atendimentos/${id}`, { method: 'DELETE' });
    carregar();
  };

  const listaFiltrada = atendimentos.filter((at) => {
    if (coluna === 'Todas') return true;
    const info = colunas.find((c) => c.id === coluna);
    if (!info) return true;
    const valor = at[coluna] || '';
    if (coluna === 'dataCadastro' || coluna === 'ultimaAtualizacao') {
      const raw = at[info.sortKey];
      if (!raw) return false;
      const dt = new Date(raw);
      if (filtroInicio && new Date(filtroInicio) > dt) return false;
      if (filtroFim && new Date(filtroFim) < dt) return false;
      return true;
    }
    return String(valor).toLowerCase().includes(filtroTexto.toLowerCase());
  });

  const listaOrdenada = [...listaFiltrada].sort((a, b) => {
    const col = ordenar.col;
    const av = a[col] || '';
    const bv = b[col] || '';
    if (col.includes('Raw')) {
      const ad = new Date(av);
      const bd = new Date(bv);
      return ordenar.dir === 'asc' ? ad - bd : bd - ad;
    }
    if (av < bv) return ordenar.dir === 'asc' ? -1 : 1;
    if (av > bv) return ordenar.dir === 'asc' ? 1 : -1;
    return 0;
  });

  return (
    <div>
      <div className="flex justify-between mb-4">
        <div className="flex gap-2 items-end">
          <select
            className="border px-2 py-1"
            value={coluna}
            onChange={e => setColuna(e.target.value)}
          >
            <option value="Todas">Todas</option>
            {colunas.map(c => (
              <option key={c.id} value={c.id}>
                {c.label}
              </option>
            ))}
          </select>
          {coluna !== 'Todas' && (
            coluna === 'dataCadastro' || coluna === 'ultimaAtualizacao' ? (
              <>
                <input
                  type="date"
                  className="border px-2 py-1"
                  value={filtroInicio}
                  onChange={e => setFiltroInicio(e.target.value)}
                />
                <input
                  type="date"
                  className="border px-2 py-1"
                  value={filtroFim}
                  onChange={e => setFiltroFim(e.target.value)}
                />
              </>
            ) : (
              <input
                className="border px-2 py-1"
                placeholder="Filtrar..."
                value={filtroTexto}
                onChange={e => setFiltroTexto(e.target.value)}
              />
            )
          )}
        </div>
        <Link to="novo" className="bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-700">
          Novo Atendimento
        </Link>
      </div>
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-gray-100">
            {colunas.map(c =>
              coluna === 'Todas' || coluna === c.id ? (
                <th
                  key={c.id}
                  className="border px-2 cursor-pointer"
                  onClick={() =>
                    setOrdenar(prev => ({
                      col: c.sortKey,
                      dir: prev.col === c.sortKey && prev.dir === 'asc' ? 'desc' : 'asc',
                    }))
                  }
                >
                  {c.label}
                </th>
              ) : null
            )}
            <th className="border px-2"></th>
          </tr>
        </thead>
        <tbody>
          {listaOrdenada.map(at => (
            <tr key={at.id}>
              {(coluna === 'Todas' || coluna === 'dataCadastro') && (
                <td className="border px-2">{at.dataCadastro || '-'}</td>
              )}
              {(coluna === 'Todas' || coluna === 'codigo') && (
                <td className="border px-2">
                  <Link to={String(at.id)} className="hover:underline">
                    {at.codigo}
                  </Link>
                </td>
              )}
              {(coluna === 'Todas' || coluna === 'cliente') && (
                <td className="border px-2">{at.cliente}</td>
              )}
              {(coluna === 'Todas' || coluna === 'setor') && (
                <td className="border px-2">{at.setor || '-'}</td>
              )}
              {(coluna === 'Todas' || coluna === 'status') && (
                <td className="border px-2">{at.status || '-'}</td>
              )}
              {(coluna === 'Todas' || coluna === 'ultimaAtualizacao') && (
                <td className="border px-2">{at.ultimaAtualizacao || '-'}</td>
              )}
              <td className="border px-2 text-center">
                <Button size="sm" variant="destructive" onClick={() => remover(at.id)}>
                  Excluir
                </Button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default Atendimentos;
