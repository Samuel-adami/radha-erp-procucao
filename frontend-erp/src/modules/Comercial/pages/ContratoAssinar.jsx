import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button } from '../../Producao/components/ui/button';
import SignaturePad from '../components/SignaturePad';
import { fetchComAuth } from '../../../utils/fetchComAuth';

function ContratoAssinar() {
  const { id, tarefaId } = useParams();
  const navigate = useNavigate();
  const [assinatura, setAssinatura] = useState('');

  const salvar = async () => {
    const usuario = JSON.parse(localStorage.getItem('usuario') || '{}');
    const resp = await fetchComAuth('/comercial/contratos/assinar', {
      method: 'POST',
      body: JSON.stringify({ assinatura, usuario: usuario.username }),
    });
    const blob = await resp.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'contrato_assinado.pdf';
    a.click();
    const dados = {
      data: new Date().toISOString(),
      usuario: usuario.username,
    };
    await fetchComAuth(`/comercial/atendimentos/${id}/tarefas/${tarefaId}`, {
      method: 'PUT',
      body: JSON.stringify({ dados: JSON.stringify(dados), concluida: true }),
    });
    navigate(`/comercial/${id}`);
  };

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">Assinatura do Contrato</h3>
      <SignaturePad onChange={setAssinatura} />
      <Button onClick={salvar}>Assinar</Button>
    </div>
  );
}

export default ContratoAssinar;
