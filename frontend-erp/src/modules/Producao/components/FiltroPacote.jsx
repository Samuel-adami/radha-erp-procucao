import React from "react";

const FiltroPacote = ({ lotes, lote, onChangeLote, pacotes, pacoteIndex, onChangePacote }) => {
  return (
    <div className="flex flex-col sm:flex-row gap-2 mb-4">
      <select
        className="input sm:w-48"
        value={lote}
        onChange={e => onChangeLote(e.target.value)}
      >
        <option value="">Selecione o Lote</option>
        {lotes.map(l => (
          <option key={l.nome} value={l.nome}>{l.nome}</option>
        ))}
      </select>
      {pacotes.length > 0 && (
        <select
          className="input sm:w-48"
          value={pacoteIndex}
          onChange={e => onChangePacote(e.target.value)}
        >
          <option value="">Selecione o Pacote</option>
          {pacotes.map((p, i) => (
            <option key={i} value={i}>{p.nome_pacote || `Pacote ${i + 1}`}</option>
          ))}
        </select>
      )}
    </div>
  );
};

export default FiltroPacote;
