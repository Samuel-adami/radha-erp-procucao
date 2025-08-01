import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { DndContext, closestCenter } from '@dnd-kit/core';
import { SortableContext, useSortable, arrayMove, verticalListSortingStrategy } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import AutoFieldSelect from './AutoFieldSelect';
import { Button } from '../../Producao/components/ui/button';
import { fetchComAuth } from '../../../utils/fetchComAuth';

const FIELD_TYPES = [
  { value: 'short', label: 'Texto curto' },
  { value: 'long', label: 'Texto longo' },
  { value: 'number', label: 'Número' },
  { value: 'date', label: 'Data' },
  { value: 'table', label: 'Tabela' },
  { value: 'assinatura', label: 'Assinatura digital' },
  { value: 'separator', label: 'Separador' },
];

function SortableItem({ id, children }) {
  const { attributes, listeners, setNodeRef, transform, transition } = useSortable({ id });
  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };
  return (
    <div ref={setNodeRef} style={style} {...attributes} {...listeners} className="cursor-move">
      {children}
    </div>
  );
}

function FieldModal({ field, onChange, onSave, onClose }) {
  if (!field) return null;
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white p-4 rounded space-y-2 w-80">
        <h3 className="font-semibold text-lg">Configurar campo</h3>
        <input
          className="input w-full"
          placeholder="Nome do campo"
          value={field.label || ''}
          onChange={e => onChange({ ...field, label: e.target.value })}
        />
        {['short','long','number','date'].includes(field.tipo) && (
          <input
            className="input w-full"
            placeholder="Placeholder"
            value={field.placeholder || ''}
            onChange={e => onChange({ ...field, placeholder: e.target.value })}
          />
        )}
        {field.tipo === 'table' && (
          <div className="flex gap-2">
            <input
              type="number"
              className="input"
              placeholder="Linhas"
              value={field.linhas || 1}
              onChange={e => onChange({ ...field, linhas: e.target.value })}
            />
            <input
              type="number"
              className="input"
              placeholder="Colunas"
              value={field.colunas || 1}
              onChange={e => onChange({ ...field, colunas: e.target.value })}
            />
          </div>
        )}
        <select
          className="input w-full"
          value={field.largura || 'full'}
          onChange={e => onChange({ ...field, largura: e.target.value })}
        >
          <option value="full">Linha inteira</option>
          {field.autoCampo !== 'negociacao.tabela' && (
            <option value="half">Meia página</option>
          )}
        </select>
        {field.largura === 'half' && (
          <select
            className="input w-full"
            value={field.halfAlign || 'left'}
            onChange={e => onChange({ ...field, halfAlign: e.target.value })}
          >
            <option value="left">À esquerda</option>
            <option value="center">Centralizado</option>
            <option value="right">À direita</option>
          </select>
        )}
        <div>
          <label className="text-sm block mb-1">Vincular a dado do ERP</label>
          <AutoFieldSelect value={field.autoCampo} onChange={v => onChange({ ...field, autoCampo: v })} />
        </div>
        <div className="flex gap-2 justify-end pt-2">
          <Button size="sm" onClick={() => onSave(field)}>Salvar</Button>
          <Button size="sm" variant="secondary" onClick={onClose}>Cancelar</Button>
        </div>
      </div>
    </div>
  );
}

