import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button } from '../../Producao/components/ui/button';
import { fetchComAuth } from '../../../utils/fetchComAuth';
import AutoFieldSelect from './AutoFieldSelect';

const FIELD_TYPES = [
  { value: 'short', label: 'Texto curto' },
  { value: 'long', label: 'Texto longo' },
  { value: 'date', label: 'Data' },
  { value: 'number', label: 'Número' },
  { value: 'document', label: 'Documento' },
  { value: 'table', label: 'Tabela' },
  { value: 'assinatura', label: 'Assinatura digital' },
  { value: 'negociacao', label: 'Negociação' },
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
    case 'negociacao':
      return 'Negociação';
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
          if (t) {
            const campos = (t.campos || []).map(c => ({ largura: 'full', ...c }));
            setForm({ titulo: t.titulo, campos });
          }
        })
        .catch(() => {});
    }
  }, [id]);

  const addCampo = () => {
    if (!novoTipo) return;
    const novo = { tipo: novoTipo, label: '', linhas: 1, colunas: 1, largura: 'full' };
    setForm(prev => ({ ...prev, campos: [...prev.campos, novo] }));
    setNovoTipo('');
  };

  const updateCampo = (idx, campo, valor) => {
    setForm(prev => {
      const campos = prev.campos.map((c, i) => {
        if (i !== idx) return c;
        const novo = { ...c, [campo]: valor };
        if (campo === 'linhas') {
          const n = parseInt(valor) || 0;
          novo.headersLinhas = Array.from({ length: n }, (_, i2) => c.headersLinhas?.[i2] || '');
          novo.celulas = Array.from({ length: n }, (_, i2) => {
            const cols = parseInt(novo.colunas) || 0;
            return Array.from({ length: cols }, (_, j2) => c.celulas?.[i2]?.[j2] || { autoCampo: '' });
          });
        }
        if (campo === 'colunas') {
          const n = parseInt(valor) || 0;
          novo.headersColunas = Array.from({ length: n }, (_, j2) => c.headersColunas?.[j2] || '');
          novo.celulas = Array.from({ length: parseInt(novo.linhas) || 0 }, (_, i2) => {
            return Array.from({ length: n }, (_, j2) => c.celulas?.[i2]?.[j2] || { autoCampo: '' });
          });
        }
        return novo;
      });
      return { ...prev, campos };
    });
  };

  const removerCampo = idx => {
    setForm(prev => ({ ...prev, campos: prev.campos.filter((_, i) => i !== idx) }));
  };

  const moverCampo = (idx, dir) => {
    setForm(prev => {
      const campos = [...prev.campos];
      const novo = idx + dir;
      if (novo < 0 || novo >= campos.length) return prev;
      const [item] = campos.splice(idx, 1);
      campos.splice(novo, 0, item);
      return { ...prev, campos };
    });
  };

  const toggleAuto = idx => {
    setForm(prev => {
      const campos = prev.campos.map((c, i) => (i === idx ? { ...c, showAuto: !c.showAuto } : c));
      return { ...prev, campos };
    });
  };

  const setAutoCampo = (idx, valor) => {
    setForm(prev => {
      const campos = prev.campos.map((c, i) => (i === idx ? { ...c, autoCampo: valor, showAuto: false } : c));
      return { ...prev, campos };
    });
  };

  const setHeader = (idx, tipo, pos, valor) => {
    setForm(prev => {
      const campos = prev.campos.map((c, i) => {
        if (i !== idx) return c;
        const novo = { ...c };
        if (tipo === 'linha') {
          const arr = novo.headersLinhas ? [...novo.headersLinhas] : Array.from({ length: novo.linhas || 0 }, () => '');
          arr[pos] = valor;
          novo.headersLinhas = arr;
        } else {
          const arr = novo.headersColunas ? [...novo.headersColunas] : Array.from({ length: novo.colunas || 0 }, () => '');
          arr[pos] = valor;
          novo.headersColunas = arr;
        }
        return novo;
      });
      return { ...prev, campos };
    });
  };

  const setCellAuto = (idx, r, cIdx, valor) => {
    setForm(prev => {
      const campos = prev.campos.map((c, i) => {
        if (i !== idx) return c;
        const novo = { ...c };
        const rows = novo.celulas ? novo.celulas.map(row => [...row]) : [];
        while (rows.length < novo.linhas) rows.push(Array.from({ length: novo.colunas || 0 }, () => ({ autoCampo: '' })));
        rows[r] = rows[r] || Array.from({ length: novo.colunas || 0 }, () => ({ autoCampo: '' }));
        while (rows[r].length < novo.colunas) rows[r].push({ autoCampo: '' });
        rows[r][cIdx] = { autoCampo: valor };
        novo.celulas = rows;
        return novo;
      });
      return { ...prev, campos };
    });
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
              <select className="input" value={c.largura || 'full'} onChange={e => updateCampo(idx, 'largura', e.target.value)}>
                <option value="full">Linha inteira</option>
                {c.autoCampo !== 'negociacao.tabela' && (
                  <option value="half">Meia largura</option>
                )}
              </select>
              <button type="button" className="text-xl" onClick={() => moverCampo(idx, -1)}>&uarr;</button>
              <button type="button" className="text-xl" onClick={() => moverCampo(idx, 1)}>&darr;</button>
              <button type="button" className="text-red-600" onClick={() => removerCampo(idx)}>Remover</button>
            </div>
            {c.tipo === 'table' && (
              <>
                <div className="flex gap-2">
                  <label className="block">
                    <span className="text-sm">Linhas</span>
                    <input
                      type="number"
                      className="input"
                      value={c.linhas}
                      onChange={e => updateCampo(idx, 'linhas', e.target.value)}
                    />
                  </label>
                  <label className="block">
                    <span className="text-sm">Colunas</span>
                    <input
                      type="number"
                      className="input"
                      value={c.colunas}
                      onChange={e => updateCampo(idx, 'colunas', e.target.value)}
                    />
                  </label>
                </div>
                <div className="overflow-auto">
                  <table className="text-sm mt-2">
                    <thead>
                      <tr>
                        <th className="border p-1"></th>
                        {Array.from({ length: c.colunas || 0 }).map((_, j2) => (
                          <th key={j2} className="border p-1">
                            <input
                              className="input"
                              value={c.headersColunas?.[j2] || ''}
                              onChange={e => setHeader(idx, 'coluna', j2, e.target.value)}
                            />
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {Array.from({ length: c.linhas || 0 }).map((_, r2) => (
                        <tr key={r2}>
                          <th className="border p-1">
                            <input
                              className="input"
                              value={c.headersLinhas?.[r2] || ''}
                              onChange={e => setHeader(idx, 'linha', r2, e.target.value)}
                            />
                          </th>
                          {Array.from({ length: c.colunas || 0 }).map((_, c2) => (
                            <td key={c2} className="border p-1">
                              <AutoFieldSelect
                                value={c.celulas?.[r2]?.[c2]?.autoCampo || ''}
                                onChange={v => setCellAuto(idx, r2, c2, v)}
                              />
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            )}
            {c.tipo === 'negociacao' && (
              <div className="text-sm text-gray-600">Tabela da negociação será exibida neste local.</div>
            )}
            {c.tipo === 'assinatura' && (
              <div className="text-sm text-gray-600">Área para captura da assinatura digital.</div>
            )}
            {c.tipo !== 'table' && c.tipo !== 'negociacao' && c.tipo !== 'assinatura' && (
              <>
                <button type="button" className="text-blue-600 underline" onClick={() => toggleAuto(idx)}>
                  Carregamento automático
                </button>
                {c.showAuto && (
                  <AutoFieldSelect value={c.autoCampo} onChange={v => setAutoCampo(idx, v)} />
                )}
              </>
            )}
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
