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

const criaLayer = (nome) => {
  const matchFuro = nome.match(/^FURO_(\d+)_([\d\.]+)$/i);
  const matchUsinar = nome.match(/^USINAR_([\d\.]+)_([\w]+)/i);
  if (matchFuro) {
    return {
      ...modeloLayer,
      nome,
      tipo: "Operação",
      profundidade: matchFuro[2],
      ferramenta: `BROCA ${matchFuro[1]}MM`,
    };
  }
  if (matchUsinar) {
    return {
      ...modeloLayer,
      nome,
      tipo: "Operação",
      profundidade: matchUsinar[1],
      estrategia: matchUsinar[2],
    };
  }
  return { ...modeloLayer, nome };
};

const Nesting = () => {
  const navigate = useNavigate();
  const [pastaLote, setPastaLote] = useState("");
  const [lotes, setLotes] = useState([]);
  const [larguraChapa, setLarguraChapa] = useState(2750);
  const [alturaChapa, setAlturaChapa] = useState(1850);
  const [resultado, setResultado] = useState("");
  const [layers, setLayers] = useState(() =>
    JSON.parse(localStorage.getItem("configLayers") || "[]")
  );
  const [fila, setFila] = useState([]);
  const [layerAtual, setLayerAtual] = useState(null);

  useEffect(() => {
    const cfg = JSON.parse(localStorage.getItem("nestingConfig") || "{}");
    if (cfg.pastaLote) setPastaLote(cfg.pastaLote);
    if (cfg.larguraChapa) setLarguraChapa(cfg.larguraChapa);
    if (cfg.alturaChapa) setAlturaChapa(cfg.alturaChapa);
    fetchComAuth("/listar-lotes")
      .then((d) => setLotes(d?.lotes || []))
      .catch((e) => console.error("Falha ao carregar lotes", e));
  }, []);

  useEffect(() => {
    localStorage.setItem("configLayers", JSON.stringify(layers));
  }, [layers]);

  const salvar = () => {
    localStorage.setItem(
      "nestingConfig",
      JSON.stringify({ pastaLote, larguraChapa, alturaChapa })
    );
    alert("Configurações salvas");
  };

  const handleLayer = (campo) => (e) => {
    const value = e.target.type === 'checkbox' ? e.target.checked : e.target.value;
    setLayerAtual({ ...layerAtual, [campo]: value });
  };

  const executar = async () => {
    try {
      const ferramentas = JSON.parse(localStorage.getItem("ferramentasNesting") || "[]");
      const configMaquina = JSON.parse(localStorage.getItem("configMaquina") || "null");
      const configLayers = layers;
      const cortes = JSON.parse(localStorage.getItem("configuracoesCorte") || "[]");

      if (!configMaquina) return alert("Configuração da máquina não cadastrada.");
      if (!ferramentas.length) return alert("Cadastre ao menos uma ferramenta.");
      if (!cortes.length) return alert("Configure o módulo de corte.");
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
          const faltantes = data.layers.filter(
            (n) => !layers.some((l) => l.nome === n)
          );
          if (faltantes.length) {
            const filaInicial = faltantes.map(criaLayer);
            setFila(filaInicial);
            setLayerAtual(filaInicial[0]);
          }
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
      {layerAtual && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white p-4 space-y-2 rounded shadow max-w-sm w-full">
            <h3 className="font-semibold">Cadastrar Layer</h3>
            <label className="block">
              <span className="text-sm">Nome do Layer</span>
              <input
                className="input w-full"
                value={layerAtual.nome}
                onChange={handleLayer('nome')}
              />
            </label>
            <label className="block">
              <span className="text-sm">Configuração</span>
              <select className="input w-full" value={layerAtual.tipo} onChange={handleLayer('tipo')}>
                <option>Chapa</option>
                <option>Peça/Sobra</option>
                <option>Operação</option>
              </select>
            </label>
            {layerAtual.tipo === 'Chapa' && (
              <>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={layerAtual.cortarSobras}
                    onChange={handleLayer('cortarSobras')}
                  />
                  <span className="text-sm">Cortar sobras após cortar peças</span>
                </label>
                <label className="block">
                  <span className="text-sm">Rotacionar DXF</span>
                  <select className="input w-full" value={layerAtual.rotacao} onChange={handleLayer('rotacao')}>
                    <option>90 graus</option>
                    <option>180 graus</option>
                    <option>270 graus</option>
                  </select>
                </label>
                <label className="block">
                  <span className="text-sm">Espessura do Material (mm)</span>
                  <input
                    type="number"
                    className="input w-full"
                    value={layerAtual.espessura}
                    onChange={handleLayer('espessura')}
                  />
                </label>
              </>
            )}
            {layerAtual.tipo === 'Peça/Sobra' && (
              <label className="block">
                <span className="text-sm">Tipo</span>
                <select className="input w-full" value={layerAtual.pecaOuSobra} onChange={handleLayer('pecaOuSobra')}>
                  <option>Peça</option>
                  <option>Sobra</option>
                </select>
              </label>
            )}
            {layerAtual.tipo === 'Operação' && (
              <>
                <label className="block">
                  <span className="text-sm">Profundidade (mm)</span>
                  <input
                    type="number"
                    className="input w-full"
                    value={layerAtual.profundidade}
                    onChange={handleLayer('profundidade')}
                  />
                </label>
                <label className="block">
                  <span className="text-sm">Ferramenta</span>
                  <input className="input w-full" value={layerAtual.ferramenta} onChange={handleLayer('ferramenta')} />
                </label>
                <label className="block">
                  <span className="text-sm">Estratégia</span>
                  <select className="input w-full" value={layerAtual.estrategia} onChange={handleLayer('estrategia')}>
                    <option value="">Selecione</option>
                    <option>Por Dentro</option>
                    <option>Por Fora</option>
                    <option>Desbaste</option>
                  </select>
                </label>
              </>
            )}
            <div className="space-x-2 pt-2">
              <Button
                onClick={() => {
                  const prox = fila.slice(1);
                  const lista = [...layers, layerAtual];
                  setLayers(lista);
                  localStorage.setItem('configLayers', JSON.stringify(lista));
                  setFila(prox);
                  setLayerAtual(prox[0] || null);
                }}
              >
                Cadastrar
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Nesting;
