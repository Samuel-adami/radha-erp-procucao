import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Button } from '../../Producao/components/ui/button';
import { fetchComAuth } from '../../../utils/fetchComAuth';

function TarefaItem({ tarefa, atendimentoId, onChange, projetos, bloqueada }) {
  const [edit, setEdit] = useState(false);
  const [dados, setDados] = useState(() => tarefa.dados || {});

  const desfazer = async () => {
    const senha = window.prompt('Digite sua senha para desfazer a tarefa');
    if (!senha) return;
    const usuario = JSON.parse(localStorage.getItem('usuario') || '{}');
    try {
      const auth = await fetchComAuth('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ username: usuario.username, password: senha }),
      });
      if (!['Diretor', 'Gerente', 'Coordenador'].includes(auth.usuario?.cargo)) {
        alert('Usuário sem permissão para desfazer');
        return;
      }
      await fetchComAuth(
        `/comercial/atendimentos/${atendimentoId}/tarefas/${tarefa.id}`,
        {
          method: 'PUT',
          body: JSON.stringify({ concluida: false, dados: JSON.stringify({}) }),
        }
      );
      await onChange();
      setEdit(false);
    } catch (err) {
      alert('Senha incorreta ou erro ao desfazer');
    }
  };

  if (bloqueada && !tarefa.concluida) {
    return (
      <li className="p-2 border rounded bg-yellow-100 text-gray-500">
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
      <li className={`space-y-1 p-2 border rounded ${tarefa.concluida ? 'bg-green-200' : 'bg-yellow-100'}`}>
        <div className="flex items-center gap-2">
          <span>{tarefa.nome}</span>
          {!edit && (
            <Button
              size="sm"
              variant="outline"
              className="bg-white text-black"
              onClick={() => setEdit(true)}
            >
              {tarefa.concluida ? 'Editar' : 'Preencher'}
            </Button>
          )}
          {tarefa.concluida && (
            <Button
              size="sm"
              variant="destructive"
              className="bg-white text-black"
              onClick={desfazer}
            >
              Desfazer
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
            <Button size="sm" className="bg-white text-black" onClick={() => salvar(true)}>
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
      <li className={`space-y-1 p-2 border rounded ${tarefa.concluida ? 'bg-green-200' : 'bg-yellow-100'}`}>
        <div className="flex items-center gap-2">
          <span>{tarefa.nome}</span>
          <Link
            to={`/formularios/briefing-vendas/${atendimentoId}/${tarefa.id}`}
            className="px-2 py-1 text-sm rounded bg-white text-black"
          >
            {tarefa.concluida ? 'Editar' : 'Preencher'}
          </Link>
          {tarefa.concluida && (
            <Button
              size="sm"
              variant="destructive"
              className="bg-white text-black"
              onClick={desfazer}
            >
              Desfazer
            </Button>
          )}
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
      <li className={`space-y-2 p-2 border rounded ${tarefa.concluida ? 'bg-green-200' : 'bg-yellow-100'}`}>
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
        <div className="flex gap-2">
          <Button size="sm" className="bg-white text-black" onClick={() => salvar(true)}>
            Salvar Projeto 3D
          </Button>
          {tarefa.concluida && (
            <Button
              size="sm"
              variant="destructive"
              className="bg-white text-black"
              onClick={desfazer}
            >
              Desfazer
            </Button>
          )}
        </div>
      </li>
    );
  }

  if (tarefa.nome === 'Orçamento' || tarefa.nome === 'Negociação') {
    return (
      <li className={`space-y-2 p-2 border rounded ${tarefa.concluida ? 'bg-green-200' : 'bg-yellow-100'}`}>
        <div className="font-medium mb-1">Negociação</div>
        <div className="flex items-center gap-2 mt-2">
          <Link
            to={`negociacao/${tarefa.id}`}
            className="px-2 py-1 text-sm rounded bg-white text-black"
          >
            {tarefa.concluida ? 'Editar' : 'Negociar'}
          </Link>
          {tarefa.concluida && tarefa.dados?.total && (
            <div className="text-sm text-gray-700">
              Valor Final: {tarefa.dados.total}
              {tarefa.dados.descricao_pagamento ? ` - ${tarefa.dados.descricao_pagamento}` : ''}
            </div>
          )}
          {tarefa.concluida && (
            <Button
              size="sm"
              variant="destructive"
              className="bg-white text-black"
              onClick={desfazer}
            >
              Desfazer
            </Button>
          )}
        </div>
      </li>
    );
  }

  if (tarefa.nome === 'Venda Concluída' || tarefa.nome === 'Fechamento da Venda') {
    return (
      <li className={`space-y-1 p-2 border rounded ${tarefa.concluida ? 'bg-green-200' : 'bg-yellow-100'}`}>
        <div className="flex items-center gap-2">
          <span>Fechamento da Venda</span>
          {!edit && (
            <Button
              size="sm"
              variant="outline"
              className="bg-white text-black"
              onClick={() => setEdit(true)}
            >
              {tarefa.concluida ? 'Refazer' : 'Gerar Contrato'}
            </Button>
          )}
          {tarefa.concluida && (
            <Button
              size="sm"
              variant="destructive"
              className="bg-white text-black"
              onClick={desfazer}
            >
              Desfazer
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
            <Button size="sm" className="bg-white text-black" onClick={() => salvar(true)}>
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

  if (tarefa.nome === 'Pasta Final') {
    const docs = [
      { campo: 'contrato_assinado', label: 'Contrato Assinado' },
      { campo: 'projeto_executivo_assinado', label: 'Projeto Executivo Assinado' },
      { campo: 'termo_preparacao_assinado', label: 'Termo de Preparação Assinado' },
      { campo: 'ficha_medidas', label: 'Ficha de Medidas' },
    ];
    const todos = docs.every(d => dados[d.campo]);

    const handleDoc = campo => e => {
      const file = e.target.files[0];
      if (file) setDados(prev => ({ ...prev, [campo]: file.name }));
    };

    return (
      <li className={`space-y-2 p-2 border rounded ${tarefa.concluida ? 'bg-green-200' : 'bg-yellow-100'}`}>
        <div className="font-medium">Pasta Final</div>
        {docs.map(doc => (
          <div key={doc.campo} className="flex items-center gap-2">
            <span>{doc.label}</span>
            <input type="file" accept=".pdf,.doc,.docx" onChange={handleDoc(doc.campo)} />
            {dados[doc.campo] && <span className="text-sm text-gray-700">{dados[doc.campo]}</span>}
          </div>
        ))}
        <div className="flex gap-2">
          <Button
            size="sm"
            className="bg-white text-black"
            onClick={() => salvar(true)}
            disabled={!todos}
          >
            Finalizar Pasta
          </Button>
          {tarefa.concluida && (
            <Button
              size="sm"
              variant="destructive"
              className="bg-white text-black"
              onClick={desfazer}
            >
              Desfazer
            </Button>
          )}
        </div>
      </li>
    );
  }

  // tarefas não implementadas - exibir apenas nome
  return (
    <li className={`flex items-center gap-2 p-2 border rounded ${tarefa.concluida ? 'bg-green-200' : 'bg-yellow-100'}`}>
      <span>{tarefa.nome}</span>
      {tarefa.concluida && (
        <Button
          size="sm"
          variant="destructive"
          className="bg-white text-black"
          onClick={desfazer}
        >
          Desfazer
        </Button>
      )}
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
        <h4 className="font-medium mb-2">Tarefas do Comercial</h4>
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
      <Button className="bg-white text-black" onClick={() => window.history.back()}>
        Voltar
      </Button>
    </div>
  );
}

export default AtendimentoDetalhes;
