import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Button } from '../../Producao/components/ui/button';
import { fetchComAuth } from '../../../utils/fetchComAuth';

function Atendimentos() {
  const [atendimentos, setAtendimentos] = useState([]);

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
            const first = tarefas.find((x) => x.dados?.data);
            const lastDoneIndex = tarefas.map((x) => Number(x.concluida)).lastIndexOf(1);
            const next = tarefas[lastDoneIndex + 1];
            const last = tarefas[lastDoneIndex];
            return {
              ...at,
              dataCadastro: at.data_cadastro || first?.dados?.data || '',
              setor: 'Comercial',
              status: next ? next.nome : 'Finalizado',
              ultimaAtualizacao: last?.dados?.data || '',
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

  const remover = async (id) => {
    if (!window.confirm('Excluir atendimento?')) return;
    await fetchComAuth(`/comercial/atendimentos/${id}`, { method: 'DELETE' });
    carregar();
  };

  return (
    <div>
      <div className="flex justify-end mb-4">
        <Link to="novo" className="bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-700">
          Novo Atendimento
        </Link>
      </div>
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-gray-100">
            <th className="border px-2">Data de Cadastro</th>
            <th className="border px-2">Código</th>
            <th className="border px-2">Cliente</th>
            <th className="border px-2">Setor</th>
            <th className="border px-2">Status</th>
            <th className="border px-2">Última Atualização</th>
            <th className="border px-2"></th>
          </tr>
        </thead>
        <tbody>
          {atendimentos.map((at) => (
            <tr key={at.id}>
              <td className="border px-2">{at.dataCadastro || '-'}</td>
              <td className="border px-2">
                <Link to={String(at.id)} className="hover:underline">
                  {at.codigo}
                </Link>
              </td>
              <td className="border px-2">{at.cliente}</td>
              <td className="border px-2">{at.setor || '-'}</td>
              <td className="border px-2">{at.status || '-'}</td>
              <td className="border px-2">{at.ultimaAtualizacao || '-'}</td>
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
