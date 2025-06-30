import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Button } from '../../Producao/components/ui/button';
import { fetchComAuth } from '../../../utils/fetchComAuth';

function TarefaItem({ tarefa, atendimentoId, onChange, projetos, bloqueada }) {
  const [edit, setEdit] = useState(false);
  const [dados, setDados] = useState(() => tarefa.dados || {});

  if (bloqueada && !tarefa.concluida) {
    return (
      <li className="p-2 border rounded text-gray-500">
        <span>{tarefa.nome} - aguarde a conclusão da tarefa anterior</span>
      </li>
    );
  }

  const salvar = async concl => {
    await fetchComAuth(
      `/comercial/atendimentos/${atendimentoId}/tarefas/${tarefa.id}`,
      {
        method: 'PUT',
        body: JSON.stringify({
          concluida: concl,
          dados: JSON.stringify(dados),
        }),
      }
    );
    await onChange();
    setEdit(false);
  };

  if (tarefa.nome === 'Contato Inicial' || tarefa.nome === 'Apresentação') {
    return (
      <li className="space-y-1 p-2 border rounded">
        <div className="flex items-center gap-2">
          <span className={tarefa.concluida ? 'line-through' : ''}>{tarefa.nome}</span>
          {!edit && (
            <Button size="sm" variant="outline" onClick={() => setEdit(true)}>
              {tarefa.concluida ? 'Editar' : 'Preencher'}
            </Button>
          )}
        </div>
        {edit && (
          <div className="space-y-2 mt-2">
            <input
              type="date"
              className="input"
              value={dados.data || ''}
              onChange={e => setDados({ ...dados, data: e.target.value })}
            />
            <textarea
              className="input"
              rows="3"
              placeholder="Resumo ou conversa"
              value={dados.resumo || ''}
              onChange={e => setDados({ ...dados, resumo: e.target.value })}
            />
            <Button size="sm" onClick={() => salvar(true)}>
              Salvar
            </Button>
          </div>
        )}
        {tarefa.concluida && !edit && dados.data && (
          <div className="text-sm text-gray-700 mt-1">
            {dados.data} - {dados.resumo}
          </div>
        )}
      </li>
    );
  }

  if (tarefa.nome === 'Visita Técnica/Briefing') {
    return (
      <li className="space-y-1 p-2 border rounded">
        <div className="flex items-center gap-2">
          <span className={tarefa.concluida ? 'line-through' : ''}>{tarefa.nome}</span>
          <Link
            to={`/formularios/briefing-vendas/${atendimentoId}/${tarefa.id}`}
            className="px-2 py-1 text-sm rounded bg-blue-600 text-white"
          >
            {tarefa.concluida ? 'Editar' : 'Preencher'}
          </Link>
        </div>
      </li>
    );
  }

  if (tarefa.nome === 'Projeto 3D') {
    const ambientes = projetos;
    const dadosProj = dados.projetos || {};

    const handleFile = amb => async e => {
      const file = e.target.files[0];
      if (!file) return;
      const form = new FormData();
      form.append('file', file);
      const info = await fetchComAuth('/comercial/leitor-orcamento-gabster', {
        method: 'POST',
        body: form,
      });
      setDados(prev => ({
        projetos: { ...prev.projetos, [amb]: { arquivo: file.name, ...info } },
      }));
    };

    return (
      <li className="space-y-2 p-2 border rounded">
        <div className="font-medium mb-1">{tarefa.nome}</div>
        {ambientes.map(amb => (
          <div key={amb} className="space-y-1">
            <div className="flex items-center gap-2">
              <span>{amb}</span>
              <input type="file" accept="application/pdf" onChange={handleFile(amb)} />
              {dadosProj[amb] && (
                <Link
                  to={`listagem/${tarefa.id}/${encodeURIComponent(amb)}`}
                  className="text-sm text-blue-600 underline"
                >
                  Listagem
                </Link>
              )}
            </div>
            {dadosProj[amb] && dadosProj[amb].total > 0 && (
              <div className="text-sm text-gray-700 ml-2">
                {dadosProj[amb].arquivo} - Valor: {dadosProj[amb].total}
              </div>
            )}
          </div>
        ))}
        <Button size="sm" onClick={() => salvar(true)}>
          Salvar Projeto 3D
        </Button>
      </li>
    );
  }

  if (tarefa.nome === 'Orçamento') {
    return (
      <li className="space-y-2 p-2 border rounded">
        <div className="font-medium mb-1">{tarefa.nome}</div>
        <div className="flex items-center gap-2 mt-2">
          <Link
            to={`negociacao/${tarefa.id}`}
            className="px-2 py-1 text-sm rounded bg-blue-600 text-white"
          >
            {tarefa.concluida ? 'Editar' : 'Negociar'}
          </Link>
          {tarefa.concluida && tarefa.dados?.total && (
            <div className="text-sm text-gray-700">
              Valor Final: {tarefa.dados.total}
              {tarefa.dados.descricao_pagamento ? ` - ${tarefa.dados.descricao_pagamento}` : ''}
            </div>
          )}
        </div>
      </li>
    );
  }

  if (tarefa.nome === 'Venda Concluída') {
    return (
      <li className="space-y-1 p-2 border rounded">
        <div className="flex items-center gap-2">
          <span className={tarefa.concluida ? 'line-through' : ''}>{tarefa.nome}</span>
          {!edit && (
            <Button size="sm" variant="outline" onClick={() => setEdit(true)}>
              {tarefa.concluida ? 'Refazer' : 'Gerar Contrato'}
            </Button>
          )}
        </div>
        {edit && (
          <div className="space-y-2 mt-2">
            <input
              type="date"
              className="input"
              value={dados.data || ''}
              onChange={e => setDados({ ...dados, data: e.target.value })}
            />
            <Button size="sm" onClick={() => salvar(true)}>
              Gerar Contrato
            </Button>
          </div>
        )}
        {tarefa.concluida && !edit && dados.data && (
          <div className="text-sm text-gray-700 mt-1">Contrato gerado em {dados.data}</div>
        )}
      </li>
    );
  }

  // tarefas não implementadas - exibir apenas nome
  return (
    <li className="flex items-center gap-2 p-2 border rounded">
      <span className={tarefa.concluida ? 'line-through' : ''}>{tarefa.nome}</span>
    </li>
  );
}

