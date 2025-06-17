import React, { useState } from "react";
import { Button } from "./ui/button";

const Apontamento = () => {
  const lotes = JSON.parse(localStorage.getItem("lotesProducao") || "[]");
  const [lote, setLote] = useState("");
  const [pacoteIndex, setPacoteIndex] = useState("");
  const [codigo, setCodigo] = useState("");
  const [apontados, setApontados] = useState([]);

  const pacotes = lote ? (lotes.find(l => l.nome === lote)?.pacotes || []) : [];
  const pacote = pacotes[parseInt(pacoteIndex)] || null;

  const registrarCodigo = (e) => {
    e.preventDefault();
    if (!pacote) return;
    const cod = codigo.trim();
    if (!cod) return;
    const peca = pacote.pecas.find(p => String(p.codigo_peca) === cod);
    if (peca) {
      if (!apontados.includes(peca.id)) {
        setApontados([...apontados, peca.id]);
      }
    } else {
      alert("Código não encontrado no pacote");
    }
    setCodigo("");
  };

  return (
    <div className="p-6">
      <h2 className="text-lg font-semibold mb-4">Apontamento de Peças</h2>
      <div className="flex flex-col sm:flex-row gap-2 mb-4">
        <select
          className="input sm:w-48"
          value={lote}
          onChange={e => { setLote(e.target.value); setPacoteIndex(""); setApontados([]); }}
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
            onChange={e => { setPacoteIndex(e.target.value); setApontados([]); }}
          >
            <option value="">Selecione o Pacote</option>
            {pacotes.map((p, i) => (
              <option key={i} value={i}>{p.nome_pacote || `Pacote ${i + 1}`}</option>
            ))}
          </select>
        )}
      </div>
      {pacote && (
        <>
          <form onSubmit={registrarCodigo} className="mb-4">
            <input
              className="input w-full sm:w-64"
              placeholder="Program1 / Código de Barras"
              value={codigo}
              onChange={e => setCodigo(e.target.value)}
              autoFocus
            />
          </form>
          <ul className="space-y-1 max-h-96 overflow-y-auto">
            {pacote.pecas.map(p => (
              <li
                key={p.id}
                className={`border rounded p-2 ${apontados.includes(p.id) ? 'bg-green-200' : ''}`}
              >
                <span className="font-mono mr-2">{p.codigo_peca}</span>
                {p.nome}
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
};

export default Apontamento;
