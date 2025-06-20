import React, { useState, useEffect } from "react";
import JsBarcode from "jsbarcode";
import { Button } from "./ui/button";
import FiltroPacote from "./FiltroPacote";

const CODE_FECHA_VOLUME = "999999";

const Apontamento = () => {
  const lotes = JSON.parse(localStorage.getItem("lotesProducao") || "[]");
  const [lote, setLote] = useState("");
  const [pacoteIndex, setPacoteIndex] = useState("");
  const [codigo, setCodigo] = useState("");
  const [pendentes, setPendentes] = useState([]);
  const [volumes, setVolumes] = useState([]);

  const pacotes = lote ? (lotes.find(l => l.nome === lote)?.pacotes || []) : [];
  const pacote = pacotes[parseInt(pacoteIndex)] || null;
  const itensPacote = pacote ? [...(pacote.pecas || []), ...(pacote.ferragens || [])] : [];

  useEffect(() => {
    if (pacote) {
      setVolumes(pacote.volumes || []);
    } else {
      setVolumes([]);
    }
    setPendentes([]);
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
      if (pendentes.length) {
        const itensVolume = pendentes.map(id => itensPacote.find(p => p.id === id));
        const novoVolume = {
          numero: volumes.length + 1,
          pecas: itensVolume,
          barcode: gerarCodigoBarra(volumes.length + 1)
        };
        const atualizados = [...volumes, novoVolume];
        setVolumes(atualizados);
        salvarVolumes(atualizados);
        setPendentes([]);
        imprimirEtiqueta(novoVolume.barcode);
      }
    } else {
      const item = itensPacote.find(p => String(p.id).padStart(6,'0') === cod);
      if (item) {
        const jaFechado = volumes.some(v => v.pecas.some(p => p.id === item.id));
        if (!jaFechado && !pendentes.includes(item.id)) {
          setPendentes([...pendentes, item.id]);
        }
      } else {
        alert("Código não encontrado no pacote");
      }
    }
    setCodigo("");
  };

  const idsFechados = new Set(volumes.flatMap(v => v.pecas.map(p => p.id)));

  return (
    <div className="p-6">
      <h2 className="text-lg font-semibold mb-4">Apontamento de Itens</h2>
      <FiltroPacote
        lotes={lotes}
        lote={lote}
        onChangeLote={(v) => { setLote(v); setPacoteIndex(""); setPendentes([]); }}
        pacotes={pacotes}
        pacoteIndex={pacoteIndex}
        onChangePacote={(v) => { setPacoteIndex(v); setPendentes([]); }}
      />
      {pacote && (
        <>
          <form onSubmit={registrarCodigo} className="mb-4">
            <input
              className="input w-full sm:w-64"
              placeholder="ID do item (6 dígitos)"
              value={codigo}
              onChange={e => setCodigo(e.target.value)}
              autoFocus
            />
          </form>
          <ul className="space-y-1 max-h-96 overflow-y-auto">
            {itensPacote.map(item => {
              const classe = idsFechados.has(item.id)
                ? 'bg-green-200'
                : pendentes.includes(item.id)
                  ? 'bg-yellow-200'
                  : '';
              return (
                <li key={item.id} className={`border rounded p-2 ${classe}`}>
                  <span className="font-mono mr-2">{String(item.id).padStart(6,'0')}</span>
                  {item.nome || item.descricao}
                </li>
              );
            })}
          </ul>
        </>
      )}
    </div>
  );
};

export default Apontamento;
