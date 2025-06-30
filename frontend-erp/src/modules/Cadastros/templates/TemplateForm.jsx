import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button } from '../../Producao/components/ui/button';
import { fetchComAuth } from '../../../utils/fetchComAuth';

const FIELD_TYPES = [
  { value: 'short', label: 'Texto curto' },
  { value: 'long', label: 'Texto longo' },
  { value: 'date', label: 'Data' },
  { value: 'number', label: 'Número' },
  { value: 'document', label: 'Documento' },
  { value: 'table', label: 'Tabela' },
];

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
    default:
      return tipo;
  }
};

function TemplateForm() {
  const { tipo, id } = useParams();
  const navigate = useNavigate();
  const [form, setForm] = useState({ titulo: '', campos: [] });
  const [novoTipo, setNovoTipo] = useState('');

  useEffect(() => {
    if (id) {
      fetchComAuth(`/comercial/templates/${id}`)
        .then(d => {
          const t = d.template;
          if (t) setForm({ titulo: t.titulo, campos: t.campos || [] });
        })
        .catch(() => {});
    }
  }, [id]);

  const addCampo = () => {
    if (!novoTipo) return;
    const novo = { tipo: novoTipo, label: '', linhas: 1, colunas: 1 };
    setForm(prev => ({ ...prev, campos: [...prev.campos, novo] }));
    setNovoTipo('');
  };

  const updateCampo = (idx, campo, valor) => {
    setForm(prev => {
      const campos = prev.campos.map((c, i) => (i === idx ? { ...c, [campo]: valor } : c));
      return { ...prev, campos };
    });
  };

  const removerCampo = idx => {
    setForm(prev => ({ ...prev, campos: prev.campos.filter((_, i) => i !== idx) }));
  };

  const salvar = async () => {
    const body = { titulo: form.titulo, tipo, campos: form.campos };
    const url = id ? `/comercial/templates/${id}` : '/comercial/templates';
    const metodo = id ? 'PUT' : 'POST';
    await fetchComAuth(url, { method: metodo, body: JSON.stringify(body) });
    navigate('..');
  };

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">Template de {nomeTipo(tipo)}</h3>
      <label className="block">
        <span className="text-sm">Título do Template</span>
        <input className="input" value={form.titulo} onChange={e => setForm({ ...form, titulo: e.target.value })} />
      </label>
      <div className="space-y-2">
        {form.campos.map((c, idx) => (
          <div key={idx} className="border rounded p-2 space-y-1">
            <div className="flex gap-2 items-center">
              <input
                className="input flex-grow"
                placeholder="Descrição"
                value={c.label}
                onChange={e => updateCampo(idx, 'label', e.target.value)}
              />
              <select className="input" value={c.tipo} onChange={e => updateCampo(idx, 'tipo', e.target.value)}>
                {FIELD_TYPES.map(ft => (
                  <option key={ft.value} value={ft.value}>{ft.label}</option>
                ))}
              </select>
              <button type="button" className="text-red-600" onClick={() => removerCampo(idx)}>Remover</button>
            </div>
            {c.tipo === 'table' && (
              <div className="flex gap-2">
                <label className="block">
                  <span className="text-sm">Linhas</span>
                  <input type="number" className="input" value={c.linhas}
                    onChange={e => updateCampo(idx, 'linhas', e.target.value)} />
                </label>
                <label className="block">
                  <span className="text-sm">Colunas</span>
                  <input type="number" className="input" value={c.colunas}
                    onChange={e => updateCampo(idx, 'colunas', e.target.value)} />
                </label>
              </div>
            )}
            <button type="button" className="text-blue-600 underline" onClick={() => updateCampo(idx, 'auto', true)}>
              Carregamento automático
            </button>
          </div>
        ))}
      </div>
      <div className="flex items-end gap-2">
        <select className="input" value={novoTipo} onChange={e => setNovoTipo(e.target.value)}>
          <option value="">Adicionar campo</option>
          {FIELD_TYPES.map(ft => (
            <option key={ft.value} value={ft.value}>{ft.label}</option>
          ))}
        </select>
        <Button type="button" variant="secondary" onClick={addCampo}>Incluir</Button>
      </div>
      <div className="flex gap-2">
        <Button onClick={salvar}>Salvar</Button>
        <Button variant="secondary" onClick={() => navigate('..')}>Voltar</Button>
      </div>
    </div>
  );
}

export default TemplateForm;
