import React, { useEffect, useState, useRef } from 'react';
import { Link, useParams } from 'react-router-dom';
import { Button } from '../../Producao/components/ui/button';
import { fetchComAuth } from '../../../utils/fetchComAuth';

const nomeTipo = tipo => {
  switch (tipo) {
    case 'orcamento':
      return 'Orçamento';
    case 'pedido':
      return 'Pedido';
    case 'contrato':
      return 'Contrato';
    case 'romaneio':
      return 'Romaneio de Entrega';
    case 'memorial':
      return 'Memorial Descritivo';
    case 'negociacao':
      return 'Negociação';
    default:
      return tipo;
  }
};

function ListaTemplates() {
  const { tipo } = useParams();
  const [lista, setLista] = useState([]);
  const fileRef = useRef();

  const carregar = async () => {
    try {
      const dados = await fetchComAuth(`/comercial/templates?tipo=${tipo}`);
      setLista(dados.templates || []);
    } catch (err) {
      console.error('Erro ao carregar templates', err);
    }
  };

  useEffect(() => { carregar(); }, [tipo]);

  const excluir = async id => {
    if (!window.confirm('Excluir este template?')) return;
    await fetchComAuth(`/comercial/templates/${id}`, { method: 'DELETE' });
    carregar();
  };

  const selecionarArquivo = () => {
    fileRef.current?.click();
  };

  const enviarArquivo = async e => {
    const file = e.target.files?.[0];
    if (!file) return;
    const form = new FormData();
    form.append('file', file);
    form.append('tipo', tipo);
    form.append('titulo', file.name);
    await fetchComAuth('/comercial/templates/upload', { method: 'POST', body: form });
    e.target.value = '';
    carregar();
  };

  return (
    <div className="space-y-2">
      <div className="flex justify-between items-center gap-2">
        <h3 className="text-lg font-semibold">Templates de {nomeTipo(tipo)}</h3>
        <Button asChild><Link to="novo">Novo Template</Link></Button>
        <Button variant="secondary" onClick={selecionarArquivo}>Importar arquivo</Button>
        <input ref={fileRef} type="file" accept=".docx,.pdf" className="hidden" onChange={enviarArquivo} />
      </div>
      <ul className="space-y-1">
        {lista.map(t => (
          <li key={t.id} className="flex justify-between items-center border rounded p-2">
            <span>{t.titulo}</span>
            <div className="space-x-2">
              <Link className="text-blue-600 hover:underline" to={`editar/${t.id}`}>Editar</Link>
              <Link className="text-blue-600 hover:underline" to={`preview/${t.id}`}>Visualizar</Link>
              <button className="text-red-600 hover:underline" onClick={() => excluir(t.id)}>Excluir</button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default ListaTemplates;
