import React from 'react';

interface Props {
  descricao: string;
  setDescricao: (v: string) => void;
  opcoesDescricao: string[];
}

const FiltroChapa: React.FC<Props> = ({ descricao, setDescricao, opcoesDescricao }) => {
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
    </div>
  );
};

export default FiltroChapa;
