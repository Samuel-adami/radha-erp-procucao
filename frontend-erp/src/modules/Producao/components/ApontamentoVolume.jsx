import React, { useState, useEffect } from "react";
import JsBarcode from "jsbarcode";

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

  const imprimirEtiqueta = (codigo) => {
    const printWindow = window.open('', '_blank', 'width=400,height=200');
    if (!printWindow) return;
    printWindow.document.write(`<html><body style="margin:0;display:flex;align-items:center;justify-content:center;">`);
    printWindow.document.write(`<svg id="barcode"></svg>`);
    printWindow.document.write('</body></html>');
    printWindow.document.close();
    JsBarcode(printWindow.document.getElementById('barcode'), codigo, { format: 'CODE128', displayValue: true });
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
        const pecasVolume = apontados.map(id => pacote.pecas.find(p => p.id === id));
        const novoVolume = {
          numero: volumes.length + 1,
          pecas: pecasVolume,
          barcode: gerarCodigoBarra(volumes.length + 1)
        };
        const atualizados = [...volumes, novoVolume];
        setVolumes(atualizados);
        salvarVolumes(atualizados);
        setApontados([]);
        imprimirEtiqueta(novoVolume.barcode);
      }
    } else {
      const peca = pacote.pecas.find(p => String(p.codigo_peca) === cod);
      if (peca) {
        if (!apontados.includes(peca.id)) {
          setApontados([...apontados, peca.id]);
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
      <div className="flex flex-col sm:flex-row gap-2 mb-4">
        <select
          className="input sm:w-48"
          value={lote}
          onChange={e => { setLote(e.target.value); setPacoteIndex(""); }}
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
            onChange={e => setPacoteIndex(e.target.value)}
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
              placeholder="Código de Barras"
              value={codigo}
              onChange={e => setCodigo(e.target.value)}
              autoFocus
            />
          </form>
          <ul className="space-y-1 max-h-64 overflow-y-auto mb-4">
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
          <h3 className="font-semibold mb-2">Volumes Criados</h3>
          <ul className="space-y-2">
            {volumes.map(v => (
              <li key={v.numero} className="border rounded p-2">
                <div className="font-semibold">Volume {v.numero} - {v.barcode}</div>
                <ul className="text-sm list-disc ml-4">
                  {v.pecas.map(pc => (
                    <li key={pc.id}>{pc.codigo_peca} - {pc.nome}</li>
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
