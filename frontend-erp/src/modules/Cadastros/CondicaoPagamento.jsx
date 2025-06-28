import React, { useState, useEffect } from 'react';
import { Button } from '../Producao/components/ui/button';
import { useNavigate, useParams } from 'react-router-dom';
import { fetchComAuth } from '../../utils/fetchComAuth';
import * as XLSX from 'xlsx';

function CondicaoPagamento() {
  const navigate = useNavigate();
  const { id } = useParams();
  const initialForm = {
    descricao: '',
    ativa: true,
    semEntrada: [],
    comEntrada: [],
  };
  const [form, setForm] = useState(initialForm);

  useEffect(() => {
    if (id) {
      fetchComAuth(`/comercial/condicoes-pagamento/${id}`)
        .then(d => {
          const c = d.condicao;
          if (c) {
            setForm(prev => ({
              ...prev,
              descricao: c.nome,
              ativa: !!c.ativa,
              semEntrada: c.semEntrada || [],
              comEntrada: c.comEntrada || [],
            }));
          }
        })
        .catch(() => {});
    }
  }, [id]);

  const handle = campo => e => {
    const value = e.target.type === 'checkbox' ? e.target.checked : e.target.value;
    setForm(prev => ({ ...prev, [campo]: value }));
  };

  const adicionarParcela = tipo => {
    setForm(prev => ({
      ...prev,
g1b3co-codex/adicionar-tela-de-cadastro-com-tabela-e-importação
      [tipo]: [
        ...prev[tipo],
        {
          numero:
            tipo === 'comEntrada'
              ? `1+${prev[tipo].length + 1}`
              : prev[tipo].length + 1,
          juros: '',
          retencao: '',
        },
      ],
    }));
  };

  const atualizarParcela = (tipo, index, campo, valor) => {
    setForm(prev => {
      const lista = [...prev[tipo]];
      lista[index] = { ...lista[index], [campo]: valor };
      return { ...prev, [tipo]: lista };
    });
  };

  const removerParcela = (tipo, index) => {
    setForm(prev => ({
      ...prev,
      [tipo]: prev[tipo].filter((_, i) => i !== index),
    }));
  };

  const importarPlanilha = (e, tipo) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = evt => {
      const data = new Uint8Array(evt.target.result);
      const wb = XLSX.read(data, { type: 'array' });
      const sheet = wb.Sheets[wb.SheetNames[0]];
      const rows = XLSX.utils.sheet_to_json(sheet, { header: 1 });
      const parsed = rows.slice(1).map(r => ({
        numero: r[0],
        juros: r[1],
        retencao: r[2],
      }));
      setForm(prev => ({ ...prev, [tipo]: parsed }));
    };
    reader.readAsArrayBuffer(file);
  };

  const salvar = async () => {
    const body = {
      descricao: form.descricao,
      ativa: form.ativa ? 1 : 0,
      semEntrada: form.semEntrada,
      comEntrada: form.comEntrada,
    };
    const url = id ? `/comercial/condicoes-pagamento/${id}` : '/comercial/condicoes-pagamento';
    const metodo = id ? 'PUT' : 'POST';
    await fetchComAuth(url, { method: metodo, body: JSON.stringify(body) });
  };

  const handleSubmit = async e => {
    e.preventDefault();
    await salvar();
    if (id) {
      navigate('../lista');
    } else {
      setForm(initialForm);
    }
  };

  const cancelar = () => {
    setForm(initialForm);
  };

  const sair = () => {
    navigate('..');
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="flex items-center gap-4">
        <label className="flex-1 block">
          <span className="text-sm">Descrição</span>
          <input className="input w-full" value={form.descricao} onChange={handle('descricao')} />
        </label>
        <label className="inline-flex items-center gap-1">
          <input type="checkbox" checked={form.ativa} onChange={handle('ativa')} />
          Ativa
        </label>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <h4 className="font-semibold mb-2">Sem Entrada</h4>
          <table className="min-w-full text-sm border">
            <thead>
              <tr className="bg-gray-100">
                <th className="border px-2">Parcela</th>
                <th className="border px-2">Juros (%)</th>
                <th className="border px-2">Retenção (%)</th>
                <th className="border px-2"></th>
              </tr>
            </thead>
            <tbody>
              {form.semEntrada.map((p, idx) => (
                <tr key={idx}>
                  <td className="border px-2">
                    <input
                      type="number"
                      className="input w-full"
                      value={p.numero}
                      onChange={e => atualizarParcela('semEntrada', idx, 'numero', e.target.value)}
                    />
                  </td>
                  <td className="border px-2">
                    <input
                      type="number"
                      className="input w-full"
                      value={p.juros}
                      onChange={e => atualizarParcela('semEntrada', idx, 'juros', e.target.value)}
                    />
                  </td>
                  <td className="border px-2">
                    <input
                      type="number"
                      className="input w-full"
                      value={p.retencao}
                      onChange={e => atualizarParcela('semEntrada', idx, 'retencao', e.target.value)}
                    />
                  </td>
                  <td className="border px-2 text-center">
                    <button type="button" className="text-red-600 hover:underline" onClick={() => removerParcela('semEntrada', idx)}>
                      Remover
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="flex items-center gap-2 mt-2">
            <Button type="button" variant="secondary" onClick={() => adicionarParcela('semEntrada')}>
              Adicionar Parcela
            </Button>
            <input type="file" accept=".xlsx" onChange={e => importarPlanilha(e, 'semEntrada')} />
          </div>
        </div>

        <div>
          <h4 className="font-semibold mb-2">Com Entrada</h4>
          <table className="min-w-full text-sm border">
            <thead>
              <tr className="bg-gray-100">
                <th className="border px-2">Parcela</th>
                <th className="border px-2">Juros (%)</th>
                <th className="border px-2">Retenção (%)</th>
                <th className="border px-2"></th>
              </tr>
            </thead>
            <tbody>
              {form.comEntrada.map((p, idx) => (
                <tr key={idx}>
                  <td className="border px-2">
                    <input
                      type="number"
                      className="input w-full"
                      value={p.numero}
                      onChange={e => atualizarParcela('comEntrada', idx, 'numero', e.target.value)}
                    />
                  </td>
                  <td className="border px-2">
                    <input
                      type="number"
                      className="input w-full"
                      value={p.juros}
                      onChange={e => atualizarParcela('comEntrada', idx, 'juros', e.target.value)}
                    />
                  </td>
                  <td className="border px-2">
                    <input
                      type="number"
                      className="input w-full"
                      value={p.retencao}
                      onChange={e => atualizarParcela('comEntrada', idx, 'retencao', e.target.value)}
                    />
                  </td>
                  <td className="border px-2 text-center">
                    <button type="button" className="text-red-600 hover:underline" onClick={() => removerParcela('comEntrada', idx)}>
                      Remover
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="flex items-center gap-2 mt-2">
            <Button type="button" variant="secondary" onClick={() => adicionarParcela('comEntrada')}>
              Adicionar Parcela
            </Button>
            <input type="file" accept=".xlsx" onChange={e => importarPlanilha(e, 'comEntrada')} />
          </div>
        </div>
      </div>

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
