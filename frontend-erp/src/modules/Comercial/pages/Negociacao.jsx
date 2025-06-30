import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button } from '../../Producao/components/ui/button';
import { fetchComAuth } from '../../../utils/fetchComAuth';

const currency = v => Number(v || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

function Negociacao() {
  const { id, tarefaId } = useParams();
  const navigate = useNavigate();
  const [pontuacao, setPontuacao] = useState('4');
  const [condicoes, setCondicoes] = useState([]);
  const [condicaoId, setCondicaoId] = useState('');
  const [desc1, setDesc1] = useState('');
  const [desc2, setDesc2] = useState('');
  const [entrada, setEntrada] = useState('');
  const [numParcelas, setNumParcelas] = useState('');
  const [ambientes, setAmbientes] = useState([]);
  const [selecionados, setSelecionados] = useState({});
  const [custos, setCustos] = useState([]);
  const [novoCusto, setNovoCusto] = useState({ descricao: '', ambiente: '', valor: '' });
  const [mostrarFormCusto, setMostrarFormCusto] = useState(false);
  const [mostrarListaCustos, setMostrarListaCustos] = useState(false);
  const [editIdx, setEditIdx] = useState(-1);
  const [parcelas, setParcelas] = useState([]);
  const [totalVenda, setTotalVenda] = useState(0);

  useEffect(() => {
    const carregar = async () => {
      const at = await fetchComAuth(`/comercial/atendimentos/${id}`);
      const t = await fetchComAuth(`/comercial/atendimentos/${id}/tarefas`);
      const conds = await fetchComAuth('/comercial/condicoes-pagamento');
      setCondicoes(conds.condicoes || []);
      const proj = t.tarefas.find(tt => tt.nome === 'Projeto 3D');
      const orcAtual = t.tarefas.find(tt => String(tt.id) === String(tarefaId));
      let dadosProj = {};
      let dadosNeg = {};
      try { dadosProj = proj && proj.dados ? JSON.parse(proj.dados) : {}; } catch {}
      try { dadosNeg = orcAtual && orcAtual.dados ? JSON.parse(orcAtual.dados) : {}; } catch {}
      const projs = (at.atendimento.projetos || '').split(',').map(p => p.trim()).filter(Boolean);
      const listaAmb = projs.map(a => ({
        nome: a,
        valor: dadosProj.projetos?.[a]?.total || dadosProj.projetos?.[a]?.valor || 0
      }));
      setAmbientes(listaAmb);
      setSelecionados(listaAmb.reduce((acc, a) => ({ ...acc, [a.nome]: true }), {}));
      if (dadosNeg.pontuacao) setPontuacao(String(dadosNeg.pontuacao));
      if (dadosNeg.condicaoId) setCondicaoId(String(dadosNeg.condicaoId));
      if (dadosNeg.desconto1) setDesc1(String(dadosNeg.desconto1));
      if (dadosNeg.desconto2) setDesc2(String(dadosNeg.desconto2));
      if (dadosNeg.entrada) setEntrada(String(dadosNeg.entrada));
      if (dadosNeg.numParcelas) setNumParcelas(String(dadosNeg.numParcelas));
      if (dadosNeg.custos) setCustos(dadosNeg.custos);
    };
    carregar();
  }, [id, tarefaId]);

  const toggleAmb = nome => {
    setSelecionados(prev => ({ ...prev, [nome]: !prev[nome] }));
  };

  const addCusto = () => {
    if (!novoCusto.descricao || !novoCusto.ambiente || !novoCusto.valor) return;
    if (editIdx >= 0) {
      setCustos(prev => prev.map((c, i) => (i === editIdx ? { ...novoCusto, valor: parseFloat(novoCusto.valor) } : c)));
      setEditIdx(-1);
    } else {
      setCustos(prev => [...prev, { ...novoCusto, valor: parseFloat(novoCusto.valor) }]);
    }
    setNovoCusto({ descricao: '', ambiente: '', valor: '' });
    setMostrarFormCusto(false);
  };

  const somaCustos = nome => custos.filter(c => c.ambiente === nome).reduce((s, c) => s + Number(c.valor || 0), 0);
  const valorAmbiente = nome => {
    const amb = ambientes.find(a => a.nome === nome);
    return (amb?.valor || 0) + somaCustos(nome);
  };

  const editarCusto = idx => {
    const c = custos[idx];
    setNovoCusto({ descricao: c.descricao, ambiente: c.ambiente, valor: c.valor });
    setEditIdx(idx);
    setMostrarFormCusto(true);
  };

  const removerCusto = idx => {
    setCustos(prev => prev.filter((_, i) => i !== idx));
  };

  const valorOrcamento = nome => {
    let v = valorAmbiente(nome);
    if (pontuacao) v *= parseFloat(pontuacao);
    if (desc1) v *= 1 - parseFloat(desc1) / 100;
    if (desc2) v *= 1 - parseFloat(desc2) / 100;
    if (total > 0) v *= totalVenda / total;
    return v;
  };

  const totalBase = ambientes.reduce((s, a) => s + (selecionados[a.nome] ? valorAmbiente(a.nome) : 0), 0);
  let total = totalBase;
  if (pontuacao) total *= parseFloat(pontuacao);
  if (desc1) total *= 1 - parseFloat(desc1) / 100;
  if (desc2) total *= 1 - parseFloat(desc2) / 100;

  useEffect(() => {
    const c = condicoes.find(cc => String(cc.id) === String(condicaoId));
    if (!c) {
      setParcelas([]);
      setTotalVenda(total);
      return;
    }

    const temEntrada = parseFloat(entrada || 0) > 0;
    const tipo = temEntrada ? 'com' : 'sem';
    const listaOrig = c.parcelas?.[tipo] || [];
    const lista = [...listaOrig].sort((a, b) => (a.numero || 0) - (b.numero || 0));

    const max = c.numero_parcelas || (c.parcelas ? c.parcelas.sem.length + c.parcelas.com.length : 0);
    const nSel = numParcelas ? parseInt(numParcelas, 10) : max;
    const nCalculo = temEntrada ? nSel - 1 : nSel;
    const resto = total - parseFloat(entrada || 0);
    const valorBase = nCalculo > 0 ? resto / nCalculo : 0;

    let listaParcelas = lista.slice(0, Math.max(nCalculo, 0)).map((p, idx) => {
      const juros = parseFloat(p.retencao || 0) / 100;
      const valor = valorBase * (1 + juros);
      const numero = temEntrada ? idx + 2 : idx + 1;
      return { numero, valor };
    });

    if (temEntrada) {
      listaParcelas = [{ numero: 1, valor: parseFloat(entrada) || 0 }, ...listaParcelas];
    }

    setParcelas(listaParcelas);
    const soma = listaParcelas.reduce((s, p) => s + Number(p.valor || 0), 0);
    setTotalVenda(soma);
  }, [condicaoId, total, condicoes, numParcelas, entrada]);

  const salvar = async () => {
    const descricao = parcelas
      .map(p => `Parcela ${p.numero} = R$ ${currency(p.valor)}`)
      .join(', ');
    const dados = {
      pontuacao,
      condicaoId,
      entrada,
      numParcelas,
      desconto1: desc1,
      desconto2: desc2,
      custos,
      ambientes,
      selecionados,
      parcelas,
      descricao_pagamento: descricao,
      total: totalVenda || total,
    };
    await fetchComAuth(`/comercial/atendimentos/${id}/tarefas/${tarefaId}`, {
      method: 'PUT',
      body: JSON.stringify({ concluida: true, dados: JSON.stringify(dados) }),
    });
    navigate(`/comercial/${id}`);
  };

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">Negociação</h3>
      <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
        <label className="block">
          <span className="text-sm">Pontuação</span>
          <input type="number" className="input" value={pontuacao} onChange={e => setPontuacao(e.target.value)} />
        </label>
        <label className="block">
          <span className="text-sm">Desconto 1 (%)</span>
          <input type="number" className="input" value={desc1} onChange={e => setDesc1(e.target.value)} />
        </label>
        <label className="block">
          <span className="text-sm">Desconto 2 (%)</span>
          <input type="number" className="input" value={desc2} onChange={e => setDesc2(e.target.value)} />
        </label>
        <label className="block">
          <span className="text-sm">Condição de Pagamento</span>
          <select className="input" value={condicaoId} onChange={e => setCondicaoId(e.target.value)}>
            <option value="">Selecione</option>
            {condicoes.map(c => (
              <option key={c.id} value={c.id}>{c.nome}</option>
            ))}
          </select>
        </label>
        <label className="block">
          <span className="text-sm">Entrada (R$)</span>
          <input type="number" className="input" value={entrada} onChange={e => setEntrada(e.target.value)} />
        </label>
        <label className="block">
          <span className="text-sm">Parcelas</span>
          <select className="input" value={numParcelas} onChange={e => setNumParcelas(e.target.value)}>
            <option value="">Selecione</option>
            {(() => {
              const c = condicoes.find(cc => String(cc.id) === String(condicaoId));
              const n = c ? c.numero_parcelas || (c.parcelas ? c.parcelas.sem.length + c.parcelas.com.length : 0) : 0;
              return Array.from({ length: n }, (_, i) => i + 1).map(nPar => (
                <option key={nPar} value={nPar}>{nPar}</option>
              ));
            })()}
          </select>
        </label>
      </div>
      <div>
        <table className="w-full text-sm mb-2">
          <thead>
            <tr className="bg-gray-100">
              <th className="border px-2"></th>
              <th className="border px-2">Ambiente</th>
              <th className="border px-2">Custo Fábrica</th>
              <th className="border px-2">Custos Adicionais</th>
              <th className="border px-2">Custo Total</th>
              <th className="border px-2">Orçamento</th>
            </tr>
          </thead>
          <tbody>
            {ambientes.map(a => (
              <tr key={a.nome}>
                <td className="border px-2 text-center">
                  <input type="checkbox" checked={selecionados[a.nome] || false} onChange={() => toggleAmb(a.nome)} />
                </td>
                <td className="border px-2">{a.nome}</td>
                <td className="border px-2">{currency(a.valor)}</td>
                <td className="border px-2">{currency(somaCustos(a.nome))}</td>
                <td className="border px-2">{currency(valorAmbiente(a.nome))}</td>
                <td className="border px-2">{currency(valorOrcamento(a.nome))}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <div className="flex gap-2 mb-2">
          <Button size="sm" variant="secondary" onClick={() => setMostrarFormCusto(!mostrarFormCusto)}>
            {editIdx >= 0 ? 'Editar Custo' : 'Inserir Custos Adicionais'}
          </Button>
          <Button size="sm" variant="secondary" onClick={() => setMostrarListaCustos(!mostrarListaCustos)}>
            Listar Custos Adicionais
          </Button>
        </div>
        {mostrarFormCusto && (
          <div className="border p-2 rounded mt-2 space-y-2">
            <label className="block">
              <span className="text-sm">Descrição</span>
              <input className="input" value={novoCusto.descricao} onChange={e => setNovoCusto({ ...novoCusto, descricao: e.target.value })} />
            </label>
            <label className="block">
              <span className="text-sm">Ambiente</span>
              <select className="input" value={novoCusto.ambiente} onChange={e => setNovoCusto({ ...novoCusto, ambiente: e.target.value })}>
                <option value="">Selecione</option>
                {ambientes.map(a => (
                  <option key={a.nome} value={a.nome}>{a.nome}</option>
                ))}
              </select>
            </label>
            <label className="block">
              <span className="text-sm">Valor (R$)</span>
              <input type="number" className="input" value={novoCusto.valor} onChange={e => setNovoCusto({ ...novoCusto, valor: e.target.value })} />
            </label>
            <Button size="sm" onClick={addCusto}>{editIdx >= 0 ? 'Salvar' : 'Adicionar'}</Button>
          </div>
        )}
        {mostrarListaCustos && (
          <div className="border p-2 rounded mt-2">
            <table className="w-full text-sm mb-2">
              <thead>
                <tr className="bg-gray-100">
                  <th className="border px-2">Descrição</th>
                  <th className="border px-2">Ambiente</th>
                  <th className="border px-2">Valor</th>
                  <th className="border px-2">Ações</th>
                </tr>
              </thead>
              <tbody>
                {custos.map((c, idx) => (
                  <tr key={idx}>
                    <td className="border px-2">{c.descricao}</td>
                    <td className="border px-2">{c.ambiente}</td>
                    <td className="border px-2">{currency(c.valor)}</td>
                    <td className="border px-2 space-x-2">
                      <button className="text-blue-600" onClick={() => editarCusto(idx)}>Editar</button>
                      <button className="text-red-600" onClick={() => removerCusto(idx)}>Excluir</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
      <div className="flex flex-col md:flex-row gap-4">
        <div className="md:w-1/2">
          <h4 className="font-medium">Parcelas</h4>
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-100">
                <th className="border px-2">Número</th>
                <th className="border px-2">Valor</th>
              </tr>
            </thead>
            <tbody>
              {parcelas.map(p => (
                <tr key={p.numero}>
                  <td className="border px-2">{p.numero}</td>
                  <td className="border px-2">{currency(p.valor)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="md:w-1/2 flex items-center justify-center text-xl font-bold">
          Total: R$ {currency(totalVenda || total)}
        </div>
      </div>
      <div className="flex gap-2">
        <Button onClick={salvar}>Salvar Negociação</Button>
        <Button variant="secondary" onClick={() => navigate(`/comercial/${id}`)}>
          Cancelar
        </Button>
      </div>
    </div>
  );
}

export default Negociacao;
