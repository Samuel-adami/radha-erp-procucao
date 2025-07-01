import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { DndContext, closestCenter } from '@dnd-kit/core';
import {
  SortableContext,
  useSortable,
  arrayMove,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { Button } from '../../Producao/components/ui/button';
import { fetchComAuth } from '../../../utils/fetchComAuth';

// Os templates antigos utilizam um array "campos" com objetos
// {tipo, label, largura, ...}. O TemplateBuilder continua usando
// exatamente o mesmo formato, apenas adicionando os novos tipos
// 'titulo', 'texto' e 'section'. Portanto nenhuma migração é necessária.
// Basta ler e salvar os dados como já feito anteriormente.

const FIELD_TYPES = [
  { value: 'short', label: 'Texto curto' },
  { value: 'long', label: 'Texto longo' },
  { value: 'date', label: 'Data' },
  { value: 'number', label: 'Número' },
  { value: 'document', label: 'Documento' },
  { value: 'table', label: 'Tabela' },
  { value: 'assinatura', label: 'Assinatura digital' },
  { value: 'negociacao', label: 'Negociação' },
  { value: 'titulo', label: 'Título' },
  { value: 'texto', label: 'Texto' },
  { value: 'section', label: 'Seção/Agrupador' },
];

function SortableItem({ id, children }) {
  const { attributes, listeners, setNodeRef, transform, transition } = useSortable({ id });
  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };
  return (
    <div ref={setNodeRef} style={style} {...attributes} {...listeners} className="mb-2 cursor-move">
      {children}
    </div>
  );
}

function TemplateBuilder() {
  const { tipo, id } = useParams();
  const navigate = useNavigate();
  const [form, setForm] = useState({ titulo: '', campos: [] });
  const [selected, setSelected] = useState(null);

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

  const addCampo = tipoCampo => {
    const novo = { tipo: tipoCampo, label: '', largura: 'full' };
    setForm(prev => ({ ...prev, campos: [...prev.campos, novo] }));
  };

  const atualizarCampo = (idx, prop, valor) => {
    setForm(prev => {
      const campos = prev.campos.map((c, i) => (i === idx ? { ...c, [prop]: valor } : c));
      return { ...prev, campos };
    });
  };

  const moverCampo = event => {
    const { active, over } = event;
    if (active.id !== over?.id) {
      setForm(prev => {
        const oldIndex = prev.campos.findIndex((_, i) => i.toString() === active.id);
        const newIndex = prev.campos.findIndex((_, i) => i.toString() === over?.id);
        const campos = arrayMove(prev.campos, oldIndex, newIndex);
        return { ...prev, campos };
      });
    }
  };

  const salvar = async () => {
    const body = { titulo: form.titulo, tipo, campos: form.campos };
    const url = id ? `/comercial/templates/${id}` : '/comercial/templates';
    const metodo = id ? 'PUT' : 'POST';
    await fetchComAuth(url, { method: metodo, body: JSON.stringify(body) });
    navigate('..');
  };

  const renderPreview = campo => {
    if (campo.tipo === 'section') {
      return <div className="col-span-2 font-bold pt-4">{campo.label}</div>;
    }
    const wClass = campo.largura === 'half' ? 'w-1/2 px-2' : 'w-full';
    return (
      <div className={wClass + ' mb-2'}>
        {campo.tipo === 'titulo' && <h3 className="text-lg font-semibold">{campo.label}</h3>}
        {campo.tipo === 'texto' && <div className="whitespace-pre-wrap text-sm">{campo.texto}</div>}
        {['short', 'long', 'date', 'number', 'document'].includes(campo.tipo) && (
          <div>{campo.label || '_____'}:</div>
        )}
        {campo.tipo === 'table' && <div className="border p-2 text-sm">Tabela</div>}
        {campo.tipo === 'assinatura' && <div className="text-sm">Assinatura digital</div>}
        {campo.tipo === 'negociacao' && <div className="text-sm">Negociação</div>}
      </div>
    );
  };

  return (
    <div className="flex gap-4">
      <div className="w-48 space-y-2 border-r pr-2">
        {FIELD_TYPES.map(ft => (
          <button
            key={ft.value}
            className="w-full text-left p-1 border rounded hover:bg-accent"
            type="button"
            onClick={() => addCampo(ft.value)}
          >
            {ft.label}
          </button>
        ))}
      </div>
      <div className="flex-1 space-y-4">
        <label className="block">
          <span className="text-sm">Título do Template</span>
          <input
            className="input w-full"
            value={form.titulo}
            onChange={e => setForm({ ...form, titulo: e.target.value })}
          />
        </label>
        <DndContext collisionDetection={closestCenter} onDragEnd={moverCampo}>
          <SortableContext items={form.campos.map((_, i) => i.toString())} strategy={verticalListSortingStrategy}>
            {form.campos.map((c, idx) => (
              <SortableItem key={idx} id={idx.toString()}>
                <div
                  className="border p-2 bg-muted cursor-pointer"
                  onClick={() => setSelected(idx)}
                >
                  {c.label || c.tipo}
                </div>
              </SortableItem>
            ))}
          </SortableContext>
        </DndContext>
        {selected !== null && form.campos[selected] && (
          <div className="border p-2 bg-background rounded">
            <h4 className="font-semibold mb-2">Editar Campo</h4>
            <div className="space-y-2">
              <input
                className="input w-full"
                placeholder="Descrição"
                value={form.campos[selected].label || ''}
                onChange={e => atualizarCampo(selected, 'label', e.target.value)}
              />
              <select
                className="input w-full"
                value={form.campos[selected].largura}
                onChange={e => atualizarCampo(selected, 'largura', e.target.value)}
              >
                <option value="full">Linha inteira</option>
                <option value="half">Meia largura</option>
              </select>
              {form.campos[selected].tipo === 'texto' && (
                <textarea
                  className="input w-full"
                  rows="3"
                  value={form.campos[selected].texto || ''}
                  onChange={e => atualizarCampo(selected, 'texto', e.target.value)}
                />
              )}
              <Button
                variant="destructive"
                onClick={() => {
                  setForm(prev => ({ ...prev, campos: prev.campos.filter((_, i) => i !== selected) }));
                  setSelected(null);
                }}
              >
                Remover
              </Button>
            </div>
          </div>
        )}
        <div className="flex gap-2">
          <Button onClick={salvar}>Salvar</Button>
          <Button variant="secondary" onClick={() => navigate('..')}>
            Voltar
          </Button>
        </div>
      </div>
      <div className="w-1/2 border-l pl-2">
        <div className="p-2 bg-white border rounded" style={{ width: '210mm', minHeight: '297mm' }}>
          <h2 className="text-center font-bold mb-4">{form.titulo}</h2>
          <div className="flex flex-wrap">
            {form.campos.map((c, i) => (
              <React.Fragment key={i}>{renderPreview(c)}</React.Fragment>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default TemplateBuilder;
