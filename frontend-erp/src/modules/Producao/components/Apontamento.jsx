import React, { useState, useEffect } from "react";
import JsBarcode from "jsbarcode";
import { Button } from "./ui/button";
import FiltroPacote from "./FiltroPacote";
import { fetchComAuth } from "../../../utils/fetchComAuth";

const CODE_FECHA_VOLUME = "999999";

const Apontamento = () => {
  const [lotes, setLotes] = useState([]);
  const [lote, setLote] = useState("");
  const [pacoteIndex, setPacoteIndex] = useState("");
  const [codigo, setCodigo] = useState("");
  const [pendentes, setPendentes] = useState([]);
  const [volumes, setVolumes] = useState([]);
  const [pacotes, setPacotes] = useState([]);
  const pacote = pacotes[parseInt(pacoteIndex)] || null;
  const itensPacote = pacote ? [...(pacote.pecas || []), ...(pacote.ferragens || [])] : [];

  useEffect(() => {
    const carregar = async () => {
      try {
        const [respL, respOc] = await Promise.all([
          fetchComAuth("/listar-lotes"),
          fetchComAuth("/lotes-ocorrencias"),
        ]);
        const listaProd = (respL?.lotes || []).map((p) => ({
          pasta: p,
          nome: p.split(/[/\\\\]/).pop(),
        }));
        const listaOc = (Array.isArray(respOc) ? respOc : respOc?.lotes || []).map((o) => ({
          pasta: o.obj_key,
          nome: o.obj_key.split(/[/\\\\]/).pop(),
        }));
        setLotes([...listaProd, ...listaOc]);
      } catch {
        setLotes([]);
      }
    };
    carregar();
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
      setPendentes([]);
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
    setPendentes([]);
    setCodigo("");
  }, [pacoteIndex, lote, pacotes]);

  const salvarVolumes = (novos) => {
    const pacoteAtual = pacotes[parseInt(pacoteIndex)];
    const nomePacote = pacoteAtual?.nome_pacote || `Pacote ${parseInt(pacoteIndex) + 1}`;
    fetchComAuth("/apontamentos", {
      method: "POST",
      body: JSON.stringify({ lote, pacote: nomePacote, volumes: novos }),
    }).catch(() => {});
  };

  const gerarCodigoBarra = (num) => {
    return `${Date.now()}${num}`;
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
        imprimirEtiqueta(novoVolume);
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