function VisualTemplateBuilder() {
  const { tipo, id } = useParams();
  const navigate = useNavigate();
  const [titulo, setTitulo] = useState('');
  const [campos, setCampos] = useState([]);
  const [arquivoUrl, setArquivoUrl] = useState('');
  const fileRef = useRef();
  const [editing, setEditing] = useState(null); // { field, index }

  useEffect(() => {
    if (id) {
      fetchComAuth(`/comercial/templates/${id}`)
        .then(d => {
          const t = d.template;
          if (t) {
            setTitulo(t.titulo);
            setCampos(t.campos || []);
            setArquivoUrl(t.arquivo_url || '');
          }
        })
        .catch(() => {});
    }
  }, [id]);

  const addCampo = tipoCampo => {
    const novo = { tipo: tipoCampo, largura: 'full' };
    setEditing({ field: novo, index: campos.length });
  };

  const salvarCampo = field => {
    setCampos(prev => {
      const arr = [...prev];
      if (editing.index < prev.length) arr[editing.index] = field; else arr.push(field);
      return arr;
    });
    setEditing(null);
  };

  const removerCampo = idx => {
    setCampos(prev => prev.filter((_, i) => i !== idx));
  };

  const moverCampo = event => {
    const { active, over } = event;
    if (active.id !== over.id) {
      setCampos(prev => {
        const oldIndex = prev.findIndex((_, i) => i.toString() === active.id);
        const newIndex = prev.findIndex((_, i) => i.toString() === over.id);
        return arrayMove(prev, oldIndex, newIndex);
      });
    }
  };

  const selecionarArquivo = () => {
    fileRef.current?.click();
  };

  const enviarArquivo = async e => {
    const file = e.target.files?.[0];
    if (!file || !id) return;
    const form = new FormData();
    form.append('file', file);
    const resp = await fetchComAuth(`/comercial/templates/${id}/upload`, {
      method: 'POST',
      body: form,
    });
    setArquivoUrl(resp.arquivo_url || '');
    e.target.value = '';
  };

  const salvarTemplate = async () => {
    const body = { titulo, tipo, campos };
    const url = id ? `/comercial/templates/${id}` : '/comercial/templates';
    const metodo = id ? 'PUT' : 'POST';
    await fetchComAuth(url, { method: metodo, body: JSON.stringify(body) });
    navigate('..');
  };

  return (
    <div className="flex gap-4">
      <div className="w-48 space-y-2 border-r pr-2 overflow-y-auto" style={{ maxHeight: '90vh' }}>
        <h4 className="font-semibold">Campos</h4>
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
        <input
          className="input w-full"
          placeholder="Título do Template"
          value={titulo}
          onChange={e => setTitulo(e.target.value)}
        />
        <DndContext collisionDetection={closestCenter} onDragEnd={moverCampo}>
          <SortableContext items={campos.map((_, i) => i.toString())} strategy={verticalListSortingStrategy}>
            {campos.map((c, idx) => (
              <SortableItem key={idx} id={idx.toString()}>
                <div className="border p-2 bg-muted flex justify-between items-center">
                  <div
                    className="flex-1 cursor-pointer"
                    onDoubleClick={() => setEditing({ field: c, index: idx })}
                  >
                    {c.label || c.tipo}
                  </div>
                  <button
                    type="button"
                    className="text-red-600 ml-2"
                    onPointerDown={e => e.stopPropagation()}
                    onMouseDown={e => e.stopPropagation()}
                    onClick={e => {
                      e.preventDefault();
                      e.stopPropagation();
                      removerCampo(idx);
                    }}
                  >
                    Remover
                  </button>
                </div>
              </SortableItem>
            ))}
          </SortableContext>
        </DndContext>
        <div className="flex gap-2">
          <Button onClick={salvarTemplate}>Salvar</Button>
          <Button variant="secondary" onClick={() => navigate('..')}>Voltar</Button>
          {id && (
            <>
              <Button variant="secondary" onClick={selecionarArquivo}>Atualizar arquivo</Button>
              <input ref={fileRef} type="file" accept=".docx,.pdf" className="hidden" onChange={enviarArquivo} />
            </>
          )}
        </div>
      </div>
      <div className="w-1/2 border-l pl-2">
        {arquivoUrl && (
          <p className="text-sm mb-2">
            Arquivo atual:{' '}
            <a className="text-blue-600 underline" href={arquivoUrl} target="_blank" rel="noopener noreferrer">
              baixar
            </a>
          </p>
        )}
        <div className="p-4 bg-white border rounded" style={{ width: '210mm', minHeight: '297mm' }}>
          <h2 className="text-center font-bold text-xl mb-4">{titulo || 'Título do Template'}</h2>
          <div className="grid grid-cols-3 gap-4">
            {campos.map((c, i) => {
              const colClass = c.largura === 'half' ? 'col-span-2' : 'col-span-3';
              const posClass = c.largura === 'half' && c.halfAlign === 'right'
                ? 'ml-auto'
                : c.largura === 'half' && c.halfAlign === 'center'
                ? 'mx-auto'
                : '';
              return (
                <div
                  key={i}
                  className={`${colClass} ${posClass}`.trim()}
                  style={{ textAlign: c.textAlign }}
                >
                  {c.label || c.tipo}
                </div>
              );
            })}
          </div>
        </div>
      </div>
      {editing && (
        <FieldModal
          field={editing.field}
          onChange={f => setEditing({ ...editing, field: f })}
          onSave={salvarCampo}
          onClose={() => setEditing(null)}
        />
      )}
    </div>
  );
}

export default VisualTemplateBuilder;
