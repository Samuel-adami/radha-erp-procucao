import React, { useState } from 'react';
import { Button } from './ui/button';

const CAMPOS_DXT = [
  'PartName',
  'Length',
  'Width',
  'Thickness',
  'Material',
  'Program1',
  'Filename',
  'Client',
  'Project',
  'Comment'
];

const SCALE = 3; // pixels per mm

const EtiquetaDesigner = ({ layout = [], onChange, largura = 50, altura = 30 }) => {
  const [campo, setCampo] = useState('');
  const [arrastando, setArrastando] = useState(null);

  const adicionar = () => {
    if (!campo) return;
    const novo = { id: Date.now(), campo, x: 0, y: 0 };
    onChange([...layout, novo]);
    setCampo('');
  };

  const iniciarArraste = (id) => (e) => {
    const rect = e.target.getBoundingClientRect();
    setArrastando({
      id,
      offsetX: e.clientX - rect.left,
      offsetY: e.clientY - rect.top
    });
  };

  const mover = (e) => {
    if (!arrastando) return;
    const container = e.currentTarget.getBoundingClientRect();
    const x = (e.clientX - container.left - arrastando.offsetX) / SCALE;
    const y = (e.clientY - container.top - arrastando.offsetY) / SCALE;
    onChange(
      layout.map((it) => (it.id === arrastando.id ? { ...it, x, y } : it))
    );
  };

  const parar = () => setArrastando(null);

  const remover = (id) => {
    onChange(layout.filter((it) => it.id !== id));
  };

  const larguraPx = parseFloat(largura || 50) * SCALE;
  const alturaPx = parseFloat(altura || 30) * SCALE;

  const disponiveis = CAMPOS_DXT.filter((c) => !layout.some((l) => l.campo === c));

  return (
    <div>
      <div className="flex items-end gap-2 mb-2">
        <select className="input" value={campo} onChange={(e) => setCampo(e.target.value)}>
          <option value="">Adicionar informação...</option>
          {disponiveis.map((c) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
        <Button size="sm" onClick={adicionar}>Adicionar</Button>
      </div>
      <div
        className="border relative bg-white"
        style={{ width: larguraPx, height: alturaPx }}
        onMouseMove={mover}
        onMouseUp={parar}
      >
        {layout.map((it) => (
          <div
            key={it.id}
            onMouseDown={iniciarArraste(it.id)}
            className="absolute text-xs cursor-move bg-white px-1 border"
            style={{ left: it.x * SCALE, top: it.y * SCALE }}
          >
            {it.campo}
            <button onClick={() => remover(it.id)} className="ml-1 text-red-600">x</button>
          </div>
        ))}
      </div>
    </div>
  );
};

export default EtiquetaDesigner;
