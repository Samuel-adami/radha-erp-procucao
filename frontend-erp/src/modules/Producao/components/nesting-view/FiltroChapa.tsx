import React from 'react';

interface Props {
  descricao: string;
  setDescricao: (v: string) => void;
  opcoesDescricao: string[];
  codigo: string;
  setCodigo: (v: string) => void;
  busca: string;
  setBusca: (v: string) => void;
}

const FiltroChapa: React.FC<Props> = ({ descricao, setDescricao, opcoesDescricao, codigo, setCodigo, busca, setBusca }) => {
  return (
    <div className="flex flex-wrap gap-2 mb-4">
      <select
        value={descricao}
        onChange={(e) => setDescricao(e.target.value)}
        className="input"
      >
        {opcoesDescricao.map((op) => (
          <option key={op} value={op}>
            {op}
          </option>
        ))}
      </select>
      <input
        type="text"
        placeholder="Código"
        value={codigo}
        onChange={(e) => setCodigo(e.target.value)}
        className="input"
      />
      <input
        type="text"
        placeholder="Busca rápida"
        value={busca}
        onChange={(e) => setBusca(e.target.value)}
        className="input flex-1"
      />
    </div>
  );
};

export default FiltroChapa;
