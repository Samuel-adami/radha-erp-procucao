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

  const footerText = () => {
    switch (template.tipo) {
      case 'contrato':
        return `Contrato ${new Date().getFullYear()}/0001`;
      case 'orcamento':
        return 'OR AT-0001 001';
      case 'pedido':
        return 'Pedido AT-0001';
      case 'romaneio':
        return 'Romaneio Nº 00001';
      default:
        return '';
    }
  };

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
    } else if (campo.tipo === 'table') {
      content = (
        <table className="w-full text-sm">
          <thead>
            <tr>
              <th className="border px-1"></th>
              {Array.from({ length: campo.colunas || 0 }).map((_, i) => (
                <th key={i} className="border px-1">{campo.headersColunas?.[i] || ''}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {Array.from({ length: campo.linhas || 0 }).map((_, r) => (
              <tr key={r}>
                <th className="border px-1">{campo.headersLinhas?.[r] || ''}</th>
                {Array.from({ length: campo.colunas || 0 }).map((_, cIdx) => (
                  <td key={cIdx} className="border px-1">___</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      );
    } else if (campo.tipo === 'negociacao') {
      content = (
        <div className="space-y-1 text-sm">
          <div>Descrição da condição de pagamento</div>
          <table className="w-full">
            <thead>
              <tr>
                <th className="border px-1">Projeto</th>
                <th className="border px-1">Valor</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td className="border px-1">Projeto 1</td>
                <td className="border px-1">R$ 0,00</td>
              </tr>
            </tbody>
          </table>
          <table className="w-full">
            <thead>
              <tr>
                <th className="border px-1">Número</th>
                <th className="border px-1">Valor</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td className="border px-1">1</td>
                <td className="border px-1">R$ 0,00</td>
              </tr>
            </tbody>
          </table>
          <div>Total: R$ 0,00</div>
        </div>
      );
    } else {
      content = (
        <div className="whitespace-pre-wrap">
          {campo.label ? `${campo.label}: ___` : '___'}
        </div>
      );
    }
    return (
      <div key={idx} className={wClass}>{content}</div>
    );
  };

  return (
    <div className="p-4 flex justify-center">
      <div className="border bg-white p-4 flex flex-col justify-between" style={{ width: '210mm', minHeight: '297mm' }}>
        <div className="flex justify-between items-center mb-4">
          {empresa.logo && <img src={empresa.logo} alt="Logo" className="h-12" />}
          <div className="text-sm">{empresa.slogan}</div>
        </div>
        <div className="flex-1">
          <h2 className="text-center font-bold mb-4">{template.titulo}</h2>
          <div className="flex flex-wrap">
            {template.campos?.map(renderField)}
          </div>
        </div>
        <div className="flex justify-between items-center mt-4 text-sm">
          <div>Página 1 de 1</div>
          <div className="mx-auto">{footerText()}</div>
        </div>
      </div>
    </div>
  );
}

export default TemplatePreview;
