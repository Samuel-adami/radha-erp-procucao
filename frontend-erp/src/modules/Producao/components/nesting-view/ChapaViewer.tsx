import React from 'react';

export interface Operacao {
  id: number;
  nome: string;
  tipo: string;
  ferramenta?: string;
  layer?: string;
  x: number;
  y: number;
  largura: number;
  altura: number;
  coords?: [number, number][];
  cliente?: string;
  ambiente?: string;
}

export interface Chapa {
  id: number;
  codigo: string;
  descricao: string;
  largura: number;
  altura: number;
  temVeio?: boolean;
  operacoes: Operacao[];
}

interface Props {
  chapa: Chapa;
  onSelect: (op: Operacao) => void;
  destaqueId?: number | null;
  width?: number;
}

const cores: Record<string, string> = {
  Peca: '#60a5fa',
  Sobra: '#a3e635',
};

const ChapaViewer: React.FC<Props> = ({
  chapa,
  onSelect,
  destaqueId,
  width = 500,
}) => {
  const svgWidth = width;
  const escala = svgWidth / chapa.largura;
  const alturaSvg = chapa.altura * escala;
  // As linhas de veio devem acompanhar a primeira medida da chapa
  // (comprimento), que é representada pelo eixo horizontal no viewer.
  const isHorizontal = true;
  let sobraCount = 0;

  return (
    <svg width={svgWidth} height={alturaSvg} className="border bg-white">
      <rect width={svgWidth} height={alturaSvg} fill="#f9fafb" stroke="#000" />
      {chapa.temVeio &&
        Array.from({ length: 8 }).map((_, i) => {
          if (isHorizontal) {
            const y = ((i + 1) * chapa.altura) / 9 * escala;
            return (
              <line
                key={`veio-h-${i}`}
                x1={0}
                y1={y}
                x2={svgWidth}
                y2={y}
                stroke="#bbb"
                strokeDasharray="4 4"
              />
            );
          }
          const x = ((i + 1) * chapa.largura) / 9 * escala;
          return (
            <line
              key={`veio-v-${i}`}
              x1={x}
              y1={0}
              x2={x}
              y2={alturaSvg}
              stroke="#bbb"
              strokeDasharray="4 4"
            />
          );
        })}
      {chapa.operacoes.map((op) => {
        const x = op.x * escala;
        const y = op.y * escala;
        const w = op.largura * escala;
        const h = op.altura * escala;
        const cor = cores[op.tipo] || '#fca5a5';
        const stroke = destaqueId === op.id ? '#e11d48' : '#000';
        return (
          <g key={op.id} onClick={() => onSelect(op)} className="cursor-pointer">
            {op.tipo === 'Sobra' && op.coords && op.coords.length > 0 ? (
              <polygon
                points={op.coords
                  .map(([px, py]) => `${px * escala},${py * escala}`)
                  .join(' ')}
                fill={cor}
                opacity={0.3}
                stroke={stroke}
                strokeWidth={1}
              />
            ) : (
              <rect
                x={x}
                y={y}
                width={w}
                height={h}
                fill={cor}
                opacity={op.tipo === 'Sobra' ? 0.3 : 0.6}
                stroke={stroke}
                strokeWidth={1}
              />
            )}
            {op.tipo === 'Peca' && (
              <text
                x={x + w / 2}
                y={y + h / 2}
                textAnchor="middle"
                dominantBaseline="middle"
                fontSize={12}
                fill="#000"
              >
                {`${Math.round(op.largura)} x ${Math.round(op.altura)}`}
              </text>
            )}
            {op.tipo === 'Sobra' && (
              <text
                x={x + w / 2}
                y={y + h / 2}
                textAnchor="middle"
                dominantBaseline="middle"
                fontSize={12}
                fill="#000"
              >
                {`S${String(++sobraCount).padStart(2, '0')}`}
              </text>
            )}
          </g>
        );
      })}
    </svg>
  );
};

export default ChapaViewer;
