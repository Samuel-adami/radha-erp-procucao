import React, { useState, useEffect } from "react";
import JsBarcode from "jsbarcode";
import FiltroPacote from "./FiltroPacote";

const CODE_FECHA_VOLUME = "999999";

const ApontamentoVolume = () => {
  const [lote, setLote] = useState("");
  const [pacoteIndex, setPacoteIndex] = useState("");
  const [codigo, setCodigo] = useState("");
  const [apontados, setApontados] = useState([]);
  const [volumes, setVolumes] = useState([]);

  const lotes = JSON.parse(localStorage.getItem("lotesProducao") || "[]");
  const pacotes = lote ? (lotes.find(l => l.nome === lote)?.pacotes || []) : [];
  const pacote = pacotes[parseInt(pacoteIndex)] || null;
  const itensPacote = pacote ? [...(pacote.pecas || []), ...(pacote.ferragens || [])] : [];

  useEffect(() => {
    if (pacote) {
      setVolumes(pacote.volumes || []);
    } else {
      setVolumes([]);
    }
    setApontados([]);
    setCodigo("");
  }, [pacoteIndex, lote]);

  const salvarVolumes = (novos) => {
    const atual = JSON.parse(localStorage.getItem("lotesProducao") || "[]");
    const idxLote = atual.findIndex(l => l.nome === lote);
    if (idxLote >= 0) {
      if (!atual[idxLote].pacotes[parseInt(pacoteIndex)].volumes) {
        atual[idxLote].pacotes[parseInt(pacoteIndex)].volumes = [];
      }
      atual[idxLote].pacotes[parseInt(pacoteIndex)].volumes = novos;
      localStorage.setItem("lotesProducao", JSON.stringify(atual));
    }
  };

const gerarCodigoBarra = (num) => {
  return `VOL-${Date.now()}-${num}`;
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

  const registrarCodigo = (e) => {
    e.preventDefault();
    if (!pacote) return;
    const cod = codigo.trim();
    if (!cod) return;
    if (cod === CODE_FECHA_VOLUME) {
      if (apontados.length) {
        const itensVolume = apontados.map(id => itensPacote.find(p => p.id === id));
        const novoVolume = {
          numero: volumes.length + 1,
          pecas: itensVolume,
          barcode: gerarCodigoBarra(volumes.length + 1)
        };
        const atualizados = [...volumes, novoVolume];
        setVolumes(atualizados);
        salvarVolumes(atualizados);
        setApontados([]);
        imprimirEtiqueta(novoVolume);
      }
    } else {
      const item = itensPacote.find(p => String(p.id).padStart(6,'0') === cod);
      if (item) {
        if (!apontados.includes(item.id)) {
          setApontados([...apontados, item.id]);
        }
      } else {
        alert("Código não encontrado no pacote");
      }
    }
    setCodigo("");
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
              placeholder="ID do item ou 999999 para fechar volume"
              value={codigo}
              onChange={e => setCodigo(e.target.value)}
              autoFocus
            />
          </form>
          <ul className="space-y-1 max-h-64 overflow-y-auto mb-4">
            {itensPacote.map(item => (
              <li
                key={item.id}
                className={`border rounded p-2 ${apontados.includes(item.id) ? 'bg-green-200' : ''}`}
              >
                <span className="font-mono mr-2">{String(item.id).padStart(6,'0')}</span>
                {item.nome || item.descricao}
              </li>
            ))}
          </ul>
          <h3 className="font-semibold mb-2">Volumes Criados</h3>
          <ul className="space-y-2">
            {volumes.map(v => (
              <li key={v.numero} className="border rounded p-2">
                <div className="font-semibold">Volume {v.numero} - {v.barcode}</div>
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
