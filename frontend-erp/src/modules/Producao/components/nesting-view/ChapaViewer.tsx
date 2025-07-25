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
  rotacao?: number;
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
  // As linhas de veio são sempre exibidas na horizontal,
  // seguindo o comprimento da chapa no viewer.
  let sobraCount = 0;

  return (
    <svg width={svgWidth} height={alturaSvg} className="border bg-white">
      <rect width={svgWidth} height={alturaSvg} fill="#f9fafb" stroke="#000" />
      {chapa.temVeio &&
        Array.from({ length: 8 }).map((_, i) => {
          const y = ((i + 1) * chapa.altura) / 9 * escala;
          const vy = alturaSvg - y;
          return (
            <line
              key={`veio-h-${i}`}
              x1={0}
              y1={vy}
              x2={svgWidth}
              y2={vy}
              stroke="#bbb"
              strokeDasharray="4 4"
            />
          );
        })}
      {chapa.operacoes.map((op) => {

        const x = op.x * escala;



        const y = (chapa.altura - op.y - op.altura) * escala;
        const w = op.largura * escala;
        const h = op.altura * escala;
        const cor = cores[op.tipo] || '#fca5a5';
        const stroke = destaqueId === op.id ? '#e11d48' : '#000';
        const transform = op.rotacao
          ? `rotate(${op.rotacao} ${x + w / 2} ${y + h / 2})`
          : undefined;
        return (
          <g
            key={op.id}
            onClick={() => onSelect(op)}
            className="cursor-pointer"
            {...(transform ? { transform } : {})}
          >
            {op.tipo === 'Sobra' && op.coords && op.coords.length > 0 ? (
              <polygon
                points={op.coords

                  .map(([px, py]) => `${px * escala},${(chapa.altura - py) * escala}`)

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
