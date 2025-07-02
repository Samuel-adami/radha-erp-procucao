import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { fetchComAuth } from '../../../utils/fetchComAuth';

const currency = v =>
  Number(v || 0).toLocaleString('pt-BR', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });

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
    const wClass = campo.largura === 'half' ? 'w-1/2 px-2' : 'w-full px-2';
    const posClass = campo.largura === 'half' && campo.halfAlign === 'right'
      ? 'ml-auto'
      : campo.largura === 'half' && campo.halfAlign === 'center'
      ? 'mx-auto'
      : '';
    const style = {
      textAlign: campo.textAlign || undefined,
      fontSize: campo.fontSize ? `${campo.fontSize}px` : undefined,
    };
    let content;
    if (campo.tipo === 'section') {
      return (
        <div key={idx} className="w-full font-bold pt-4" style={style}>
          {campo.label}
        </div>
      );
    }
    if (campo.tipo === 'separator') {
      return <div key={idx} className="w-full px-2 my-2" style={style}></div>;
    }
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
    } else if (campo.autoCampo === 'empresa.cabecalho') {
      content = (
        <div className="space-y-1">
          <div>{empresa.razaoSocial || 'Empresa LTDA'}</div>
          <div>{`CNPJ: ${empresa.cnpj || '00.000.000/0000-00'}`}</div>
          <div>{`${empresa.rua || 'Rua'}, ${empresa.numero || '0'}${empresa.complemento ? ' - ' + empresa.complemento : ''}`}</div>
          <div>{`${empresa.bairro || ''} - ${empresa.cidade || ''}/${empresa.estado || ''}`}</div>
          <div>{`CEP ${empresa.cep || ''}`}</div>
          <div>{`Contato ${empresa.telefone1 || ''}`}</div>
        </div>
      );
    } else if (campo.autoCampo === 'cliente.cabecalho_com_cpf') {
      const cli = {
        nome: 'Cliente',
        documento: '000.000.000-00',
        endereco: 'Rua',
        numero: '0',
        complemento: '',
        bairro: '',
        cidade: '',
        estado: '',
        cep: '',
        telefone1: '',
      };
      content = (
        <div className="space-y-1">
          <div>{cli.nome}</div>
          <div>{`CPF: ${cli.documento}`}</div>
          <div>{`${cli.endereco}, ${cli.numero}${cli.complemento ? ' - ' + cli.complemento : ''}`}</div>
          <div>{`${cli.bairro} - ${cli.cidade}/${cli.estado}`}</div>
          <div>{`CEP ${cli.cep}`}</div>
          <div>{`Contato ${cli.telefone1}`}</div>
        </div>
      );
    } else if (campo.autoCampo === 'cliente.cabecalho_sem_cpf') {
      const cli = {
        nome: 'Cliente',
        endereco: 'Rua',
        numero: '0',
        complemento: '',
        bairro: '',
        cidade: '',
        estado: '',
        cep: '',
        telefone1: '',
      };
      content = (
        <div className="space-y-1">
          <div>{cli.nome}</div>
          <div>{`${cli.endereco}, ${cli.numero}${cli.complemento ? ' - ' + cli.complemento : ''}`}</div>
          <div>{`${cli.bairro} - ${cli.cidade}/${cli.estado}`}</div>
          <div>{`CEP ${cli.cep}`}</div>
          <div>{`Contato ${cli.telefone1}`}</div>
        </div>
      );
    } else if (campo.tipo === 'titulo') {
      content = <h3 className="font-semibold">{campo.label}</h3>;
    } else if (campo.tipo === 'texto') {
      content = <div className="whitespace-pre-wrap">{campo.texto}</div>;
    } else if (campo.tipo === 'table') {
      content = (
        <table className="pdf-table text-sm">
          <thead>
            <tr>
              <th className="border px-1 text-center align-middle"></th>
              {Array.from({ length: campo.colunas || 0 }).map((_, i) => (
                <th key={i} className="border px-1 text-center align-middle">{campo.headersColunas?.[i] || ''}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {Array.from({ length: campo.linhas || 0 }).map((_, r) => (
              <tr key={r}>
                <th className="border px-1 text-center align-middle">{campo.headersLinhas?.[r] || ''}</th>
                {Array.from({ length: campo.colunas || 0 }).map((_, cIdx) => (
                  <td key={cIdx} className="border px-1 text-center align-middle">___</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      );
    } else if (campo.tipo === 'negociacao') {
      content = (
        <div className="text-sm">
          <table className="pdf-table" style={{ margin: '24px 0', width: '90%' }}>
            <tbody>
              <tr>
                <th className="text-left">Condição de Pagamento</th>
                <td className="border">___</td>
              </tr>
              <tr>
                <th className="text-left">Entrada (R$)</th>
                <td className="border">R$ {currency(0)}</td>
              </tr>
              <tr>
                <th className="text-left">Parcelas</th>
                <td className="border">1</td>
              </tr>
            </tbody>
          </table>
          <table className="pdf-table">
            <thead>
              <tr>
                <th className="border">Ambiente</th>
                <th className="border">Orçamento</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td className="border text-left">Projeto 1</td>
                <td className="border text-right">R$ {currency(0)}</td>
              </tr>
            </tbody>
          </table>
          <table className="pdf-table">
            <thead>
              <tr>
                <th className="border">Número</th>
                <th className="border">Valor</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td className="border text-center">1</td>
                <td className="border text-right">R$ {currency(0)}</td>
              </tr>
            </tbody>
          </table>
          <div className="text-right font-bold">Total: R$ {currency(0)}</div>
        </div>
      );
    } else if (campo.autoCampo === 'negociacao.tabela') {
      content = (
        <div className="text-sm">
          <table className="pdf-table" style={{ margin: '24px 0', width: '90%' }}>
            <tbody>
              <tr>
                <th className="text-left">Condição de Pagamento</th>
                <td className="border">___</td>
              </tr>
              <tr>
                <th className="text-left">Entrada (R$)</th>
                <td className="border">R$ {currency(0)}</td>
              </tr>
              <tr>
                <th className="text-left">Parcelas</th>
                <td className="border">1</td>
              </tr>
            </tbody>
          </table>
          <table className="pdf-table">
            <thead>
              <tr>
                <th className="border">Ambiente</th>
                <th className="border">Orçamento</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td className="border text-left">Projeto 1</td>
                <td className="border text-right">R$ {currency(0)}</td>
              </tr>
            </tbody>
          </table>
          <table className="pdf-table">
            <thead>
              <tr>
                <th className="border">Número</th>
                <th className="border">Valor</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td className="border text-center">1</td>
                <td className="border text-right">R$ {currency(0)}</td>
              </tr>
            </tbody>
          </table>
          <div className="text-right font-bold">Total: R$ {currency(0)}</div>
        </div>
      );
    } else if (campo.tipo === 'assinatura') {
      content = (
        <div className="space-y-1 text-sm text-center">
          <div>__________________________________</div>
          <div>Assinatura</div>
          <div>Nome do Cliente / Nome da Empresa</div>
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
      <div
        key={idx}
        className={`${wClass} ${posClass} flex items-center`.trim()}
        style={style}
      >
        {content}
      </div>
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
