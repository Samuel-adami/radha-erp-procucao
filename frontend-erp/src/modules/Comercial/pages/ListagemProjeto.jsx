import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { fetchComAuth } from '../../../utils/fetchComAuth';

export default function ListagemProjeto() {
  const { id, tarefaId, ambiente } = useParams();
  const [itens, setItens] = useState([]);
  const [headers, setHeaders] = useState([]);

  useEffect(() => {
    const carregar = async () => {
      const t = await fetchComAuth(`/comercial/atendimentos/${id}/tarefas`);
      const orc = t.tarefas.find(tt => String(tt.id) === String(tarefaId));
      if (!orc) return;
      let dados = {};
      try { dados = orc.dados ? JSON.parse(orc.dados) : {}; } catch {}
      const info = dados.projetos?.[ambiente];
      const lista = info?.itens || [];
      setItens(lista);
      setHeaders(lista[0] ? Object.keys(lista[0]) : []);
    };
    carregar();
  }, [id, tarefaId, ambiente]);

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">Listagem do Projeto - {ambiente}</h3>
      <table className="min-w-full text-sm border">
        <thead>
          <tr>
            {headers.map(h => (
              <th key={h} className="border px-2 text-left">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {itens.map((it, idx) => (
            <tr key={idx}>
              {headers.map(h => (
                <td key={h} className="border px-2 text-left">{String(it[h] ?? '')}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      <Link to={`/comercial/${id}`} className="px-3 py-1 rounded bg-blue-600 text-white">Voltar</Link>
    </div>
  );
}
