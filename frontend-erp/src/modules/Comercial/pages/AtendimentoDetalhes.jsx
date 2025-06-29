import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Button } from '../../Producao/components/ui/button';
import { fetchComAuth } from '../../../utils/fetchComAuth';

function AtendimentoDetalhes() {
  const { id } = useParams();
  const [atendimento, setAtendimento] = useState(null);
  const [tarefas, setTarefas] = useState([]);

  useEffect(() => {
    const carregar = async () => {
      try {
        const dados = await fetchComAuth(`/comercial/atendimentos/${id}`);
        setAtendimento(dados.atendimento);
        const t = await fetchComAuth(`/comercial/atendimentos/${id}/tarefas`);
        setTarefas(t.tarefas);
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
        <ul className="space-y-1">
          {tarefas.map(t => (
            <li key={t.id} className="flex items-center gap-2">
              <span className={t.concluida ? 'line-through' : ''}>{t.nome}</span>
            </li>
          ))}
        </ul>
      </div>
      <Button onClick={() => window.history.back()}>Voltar</Button>
    </div>
  );
}

export default AtendimentoDetalhes;
