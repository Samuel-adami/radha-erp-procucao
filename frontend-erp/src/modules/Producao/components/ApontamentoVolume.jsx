import React, { useState, useEffect } from "react";
import JsBarcode from "jsbarcode";
import FiltroPacote from "./FiltroPacote";
import { fetchComAuth } from "../../../utils/fetchComAuth";

const ApontamentoVolume = () => {
  const [lotes, setLotes] = useState([]);
  const [lote, setLote] = useState("");
  const [pacoteIndex, setPacoteIndex] = useState("");
  const [volumes, setVolumes] = useState([]);
  const [codigo, setCodigo] = useState("");
  const [pacotes, setPacotes] = useState([]);
  const pacote = pacotes[parseInt(pacoteIndex)] || null;

  useEffect(() => {
    fetchComAuth("/listar-lotes")
      .then((d) => {
        const lista = (d?.lotes || []).map((p) => ({
          pasta: p,
          nome: p.split(/[/\\\\]/).pop(),
        }));
        setLotes(lista);
      })
      .catch(() => setLotes([]));
  }, []);

  useEffect(() => {
    if (!lote) {
      setPacotes([]);
      return;
    }
    const obj = lotes.find((l) => l.nome === lote);
    if (!obj) return;
    fetchComAuth(`/carregar-lote-final?pasta=${encodeURIComponent(obj.pasta)}`)
      .then((d) => setPacotes(d?.pacotes || []))
      .catch(() => setPacotes([]));
  }, [lote, lotes]);

  useEffect(() => {
    if (pacoteIndex === "" || !lote) {
      setVolumes([]);
      setCodigo("");
      return;
    }
    const pacoteAtual = pacotes[parseInt(pacoteIndex)];
    const nomePacote = pacoteAtual?.nome_pacote || `Pacote ${parseInt(pacoteIndex) + 1}`;
    fetchComAuth(
      `/apontamentos?lote=${encodeURIComponent(lote)}&pacote=${encodeURIComponent(nomePacote)}`
    )
      .then((d) => setVolumes(d?.volumes || []))
      .catch(() => setVolumes([]));
    setCodigo("");
  }, [pacoteIndex, lote, pacotes]);

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
    if (pacote?.nome_pacote) {
      printWindow.document.write(`<div>${pacote.nome_pacote}</div>`);
    }
    printWindow.document.write(`<h3>Volume ${volume.numero}</h3>`);
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
          <div className="font-semibold mb-2">{pacote.nome_pacote}</div>
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
