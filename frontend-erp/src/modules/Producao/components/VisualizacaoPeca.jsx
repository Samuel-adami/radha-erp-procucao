import React from "react";

const VisualizacaoPeca = ({ comprimento, largura, operacoes = [] }) => {
  if (!comprimento || !largura) return <p>Dimensões inválidas.</p>;

  const C = parseFloat(comprimento);
  const L = parseFloat(largura);

  const viewWidth = 540;
  const viewHeight = 320;
  const paddingX = 25;

  const escala = Math.min((viewWidth - 2 * paddingX - 40) / C, (viewHeight - 40) / L);
  const larguraSVG = C * escala;
  const alturaSVG = L * escala;

  const totalWidth = larguraSVG + 40;
  const offsetX = (viewWidth - totalWidth) / 2 + 30;
  const offsetY = (viewHeight - alturaSVG) / 2;

  if (typeof operacoes === "string") {
    try {
      const parsed = JSON.parse(operacoes);
      if (Array.isArray(parsed)) operacoes = parsed;
      else return <p>Sem operações visuais.</p>;
    } catch {
      return <pre style={{ fontSize: "12px" }}>{operacoes}</pre>;
    }
  }

  let raios = { topLeft: 0, topRight: 0, bottomRight: 0, bottomLeft: 0 };
  operacoes = operacoes.filter(op => {
    if (op.tipo === 'Raio') {
      const valor = parseFloat(op.raio || 0) * escala;
      if (op.pos === 'L1') {
        if (op.subPos === 'inferior') raios.bottomLeft = valor;
        else raios.topLeft = valor;
      } else if (op.pos === 'C2' || op.pos === 'L3') {
        if (op.subPos === 'inferior') raios.bottomRight = valor;
        else raios.topRight = valor;
      } else if (op.pos === 'C1') {
        switch(op.subPos) {
          case 'T1': raios.bottomLeft = valor; break;
          case 'T2': raios.topLeft = valor; break;
          case 'T3': raios.topRight = valor; break;
          case 'T4':
          default: raios.bottomRight = valor; break;
        }
      }
      return false;
    }
    return true;
  });

  const pathD = () => {
    const rTL = raios.topLeft || 0;
    const rTR = raios.topRight || 0;
    const rBR = raios.bottomRight || 0;
    const rBL = raios.bottomLeft || 0;
    let d = `M ${offsetX + rTL} ${offsetY}`;
    d += ` H ${offsetX + larguraSVG - rTR}`;
    if (rTR) d += ` A ${rTR} ${rTR} 0 0 1 ${offsetX + larguraSVG} ${offsetY + rTR}`;
    d += ` V ${offsetY + alturaSVG - rBR}`;
    if (rBR) d += ` A ${rBR} ${rBR} 0 0 1 ${offsetX + larguraSVG - rBR} ${offsetY + alturaSVG}`;
    d += ` H ${offsetX + rBL}`;
    if (rBL) d += ` A ${rBL} ${rBL} 0 0 1 ${offsetX} ${offsetY + alturaSVG - rBL}`;
    d += ` V ${offsetY + rTL}`;
    if (rTL) d += ` A ${rTL} ${rTL} 0 0 1 ${offsetX + rTL} ${offsetY}`;
    d += ' Z';
    return d;
  };

  return (
    <svg width={viewWidth} height={viewHeight} viewBox={`0 0 ${viewWidth} ${viewHeight}`}>
      {/* Peça principal */}
      { (raios.topLeft || raios.topRight || raios.bottomRight || raios.bottomLeft) ? (
        <path d={pathD()} fill="none" stroke="#000" strokeWidth={2} />
      ) : (
        <rect
          x={offsetX}
          y={offsetY}
          width={larguraSVG}
          height={alturaSVG}
          fill="none"
          stroke="#000"
          strokeWidth={2}
        />
      ) }

      {/* Face 1 com novo nome */}
      <rect
        x={offsetX - 30}
        y={offsetY}
        width={20}
        height={alturaSVG}
        fill="none"
        stroke="#888"
        strokeDasharray="4"
      />
      <text x={offsetX - 25} y={offsetY - 8} fontSize="12" fill="black">L1</text>

      {/* Face 3 com novo nome */}
      <rect
        x={offsetX + larguraSVG + 10}
        y={offsetY}
        width={20}
        height={alturaSVG}
        fill="none"
        stroke="#888"
        strokeDasharray="4"
      />
      <text x={offsetX + larguraSVG + 12} y={offsetY - 8} fontSize="12" fill="black">L3</text>

      {operacoes.map((op, i) => {
        const tipo = op.tipo?.toLowerCase() || "";
        const cor = tipo === "furo" ? "black" : ["blue", "green", "orange", "purple"][i % 4];

        // --- LÓGICA DE DESENHO ATUALIZADA COM NOVOS NOMES DE FACE ---
        if ((tipo === "círculo" || tipo === "furo") && (op.face === "Topo (L1)" || op.face === "Topo (L3)")) {
          const r = (parseFloat(op.diametro || 0) / 2) * escala;
          const cy = offsetY + (L - parseFloat(op.y || 0)) * escala;
          const cx = op.face === "Topo (L1)"
            ? offsetX - 20
            : offsetX + larguraSVG + 20;
          return (
            <circle
              key={i}
              cx={cx}
              cy={cy}
              r={r}
              fill="none"
              stroke={cor}
              strokeWidth={2}
            />
          );
        }

        if (tipo === "retângulo" || tipo === "retangulo" || tipo === "linha") {
          const x = offsetX + parseFloat(op.x || 0) * escala;
          const y = offsetY + (L - parseFloat(op.y || 0) - parseFloat(op.largura || 0)) * escala;
          const w = parseFloat(op.comprimento || 0) * escala;
          const h = parseFloat(op.largura || 0) * escala;
          return (
            <rect
              key={i}
              x={x}
              y={y}
              width={w}
              height={h}
              fill={op.estrategia === "Desbaste" ? cor : "none"}
              stroke={cor}
              strokeWidth={2}
            />
          );
        }

        if (tipo === "círculo" || tipo === "furo") {
          const r = (parseFloat(op.diametro || 0) / 2) * escala;
          const cx = offsetX + parseFloat(op.x || 0) * escala;
          const cy = offsetY + (L - parseFloat(op.y || 0)) * escala;
          return (
            <circle
              key={i}
              cx={cx}
              cy={cy}
              r={r}
              fill={op.estrategia === "Desbaste" ? cor : "none"}
              stroke={cor}
              strokeWidth={2}
            />
          );
        }

        return null;
      })}
    </svg>
  );
};

export default VisualizacaoPeca;
