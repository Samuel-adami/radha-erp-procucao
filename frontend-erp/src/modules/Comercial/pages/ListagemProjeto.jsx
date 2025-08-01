import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { fetchComAuth } from '../../../utils/fetchComAuth';


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
  const [error, setError] = useState('');

  // Redireciona para a versão HTML do orçamento no backend
  useEffect(() => {
    const redirectHtml = async () => {
      try {
        const t = await fetchComAuth(`/comercial/atendimentos/${id}/tarefas`);
        const orc = t.tarefas.find(tt => String(tt.id) === String(tarefaId));
        let dados = typeof orc.dados === 'string' ? JSON.parse(orc.dados) : orc.dados || {};
        const projetos = dados.projetos || {};
        const chave = Object.keys(projetos).find(k => normalize(k) === normalize(ambiente));
        const info = chave ? projetos[chave] : projetos[ambiente];
        if (!info?.cabecalho?.cd_projeto) {
          throw new Error('Código do projeto não encontrado para redirecionamento');
        }
        window.location.href = `${import.meta.env.VITE_GATEWAY_URL}/comercial/${info.cabecalho.cd_projeto}/projeto3d/html`;
      } catch (err) {
        console.error('Erro ao redirecionar para HTML do orçamento', err);
        setError('Não foi possível abrir a versão HTML: ' + err.message);
      }
    };
    redirectHtml();
  }, [id, tarefaId, ambiente]);

  if (error) {
    return <div className="text-red-600">{error}</div>;
  }
  return null;
}