function AtendimentoDetalhes() {
  const { id } = useParams();
  const [atendimento, setAtendimento] = useState(null);
  const [tarefas, setTarefas] = useState([]);

  const carregarTarefas = async () => {
    const t = await fetchComAuth(`/comercial/atendimentos/${id}/tarefas`);
    // parse dados JSON if exists
    setTarefas(
      t.tarefas.map(tt => {
        let dados;
        try {
          dados = tt.dados ? JSON.parse(tt.dados) : {};
        } catch (err) {
          dados = {};
        }
        return { ...tt, dados };
      })
    );
  };

  useEffect(() => {
    const carregar = async () => {
      try {
        const dados = await fetchComAuth(`/comercial/atendimentos/${id}`);
        setAtendimento(dados.atendimento);
        await carregarTarefas();
      } catch (err) {
        console.error('Erro ao carregar detalhes', err);
      }
    };
    carregar();
  }, [id]);


  if (!atendimento) {
    return <p>Carregando...</p>;
  }

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-bold">
        Atendimento {atendimento.codigo} - {atendimento.cliente}
      </h3>
      <div className="p-2 bg-gray-100 rounded space-y-1 text-sm">
        <div><strong>Procedência:</strong> {atendimento.procedencia || '-'}</div>
        <div><strong>Vendedor:</strong> {atendimento.vendedor || '-'}</div>
        <div><strong>Telefone:</strong> {atendimento.telefone || '-'}</div>
        <div><strong>E-mail:</strong> {atendimento.email || '-'}</div>
        <div>
          <strong>Endereço:</strong> {atendimento.rua || ''} {atendimento.numero || ''} - {atendimento.cidade || ''}/{atendimento.estado || ''}
        </div>
        <Link
          to={`/comercial/${id}/editar`}
          className="text-blue-600 hover:underline"
        >
          Editar Atendimento
        </Link>
      </div>
      <div>
        <h4 className="font-medium mb-2">Tarefas</h4>
        <ul className="space-y-2">
          {tarefas.map((t, idx) => (
            <TarefaItem
              key={t.id}
              tarefa={t}
              atendimentoId={id}
              onChange={carregarTarefas}
              projetos={atendimento.projetos ? atendimento.projetos.split(',').map(p => p.trim()) : []}
              bloqueada={tarefas.slice(0, idx).some(tt => !tt.concluida)}
            />
          ))}
        </ul>
      </div>
      <Button onClick={() => window.history.back()}>Voltar</Button>
    </div>
  );
}

export default AtendimentoDetalhes;
