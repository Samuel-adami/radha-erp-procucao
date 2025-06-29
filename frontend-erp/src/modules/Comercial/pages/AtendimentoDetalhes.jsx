import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Button } from '../../Producao/components/ui/button';
import { fetchComAuth } from '../../../utils/fetchComAuth';

function TarefaItem({ tarefa, atendimentoId, onChange, projetos }) {
  const [edit, setEdit] = useState(false);
  const [dados, setDados] = useState(() => tarefa.dados || {});

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

  if (tarefa.nome === 'Projeto 3D') {
    const ambientes = projetos;
    const dadosProj = dados.projetos || {};

    const handleFile = amb => async e => {
      const file = e.target.files[0];
      if (!file) return;
      const text = await file.text();
      const m = text.match(/(\d+[\.,]?\d*)/);
      const valor = m ? parseFloat(m[1].replace(',', '.')) : 0;
      setDados(prev => ({
        projetos: { ...prev.projetos, [amb]: { arquivo: file.name, valor } },
      }));
    };

    return (
      <li className="space-y-2 p-2 border rounded">
        <div className="font-medium mb-1">{tarefa.nome}</div>
        {ambientes.map(amb => (
          <div key={amb} className="space-y-1">
            <div className="flex items-center gap-2">
              <span>{amb}</span>
              <input type="file" accept=".xml,.txt,.csv" onChange={handleFile(amb)} />
            </div>
            {dadosProj[amb] && dadosProj[amb].valor > 0 && (
              <div className="text-sm text-gray-700 ml-2">
                {dadosProj[amb].arquivo} - Valor: {dadosProj[amb].valor}
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
      <div>
        <h4 className="font-medium mb-2">Tarefas</h4>
        <ul className="space-y-2">
          {tarefas.map(t => (
            <TarefaItem
              key={t.id}
              tarefa={t}
              atendimentoId={id}
              onChange={carregarTarefas}
              projetos={atendimento.projetos ? atendimento.projetos.split(',').map(p => p.trim()) : []}
            />
          ))}
        </ul>
      </div>
      <Button onClick={() => window.history.back()}>Voltar</Button>
    </div>
  );
}

export default AtendimentoDetalhes;
