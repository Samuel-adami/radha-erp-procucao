import React, { useState, useEffect } from "react";
import { fetchComAuth } from "../../../utils/fetchComAuth";
import { Button } from "./ui/button";

const Nesting = () => {
  const [pastaLote, setPastaLote] = useState("");
  const [larguraChapa, setLarguraChapa] = useState(2750);
  const [alturaChapa, setAlturaChapa] = useState(1850);
  const [resultado, setResultado] = useState("");

  useEffect(() => {
    const cfg = JSON.parse(localStorage.getItem("nestingConfig") || "{}");
    if (cfg.pastaLote) setPastaLote(cfg.pastaLote);
    if (cfg.larguraChapa) setLarguraChapa(cfg.larguraChapa);
    if (cfg.alturaChapa) setAlturaChapa(cfg.alturaChapa);
  }, []);

  const salvar = () => {
    localStorage.setItem(
      "nestingConfig",
      JSON.stringify({ pastaLote, larguraChapa, alturaChapa })
    );
    alert("Configurações salvas");
  };

  const executar = async () => {
    try {
      const data = await fetchComAuth("/executar-nesting", {
        method: "POST",
        body: JSON.stringify({
          pasta_lote: pastaLote,
          largura_chapa: parseFloat(larguraChapa),
          altura_chapa: parseFloat(alturaChapa),
        }),
      });
      if (data?.erro) {
        alert(data.erro);
      } else if (data?.pasta_resultado) {
        setResultado(data.pasta_resultado);
      }
    } catch (err) {
      alert("Falha ao executar nesting");
      console.error(err);
    }
  };

  return (
    <div className="p-6 space-y-4">
      <h2 className="text-lg font-semibold">Configuração de Nesting</h2>
      <label className="block">
        <span className="text-sm">Pasta do Lote</span>
        <input
          type="text"
          className="input w-full"
          value={pastaLote}
          onChange={(e) => setPastaLote(e.target.value)}
        />
      </label>
      <label className="block">
        <span className="text-sm">Largura da chapa (mm)</span>
        <input
          type="number"
          className="input w-full"
          value={larguraChapa}
          onChange={(e) => setLarguraChapa(e.target.value)}
        />
      </label>
      <label className="block">
        <span className="text-sm">Altura da chapa (mm)</span>
        <input
          type="number"
          className="input w-full"
          value={alturaChapa}
          onChange={(e) => setAlturaChapa(e.target.value)}
        />
      </label>
      <div className="space-x-2">
        <Button onClick={salvar}>Salvar</Button>
        <Button onClick={executar}>Executar Nesting</Button>
      </div>
      {resultado && (
        <p className="text-sm">Arquivos gerados em: {resultado}</p>
      )}
    </div>
  );
};

export default Nesting;
