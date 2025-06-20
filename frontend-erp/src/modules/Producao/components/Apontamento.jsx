import React, { useState } from "react";
import { Button } from "./ui/button";
import FiltroPacote from "./FiltroPacote";

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
    const peca = pacote.pecas.find(p => String(p.id).padStart(6,'0') === cod);
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
      <FiltroPacote
        lotes={lotes}
        lote={lote}
        onChangeLote={(v) => { setLote(v); setPacoteIndex(""); setApontados([]); }}
        pacotes={pacotes}
        pacoteIndex={pacoteIndex}
        onChangePacote={(v) => { setPacoteIndex(v); setApontados([]); }}
      />
      {pacote && (
        <>
          <form onSubmit={registrarCodigo} className="mb-4">
            <input
              className="input w-full sm:w-64"
              placeholder="ID da peça (6 dígitos)"
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
                <span className="font-mono mr-2">{String(p.id).padStart(6,'0')}</span>
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
