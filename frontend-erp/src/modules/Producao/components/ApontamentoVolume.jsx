import React, { useState, useEffect } from "react";
import JsBarcode from "jsbarcode";
import FiltroPacote from "./FiltroPacote";

const ApontamentoVolume = () => {
  const [lote, setLote] = useState("");
  const [pacoteIndex, setPacoteIndex] = useState("");
  const [volumes, setVolumes] = useState([]);
  const [codigo, setCodigo] = useState("");

  const lotes = JSON.parse(localStorage.getItem("lotesProducao") || "[]");
  const pacotes = lote ? (lotes.find(l => l.nome === lote)?.pacotes || []) : [];
  const pacote = pacotes[parseInt(pacoteIndex)] || null;

  useEffect(() => {
    if (pacote) {
      setVolumes(pacote.volumes || []);
    } else {
      setVolumes([]);
    }
    setCodigo("");
  }, [pacoteIndex, lote]);

  const registrarCodigo = (e) => {
    e.preventDefault();
    const cod = codigo.trim();
    if (!cod) return;
    const vol = volumes.find(v => v.barcode === cod);
    if (vol) {
      imprimirEtiqueta(vol);
    } else {
      alert("Volume não encontrado");
    }
    setCodigo("");
  };

  const imprimirEtiqueta = (volume) => {
    const printWindow = window.open('', '_blank', 'width=400,height=400');
    if (!printWindow) return;
    printWindow.document.write(`<html><body style="font-family:sans-serif;margin:0;padding:8px;">`);
    printWindow.document.write(`<h3>Volume ${volume.numero}</h3>`);
    if (pacote?.nome_pacote) {
      printWindow.document.write(`<div>${pacote.nome_pacote}</div>`);
    }
    printWindow.document.write('<ul style="margin:8px 0; padding-left:16px; font-size:12px">');
    volume.pecas.forEach(p => {
      const nome = p.nome || p.descricao || '';
      printWindow.document.write(`<li>${String(p.id).padStart(6,'0')} - ${nome}</li>`);
    });
    printWindow.document.write('</ul>');
    printWindow.document.write(`<svg id="barcode"></svg>`);
    printWindow.document.write('</body></html>');
    printWindow.document.close();
    JsBarcode(printWindow.document.getElementById('barcode'), volume.barcode, { format: 'CODE128', displayValue: true });
    printWindow.focus();
    printWindow.print();
    printWindow.close();
  };


  return (
    <div className="p-6">
      <h2 className="text-lg font-semibold mb-4">Apontamento de Volumes</h2>
      <FiltroPacote
        lotes={lotes}
        lote={lote}
        onChangeLote={(v) => { setLote(v); setPacoteIndex(""); }}
        pacotes={pacotes}
        pacoteIndex={pacoteIndex}
        onChangePacote={(v) => setPacoteIndex(v)}
      />
      {pacote && (
        <>
          <form onSubmit={registrarCodigo} className="mb-4">
            <input
              className="input w-full sm:w-64"
              placeholder="Código de barras do volume"
              value={codigo}
              onChange={e => setCodigo(e.target.value)}
              autoFocus
            />
          </form>
          <ul className="space-y-2">
            {volumes.map(v => (
              <li key={v.numero} className="border rounded p-2">
                <div className="font-semibold flex justify-between items-center">
                <span>Volume {v.numero} - {v.barcode}</span>
                <button
                  onClick={() => imprimirEtiqueta(v)}
                  className="text-sm text-blue-600 underline"
                >
                  Imprimir
                </button>
              </div>
              <ul className="text-sm list-disc ml-4">
                {v.pecas.map(pc => (
                  <li key={pc.id}>{String(pc.id).padStart(6,'0')} - {pc.nome || pc.descricao}</li>
                ))}
              </ul>
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
};

export default ApontamentoVolume;
