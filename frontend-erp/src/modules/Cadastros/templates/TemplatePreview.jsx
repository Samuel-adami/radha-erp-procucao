import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { fetchComAuth } from '../../../utils/fetchComAuth';

function TemplatePreview() {
  const { id } = useParams();
  const [template, setTemplate] = useState(null);

  useEffect(() => {
    fetchComAuth(`/comercial/templates/${id}`)
      .then(d => setTemplate(d.template))
      .catch(() => {});
  }, [id]);

  if (!template) return <div>Carregando...</div>;

  const empresa = JSON.parse(localStorage.getItem('empresa') || '{}');

  const renderField = (campo, idx) => {
    const wClass = campo.largura === 'half' ? 'w-1/2 px-2' : 'w-full';
    let content;
    if (campo.autoCampo === 'empresa.dados_completos') {
      content = (
        <div className="space-y-1">
          <div>{empresa.nomeFantasia || 'Empresa LTDA'}</div>
          <div>{(empresa.cnpj || '00.000.000/0000-00') + ' / ' + (empresa.inscricaoEstadual || 'IE')}</div>
          <div>{`${empresa.rua || 'Rua'}, ${empresa.numero || '123'} - ${empresa.bairro || ''}`}</div>
          <div>{`${empresa.cidade || ''} - ${empresa.estado || ''}`}</div>
          <div>{empresa.telefone1 || ''}</div>
        </div>
      );
    } else {
      content = <div className="whitespace-pre-wrap">[{campo.label}]</div>;
    }
    return (
      <div key={idx} className={wClass}>{content}</div>
    );
  };

  return (
    <div className="p-4 flex justify-center">
      <div className="border bg-white p-4" style={{ width: '210mm', minHeight: '297mm' }}>
        <h2 className="text-center font-bold mb-4">{template.titulo}</h2>
        <div className="flex flex-wrap">
          {template.campos?.map(renderField)}
        </div>
      </div>
    </div>
  );
}

export default TemplatePreview;
