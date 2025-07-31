import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { fetchComAuth } from '../../../utils/fetchComAuth';

// formata valores para moeda BRL
const currency = v =>
  Number(v || 0).toLocaleString('pt-BR', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });

function normalize(str) {
  return (str || '')
    .normalize('NFD')
    .replace(/\p{Diacritic}/gu, '')
    .trim()
    .toLowerCase();
}

export default function ListagemProjeto() {
  const params = useParams();
  const id = params.id;
  const tarefaId = params.tarefaId;
  const ambiente = decodeURIComponent(params.ambiente || '').trim();
  const [itens, setItens] = useState([]);
  const [cabecalho, setCabecalho] = useState({});
  const [valorTotal, setValorTotal] = useState(0);
  const [error, setError] = useState('');

  useEffect(() => {
    const carregar = async () => {
      try {
        const t = await fetchComAuth(`/comercial/atendimentos/${id}/tarefas`);
        const orc = t.tarefas.find(tt => String(tt.id) === String(tarefaId));
        if (!orc) return;
        let dados = {};
        try {
          dados = typeof orc.dados === 'string' ? JSON.parse(orc.dados) : orc.dados || {};
        } catch {
          // ignore parse errors
        }
        const projetos = dados.projetos || {};
        const chave = Object.keys(projetos).find(k => normalize(k) === normalize(ambiente));
        const info = chave ? projetos[chave] : projetos[ambiente];
        if (!info || !info.cabecalho || !Array.isArray(info.itens)) {
          throw new Error('Dados do projeto inválidos ou incompletos');
        }
        setCabecalho(info.cabecalho);
        setValorTotal(info.valor_total_orcamento || 0);
        setItens(info.itens);
      } catch (err) {
        console.error('Erro ao carregar orçamento', err);
        setError('Erro ao carregar orçamento: ' + err.message);
      }
    };
    carregar();
  }, [id, tarefaId, ambiente]);

  if (error) {
    return <div className="text-red-600">{error}</div>;
  }
  return (
    <div className="space-y-4">
      <div className="p-4 bg-gray-100 rounded shadow">
        <h3 className="text-lg font-semibold mb-2">Orçamento Final Gabster</h3>
        <div className="grid grid-cols-3 gap-4 text-sm">
          <div>
            <span className="font-medium">Código do Projeto:</span> {cabecalho.cd_projeto}
          </div>
          <div>
            <span className="font-medium">Nome do Cliente:</span> {cabecalho.nome_cliente}
          </div>
          <div>
            <span className="font-medium">Ambiente:</span> {cabecalho.ambiente}
          </div>
          <div className="col-span-3">
            <span className="font-medium">Valor Total:</span> R$ {currency(valorTotal)}
          </div>
        </div>
      </div>
      <table className="min-w-full text-sm divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-2 text-left">Ref</th>
            <th className="px-4 py-2 text-left">Produto</th>
            <th className="px-4 py-2 text-center">Qtde</th>
            <th className="px-4 py-2 text-left">Unidade</th>
            <th className="px-4 py-2 text-right">Valor Unitário</th>
            <th className="px-4 py-2 text-right">Total Produto</th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {itens.map((it, idx) => (
            <tr key={idx}>
              <td className="px-4 py-2">{it.ref}</td>
              <td className="px-4 py-2">{it.produto}</td>
              <td className="px-4 py-2 text-center">{it.qtde}</td>
              <td className="px-4 py-2">{it.unidade}</td>
              <td className="px-4 py-2 text-right">{currency(it.valor_unitario)}</td>
              <td className="px-4 py-2 text-right">{currency(it.total_produto)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <Link to={`/comercial/${id}`} className="px-3 py-1 rounded bg-blue-600 text-white">
        Voltar
      </Link>
    </div>
  );
}
