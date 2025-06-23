import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { fetchComAuth } from "../../../utils/fetchComAuth";
import { Button } from "./ui/button";

const modeloLayer = {
  nome: "",
  tipo: "Chapa",
  cortarSobras: false,
  rotacao: "90 graus",
  espessura: "",
  pecaOuSobra: "Peça",
  profundidade: "",
  ferramenta: "",
  estrategia: "",
};

const Nesting = () => {
  const navigate = useNavigate();
  const [pastaLote, setPastaLote] = useState("");
  const [lotes, setLotes] = useState([]);
  const [larguraChapa, setLarguraChapa] = useState(2750);
  const [alturaChapa, setAlturaChapa] = useState(1850);
  const [resultado, setResultado] = useState("");

  useEffect(() => {
    const cfg = JSON.parse(localStorage.getItem("nestingConfig") || "{}");
    if (cfg.pastaLote) setPastaLote(cfg.pastaLote);
    if (cfg.larguraChapa) setLarguraChapa(cfg.larguraChapa);
    if (cfg.alturaChapa) setAlturaChapa(cfg.alturaChapa);
    fetchComAuth("/listar-lotes")
      .then((d) => setLotes(d?.lotes || []))
      .catch((e) => console.error("Falha ao carregar lotes", e));
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
      const ferramentas = JSON.parse(localStorage.getItem("ferramentasNesting") || "[]");
      const configMaquina = JSON.parse(localStorage.getItem("configMaquina") || "null");
      const configLayers = JSON.parse(localStorage.getItem("configLayers") || "[]");
      const data = await fetchComAuth("/executar-nesting", {
        method: "POST",
        body: JSON.stringify({
          pasta_lote: pastaLote,
          largura_chapa: parseFloat(larguraChapa),
          altura_chapa: parseFloat(alturaChapa),
          ferramentas,
          config_maquina: configMaquina,
          config_layers: configLayers,
        }),
      });
      if (data?.erro) {
        alert(data.erro);
      } else if (data?.pasta_resultado) {
        setResultado(data.pasta_resultado);
        if (Array.isArray(data.layers)) {
          const existentes = JSON.parse(localStorage.getItem("configLayers") || "[]");
          const novos = [...existentes];
          const adiciona = (nome) => {
            if (novos.some(l => l.nome === nome)) return;
            const matchFuro = nome.match(/^FURO_(\d+)_([\d\.]+)$/i);
            const matchUsinar = nome.match(/^USINAR_([\d\.]+)_([\w]+)/i);
            if (matchFuro) {
              novos.push({
                ...modeloLayer,
                nome,
                tipo: 'Operação',
                profundidade: matchFuro[2],
                ferramenta: matchFuro[1]
              });
            } else if (matchUsinar) {
              novos.push({
                ...modeloLayer,
                nome,
                tipo: 'Operação',
                profundidade: matchUsinar[1],
                estrategia: matchUsinar[2]
              });
            } else {
              novos.push({ ...modeloLayer, nome });
            }
          };
          data.layers.forEach(adiciona);
          localStorage.setItem("configLayers", JSON.stringify(novos));
        }
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
        <select
          className="input w-full"
          value={pastaLote}
          onChange={(e) => setPastaLote(e.target.value)}
        >
          <option value="">Selecione...</option>
          {lotes.map((l) => (
            <option key={l} value={l}>
              {l}
            </option>
          ))}
        </select>
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
        <Button variant="outline" onClick={() => navigate('config-maquina')}>Configurar Máquina</Button>
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
