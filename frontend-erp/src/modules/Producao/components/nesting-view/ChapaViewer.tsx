import React from 'react';

export interface Operacao {
  id: number;
  nome: string;
  tipo: string;
  ferramenta?: string;
  x: number;
  y: number;
  largura: number;
  altura: number;
}

export interface Chapa {
  id: number;
  codigo: string;
  descricao: string;
  largura: number;
  altura: number;
  operacoes: Operacao[];
}

interface Props {
  chapa: Chapa;
  onSelect: (op: Operacao) => void;
  destaqueId?: number | null;
}

const cores: Record<string, string> = {
  Peca: '#60a5fa',
  Sobra: '#a3e635',
};

const ChapaViewer: React.FC<Props> = ({ chapa, onSelect, destaqueId }) => {
  const escala = 300 / chapa.largura;
  const alturaSvg = chapa.altura * escala;

  return (
    <svg width={300} height={alturaSvg} className="border bg-white">
      <rect width={300} height={alturaSvg} fill="#f9fafb" stroke="#000" />
      {chapa.operacoes.map((op) => {
        const x = op.x * escala;
        const y = op.y * escala;
        const w = op.largura * escala;
        const h = op.altura * escala;
        const cor = cores[op.tipo] || '#fca5a5';
        const stroke = destaqueId === op.id ? '#e11d48' : '#000';
        return (
          <rect
            key={op.id}
            x={x}
            y={y}
            width={w}
            height={h}
            fill={cor}
            opacity={op.tipo === 'Sobra' ? 0.3 : 0.6}
            stroke={stroke}
            strokeWidth={1}
            onClick={() => onSelect(op)}
            className="cursor-pointer"
          />
        );
      })}
    </svg>
  );
};

export default ChapaViewer;
