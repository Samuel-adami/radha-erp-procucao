import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { fetchComAuth } from '../../../utils/fetchComAuth';

function currency(v) {
  return Number(v || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export default function ListagemProjeto() {
  const { id, tarefaId, ambiente } = useParams();
  const [itens, setItens] = useState([]);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    const carregar = async () => {
      const t = await fetchComAuth(`/comercial/atendimentos/${id}/tarefas`);
      const orc = t.tarefas.find(tt => String(tt.id) === String(tarefaId));
      if (!orc) return;
      let dados = {};
      try { dados = orc.dados ? JSON.parse(orc.dados) : {}; } catch {}
      const info = dados.projetos?.[ambiente];
      setItens(info?.itens || []);
      setTotal(info?.total || 0);
    };
    carregar();
  }, [id, tarefaId, ambiente]);

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">Listagem do Projeto - {ambiente}</h3>
      <table className="min-w-full text-sm border">
        <thead>
          <tr>
            <th className="border px-2">Descrição</th>
            <th className="border px-2">Unitário</th>
            <th className="border px-2">Qtde</th>
            <th className="border px-2">Total</th>
          </tr>
        </thead>
        <tbody>
          {itens.map((it, idx) => (
            <tr key={idx}>
              <td className="border px-2">{it.descricao}</td>
              <td className="border px-2 text-right">{currency(it.unitario)}</td>
              <td className="border px-2 text-right">{it.quantidade}</td>
              <td className="border px-2 text-right">{currency(it.total)}</td>
            </tr>
          ))}
        </tbody>
        <tfoot>
          <tr>
            <td colSpan="3" className="border px-2 text-right font-semibold">Total</td>
            <td className="border px-2 text-right font-semibold">{currency(total)}</td>
          </tr>
        </tfoot>
      </table>
      <Link to={`/comercial/${id}`} className="px-3 py-1 rounded bg-blue-600 text-white">Voltar</Link>
    </div>
  );
}
