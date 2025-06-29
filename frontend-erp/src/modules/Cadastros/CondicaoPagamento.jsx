import React, { useState, useEffect, useRef } from 'react';
import * as XLSX from 'xlsx';
import { Button } from '../Producao/components/ui/button';
import { useNavigate, useParams } from 'react-router-dom';
import { fetchComAuth } from '../../utils/fetchComAuth';

const formatDecimal = v => {
  const num = parseFloat(v);
  if (isNaN(num)) return '';
  return num.toFixed(2);
};

const formatParcelas = parc => {
  const fmt = lst =>
    (lst || []).map(p => ({
      ...p,
      juros: p.juros === '' || p.juros === undefined ? '' : formatDecimal(p.juros),
      retencao:
        p.retencao === '' || p.retencao === undefined
          ? ''
          : formatDecimal(p.retencao),
    }));
  return { sem: fmt(parc?.sem), com: fmt(parc?.com) };
};

function CondicaoPagamento() {
  const navigate = useNavigate();
  const { id } = useParams();
  const initialForm = {
    nome: '',
    ativa: true,
    parcelas: { sem: [], com: [] },
  };
  const [form, setForm] = useState(initialForm);
  const [dirty, setDirty] = useState(false);

  useEffect(() => {
    if (id) {
      fetchComAuth(`/comercial/condicoes-pagamento/${id}`)
        .then(d => {
          const c = d.condicao;
          if (c) {
            setForm({
              nome: c.nome,
              ativa: !!c.ativa,
              parcelas: formatParcelas(c.parcelas || { sem: [], com: [] }),
            });
            setDirty(false);
          }
        })
        .catch(() => {});
    }
  }, [id]);

  const handle = campo => e => {
    const value = e.target.type === 'checkbox' ? e.target.checked : e.target.value;
    setForm(prev => ({ ...prev, [campo]: value }));
    setDirty(true);
  };

  const addParcela = tipo => {
    setForm(prev => {
      const lista = [...prev.parcelas[tipo]];
      lista.push({ numero: lista.length + 1, juros: '', retencao: '' });
      return { ...prev, parcelas: { ...prev.parcelas, [tipo]: lista } };
    });
    setDirty(true);
  };

  const updateParcela = (tipo, index, campo, valor) => {
    setForm(prev => {
      const lista = prev.parcelas[tipo].map((p, i) =>
        i === index ? { ...p, [campo]: valor } : p
      );
      return { ...prev, parcelas: { ...prev.parcelas, [tipo]: lista } };
    });
    setDirty(true);
  };

  const removeParcela = (tipo, index) => {
    setForm(prev => {
      const lista = prev.parcelas[tipo].filter((_, i) => i !== index);
      return { ...prev, parcelas: { ...prev.parcelas, [tipo]: lista } };
    });
    setDirty(true);
  };

  const fileRef = useRef();

  const importarExcel = e => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = evt => {
      const data = new Uint8Array(evt.target.result);
      const wb = XLSX.read(data, { type: 'array' });
      const sheet = wb.Sheets[wb.SheetNames[0]];
      const rows = XLSX.utils.sheet_to_json(sheet, { header: 1 });
      const parc = { sem: [], com: [] };
      rows.slice(1).forEach(r => {
        const [tipo, numero, juros, retencao] = r;
        if (tipo === 'sem' || tipo === 'com') {
          parc[tipo].push({
            numero: Number(numero) || 0,
            juros: formatDecimal(juros),
            retencao: formatDecimal(retencao),
          });
        }
      });
      setForm(prev => ({ ...prev, parcelas: formatParcelas(parc) }));
      setDirty(true);
    };
    reader.readAsArrayBuffer(file);
  };

  const abrirImport = () => fileRef.current?.click();

  const salvar = async () => {
    const totalParcelas = form.parcelas.sem.length + form.parcelas.com.length;
    const body = {
      nome: form.nome,
      numero_parcelas: totalParcelas,
      juros_parcela: 0,
      dias_vencimento: [],
      ativa: form.ativa ? 1 : 0,
      parcelas: form.parcelas,
    };
    const url = id ? `/comercial/condicoes-pagamento/${id}` : '/comercial/condicoes-pagamento';
    const metodo = id ? 'PUT' : 'POST';
    try {
      await fetchComAuth(url, { method: metodo, body: JSON.stringify(body) });
      alert('Condição salva');
      setDirty(false);
    } catch (err) {
      alert('Erro ao salvar: ' + err.message);
      throw err;
    }
  };

  const handleSubmit = async e => {
    e.preventDefault();
    try {
      await salvar();
      if (id) {
        navigate('../lista');
      } else {
        setForm(initialForm);
      }
    } catch (err) {
      console.error('Falha ao salvar condição', err);
    }
  };

  const cancelar = () => {
    setForm(initialForm);
    setDirty(false);
  };

  const sair = () => {
    if (dirty) {
      if (window.confirm('Deseja salvar as informações adicionadas?')) {
        salvar();
      }
    }
    navigate('..');
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 items-end">
        <label className="block">
          <span className="text-sm">Descrição</span>
          <input className="input" value={form.nome} onChange={handle('nome')} />
        </label>
        <label className="inline-flex items-center gap-1">
          <input type="checkbox" checked={form.ativa} onChange={handle('ativa')} />
          Ativa
        </label>
      </div>
      <div className="space-y-4">
          {['sem', 'com'].map(tipo => (
            <div key={tipo}>
              <div className="flex justify-between items-center mb-1">
                <h4 className="font-semibold">
                  {tipo === 'sem' ? 'Sem Entrada' : 'Com Entrada'}
                </h4>
                <div className="flex gap-2">
                  <Button type="button" variant="secondary" onClick={() => addParcela(tipo)}>
                    Adicionar Parcela
                  </Button>
                  <Button type="button" variant="secondary" onClick={abrirImport}>
                    Importar Excel
                  </Button>
                </div>
              </div>
              <table className="w-full text-sm border">
              <thead>
                <tr className="bg-gray-100">
                  <th className="border px-2">Nº Parcela</th>
                  <th className="border px-2">Juros % mês</th>
                  <th className="border px-2">Retenção %</th>
                  <th className="border px-2"></th>
                </tr>
              </thead>
              <tbody>
                {form.parcelas[tipo].map((p, idx) => (
                  <tr key={idx}>
                    <td className="border px-2">
                      <input
                        type="number"
                        className="input w-full"
                        value={p.numero}
                        onChange={e => updateParcela(tipo, idx, 'numero', e.target.value)}
                      />
                    </td>
                    <td className="border px-2">
                      <input
                        type="number"
                        step="0.01"
                        className="input w-full"
                        value={p.juros}
                        onChange={e => updateParcela(tipo, idx, 'juros', e.target.value)}
                        onBlur={e => updateParcela(tipo, idx, 'juros', formatDecimal(e.target.value))}
                      />
                    </td>
                    <td className="border px-2">
                      <input
                        type="number"
                        step="0.01"
                        className="input w-full"
                        value={p.retencao}
                        onChange={e => updateParcela(tipo, idx, 'retencao', e.target.value)}
                        onBlur={e => updateParcela(tipo, idx, 'retencao', formatDecimal(e.target.value))}
                      />
                    </td>
                    <td className="border px-2 text-center">
                      <button type="button" className="text-red-600" onClick={() => removeParcela(tipo, idx)}>
                        Remover
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ))}
      </div>
      <input type="file" ref={fileRef} onChange={importarExcel} className="hidden" />
        <div className="flex gap-2">
          <Button type="submit">Salvar</Button>
          <Button type="button" variant="secondary" onClick={cancelar}>
            Cancelar
          </Button>
          <Button type="button" variant="secondary" onClick={sair}>
            Sair
          </Button>
      </div>
    </form>
  );
}

export default CondicaoPagamento;
