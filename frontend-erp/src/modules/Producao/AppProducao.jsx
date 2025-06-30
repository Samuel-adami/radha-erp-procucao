import React, { useState, useEffect } from "react";
import { useNavigate, useParams, useLocation } from "react-router-dom";
import { Button } from "./components/ui/button"; 
import ImportarXML from "./components/ImportarXML";
import VisualizacaoPeca from "./components/VisualizacaoPeca";
import { fetchComAuth } from "../../utils/fetchComAuth";
import Pacote from "./components/Pacote";
import Apontamento from "./components/Apontamento";
import ApontamentoVolume from "./components/ApontamentoVolume";
import EditarFerragem from "./components/EditarFerragem";
import Nesting from "./components/Nesting";
import ConfigMaquina from "./components/ConfigMaquina";
import CadastroChapas from "./components/CadastroChapas";
import LotesOcorrencia from "./components/LotesOcorrencia";
import CadastroMotivos from "./components/CadastroMotivos";
import RelatorioOcorrencias from "./components/RelatorioOcorrencias";
import EditarLoteOcorrencia from "./components/EditarLoteOcorrencia";
import PacoteOcorrencia from "./components/PacoteOcorrencia";
import "./Producao.css";

const GATEWAY_URL = import.meta.env.VITE_GATEWAY_URL || "http://localhost:8010";

let globalIdProducao = parseInt(localStorage.getItem("globalPecaIdProducao")) || 1;

const HomeProducao = () => {
  const navigate = useNavigate();
  const [lotes, setLotes] = useState(JSON.parse(localStorage.getItem("lotesProducao") || "[]"));

  const criarLote = () => {
    const nome = prompt("Digite o nome do novo lote:");
    if (!nome) return;
    if (lotes.some(l => l.nome === nome)) return alert("Nome de lote já existe.");

    const novo = { nome, pacotes: [] };
    const atualizados = [...lotes, novo];
    setLotes(atualizados);
    localStorage.setItem("lotesProducao", JSON.stringify(atualizados));
    navigate(`lote/${nome}`);
  };

  const excluirLote = async (nome) => {
    if (!window.confirm(`Tem certeza que deseja excluir o lote "${nome}"?`)) return;
    const atualizados = lotes.filter(l => l.nome !== nome);
    setLotes(atualizados);
    localStorage.setItem("lotesProducao", JSON.stringify(atualizados));
    try {
      await fetchComAuth("/excluir-lote", {
        method: "POST",
        body: JSON.stringify({ lote: nome })
      });
    } catch (e) {
      console.error("Erro ao excluir lote no backend", e);
    }
  };

  const baixarLote = (nome) => {
    const url = `${GATEWAY_URL}/producao/download-lote/${encodeURIComponent(nome)}`;
    window.open(url, '_blank');
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Painel de Produção Radha</h1>
      <Button onClick={criarLote}>+ Novo Lote</Button>
      <ul className="mt-4 space-y-2">
        {lotes.map((l, i) => (
          <li key={l.nome || i} className="flex justify-between items-center border p-2 rounded">
            <span>{l.nome}</span>
            <div className="space-x-2">
              <Button onClick={() => navigate(`lote/${l.nome}`)}>Editar</Button>
              <Button onClick={() => baixarLote(l.nome)}>Baixar</Button>
              <Button variant="destructive" onClick={() => excluirLote(l.nome)}>Excluir</Button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
};

const LoteProducao = () => {
  const { nome } = useParams();
  const navigate = useNavigate();
  const [pacotes, setPacotes] = useState(() => {
    const lotes = JSON.parse(localStorage.getItem("lotesProducao") || "[]");
    return lotes.find(l => l.nome === nome)?.pacotes || [];
  });

  const salvarPacotes = (novosPacotes) => {
    const pacotesComIds = novosPacotes.map(pacote => {
      const pecasComIds = (pacote.pecas || []).map(p => {
        const id = globalIdProducao++;
        if (p.operacoes) {
          localStorage.setItem("op_producao_" + id, JSON.stringify(p.operacoes));
        }
        localStorage.setItem("editado_peca_" + id, "false");
        return { ...p, id };
      });
      const ferragensComIds = (pacote.ferragens || []).map(f => ({
        ...f,
        id: globalIdProducao++
      }));
      return { ...pacote, pecas: pecasComIds, ferragens: ferragensComIds };
    });

    localStorage.setItem("globalPecaIdProducao", globalIdProducao);

    const lotes = JSON.parse(localStorage.getItem("lotesProducao") || "[]");
    const atualizados = lotes.map(l =>
      l.nome === nome ? { ...l, pacotes: [...(l.pacotes || []), ...pacotesComIds] } : l
    );
    localStorage.setItem("lotesProducao", JSON.stringify(atualizados));
    setPacotes(prev => [...prev, ...pacotesComIds]);
  };

  const excluirPacote = (index) => {
    if (!window.confirm(`Tem certeza que deseja excluir este pacote?`)) return;
    const novos = pacotes.filter((_, i) => i !== index);
    const lotes = JSON.parse(localStorage.getItem("lotesProducao") || "[]");
    const atualizados = lotes.map(l =>
      l.nome === nome ? { ...l, pacotes: novos } : l
    );
    localStorage.setItem("lotesProducao", JSON.stringify(atualizados));
    setPacotes(novos);
  };

  const gerarArquivos = async () => {
    const pecas = pacotes.flatMap(p => p.pecas.map(pc => ({
      ...pc,
      operacoes: JSON.parse(localStorage.getItem("op_producao_" + pc.id) || "[]")
    })));
    const json = await fetchComAuth("/gerar-lote-final", {
      method: "POST",
      body: JSON.stringify({ lote: nome, pecas })
    });
    alert(json.mensagem);
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold">Lote: {nome}</h2>
        <Button variant="outline" onClick={() => navigate("/producao")}>Voltar para Início da Produção</Button>
      </div>

      <ImportarXML onImportarPacote={(p) => salvarPacotes([p])} />

      <ul className="space-y-2 mt-4">
        {pacotes.map((p, i) => (
          <li key={i} className="border p-2 rounded">
            <div className="flex justify-between">
              <div className="font-semibold">{p.nome_pacote || `Pacote ${i + 1}`}</div>
              <div className="space-x-2">
                <Button onClick={() => navigate(`pacote/${i}`)}>Editar</Button>
                <Button variant="destructive" onClick={() => excluirPacote(i)}>Excluir</Button>
              </div>
            </div>
          </li>
        ))}
      </ul>

      <Button className="mt-6" onClick={gerarArquivos}>Gerar Arquivos Finais</Button>
    </div>
  );
};

const EditarPecaProducao = () => {
  const { nome, peca: pecaId } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const origemOcorrencia = location.state?.origem === "ocorrencia";
  const ocId = location.state?.ocId;
  const pacoteIndex = location.state?.pacoteIndex;

  const [dadosPeca, setDadosPeca] = useState(null);
  const [operacoes, setOperacoes] = useState([]);
  const [operacao, setOperacao] = useState("Retângulo");
  const [form, setForm] = useState({ comprimento: "", largura: "", profundidade: "", diametro: "", x: 0, y: 0, estrategia: "Por Dentro", posicao: "C1", face: "Face (F0)" });
  const [espelhar, setEspelhar] = useState(false);
  const [novoComprimento, setNovoComprimento] = useState("");
  const [novaLargura, setNovaLargura] = useState("");
  const [temPuxador, setTemPuxador] = useState(() =>
    Boolean(localStorage.getItem("puxador_original_" + pecaId))
  );

  useEffect(() => {
    let pecaEncontrada = null;

    if (origemOcorrencia) {
      const lotesOc = JSON.parse(localStorage.getItem("lotesOcorrenciaLocal") || "[]");
      const lote = lotesOc.find((l) => l.id === ocId);
      pecaEncontrada = lote?.pacoteData?.pecas?.find((p) => p.id === parseInt(pecaId));
    } else {
      const lotes = JSON.parse(localStorage.getItem("lotesProducao") || "[]");
      for (const l of lotes) {
        if (l.nome === nome) {
          for (const pacote of l.pacotes || []) {
            const p = pacote.pecas.find((p) => p.id === parseInt(pecaId));
            if (p) {
              pecaEncontrada = p;
              break;
            }
          }
        }
        if (pecaEncontrada) break;
      }
    }

    if (pecaEncontrada) {
      const dadosEditados = origemOcorrencia
        ? JSON.parse(localStorage.getItem("ocedit_dados_" + pecaId) || "null")
        : null;
      setDadosPeca({ ...pecaEncontrada, ...(dadosEditados || {}) });
      const chaveOp = origemOcorrencia
        ? "ocedit_op_" + pecaId
        : "op_producao_" + pecaId;
      let operacoesSalvas = JSON.parse(localStorage.getItem(chaveOp) || "[]");
      if (origemOcorrencia && operacoesSalvas.length === 0) {
        operacoesSalvas = JSON.parse(
          localStorage.getItem("op_producao_" + pecaId) || "[]"
        );
      }
      setOperacoes(operacoesSalvas);
      setNovoComprimento(dadosEditados?.comprimento || pecaEncontrada.comprimento);
      setNovaLargura(dadosEditados?.largura || pecaEncontrada.largura);
    }
  }, [pecaId, nome, origemOcorrencia, ocId]);

const espelharPuxadorCurvo = (ops = [], medida, eixo = 'Y') => {
  const M = parseFloat(medida);
  if (isNaN(M)) return ops;
  return ops.map(op => {
    const novo = { ...op };
    if (eixo === 'X') {
      if (novo.x !== undefined) {
        const x = parseFloat(novo.x);
        if (["Retângulo", "Linha"].includes(novo.tipo)) {
          const w = parseFloat(novo.comprimento || 0);
          novo.x = M - x - w;
        } else {
          novo.x = M - x;
        }
      }
      if (novo.tipo === 'Raio' && novo.pos === 'C1') {
        // mantém a posição original para espelhar dentro da extremidade C1
      }
    } else {
      if (novo.y !== undefined) {
        const y = parseFloat(novo.y);
        if (["Retângulo", "Linha"].includes(novo.tipo)) {
          const h = parseFloat(novo.largura || 0);
          novo.y = M - y - h;
        } else {
          novo.y = M - y;
        }
      }
      if (novo.tipo === 'Raio' && novo.pos) {
        if (novo.pos === 'L1') {
          // permanece em L1 para manter a extremidade
        } else if (novo.pos === 'L3') {
          novo.pos = 'C1';
        } else if (novo.pos === 'C1') {
          novo.pos = 'C2';
        } else if (novo.pos === 'C2') {
          novo.pos = 'C1';
        }
      }
    }
    return novo;
  });
};

  const salvarOperacao = () => {
    const pos = form.posicao;
    let posLinha = pos;
    let operacoesAtuais = [...operacoes];

    if (operacao === "Puxador Cava" || operacao === "Puxador Cava Curvo") {
      const isCurvo = operacao === "Puxador Cava Curvo";
      const originalComprimento = parseFloat(dadosPeca.comprimento);
      const originalLargura = parseFloat(dadosPeca.largura);
      let novoComprimento = originalComprimento;
      let novaLargura = originalLargura;
      const ajuste = 25;
      let painelLargura;
      const descontoLinha = isCurvo ? 75 : 0;

      if (pos.startsWith('C')) {
        novaLargura -= ajuste;
        painelLargura = originalComprimento;
      } else {
        novoComprimento -= ajuste;
        painelLargura = originalLargura;
      }

      operacoesAtuais = operacoes.map(op => {
        let opAjustada = { ...op };
        if (pos.startsWith('L') && op.x > originalComprimento / 2) { opAjustada.x -= ajuste; }
        if (pos.startsWith('C') && op.y > originalLargura / 2) { opAjustada.y -= ajuste; }
        return opAjustada;
      });

      const novasOps = [];
      if (pos === "C1") {
        novasOps.push({ tipo: "Retângulo", x: 0, y: 0, largura: 55, comprimento: originalComprimento, profundidade: 6.5, estrategia: "Desbaste" });
        const yLinha = posLinha === "C2" ? originalLargura - 1 : 0;
        novasOps.push({ tipo: "Linha", x: 0, y: yLinha, largura: 1, comprimento: originalComprimento - descontoLinha, profundidade: 18.2, estrategia: "Linha" });
        if (isCurvo) {
          const subPos = espelhar ? "T1" : "T4";
          novasOps.push({ tipo: "Raio", pos: posLinha, raio: 51, subPos });
        }
      } else if (pos === "C2") {
        novasOps.push({ tipo: "Retângulo", x: 0, y: originalLargura - 55, largura: 55, comprimento: originalComprimento, profundidade: 6.5, estrategia: "Desbaste" });
        const yLinha = posLinha === "C1" ? 0 : originalLargura - 1;
        novasOps.push({ tipo: "Linha", x: 0, y: yLinha, largura: 1, comprimento: originalComprimento - descontoLinha, profundidade: 18.2, estrategia: "Linha" });
        if (isCurvo) {
          const subPos = espelhar ? "inferior" : "superior";
          novasOps.push({ tipo: "Raio", pos: posLinha, raio: 51, subPos });
        }
      } else {
        let x_rect1 = pos === 'L3' ? novoComprimento - 55 : 0;
        const xLinha = posLinha === 'L3' ? novoComprimento - 1 : 0;
        novasOps.push({ tipo: "Retângulo", x: x_rect1, y: 0, largura: originalLargura, comprimento: 55, profundidade: 6.5, estrategia: "Desbaste" });
        novasOps.push({ tipo: "Linha", x: xLinha, y: 0, largura: originalLargura - descontoLinha, comprimento: 1, profundidade: 18.2, estrategia: "Linha" });
        if (isCurvo) {
          const subPos = espelhar ? "inferior" : "superior";
          novasOps.push({ tipo: "Raio", pos: posLinha, raio: 51, subPos });
        }
      }

      let opsFinal = novasOps;
      if (isCurvo && espelhar) {
        if (pos === 'C1') {
          opsFinal = espelharPuxadorCurvo(novasOps, originalComprimento, 'X');
        } else {
          const medida = originalLargura;
          opsFinal = espelharPuxadorCurvo(novasOps, medida, 'Y');
        }
      }
      operacoesAtuais.push(...opsFinal);
      localStorage.setItem(
        "puxador_original_" + pecaId,
        JSON.stringify({
          comprimento: originalComprimento,
          largura: originalLargura,
          operacoes: operacoes,
        })
      );

      let newPecaId = parseInt(localStorage.getItem("globalPecaIdProducao")) || 1;
      localStorage.setItem("globalPecaIdProducao", newPecaId + 1);
      localStorage.setItem("puxador_painel_" + pecaId, newPecaId);

      const originalMaterial = dadosPeca.material || "";
      const novoMaterialPainel = originalMaterial.replace(/\d+mm/gi, '6mm');

      const painelPuxador = {
        id: newPecaId, nome: `PAINEL PUXADOR P/ ${dadosPeca.nome}`,
        comprimento: 80, largura: painelLargura, espessura: 6,
        material: novoMaterialPainel,
        cliente: dadosPeca.cliente, ambiente: dadosPeca.ambiente,
        observacoes: `Painel complementar para puxador cava da peça ID ${pecaId}`,
        codigo_peca: dadosPeca.codigo_peca,
        operacoes: []
      };

      if (!origemOcorrencia) {
        const lotes = JSON.parse(localStorage.getItem("lotesProducao") || "[]");
        const lotesAtualizados = lotes.map((lote) =>
          lote.nome !== nome
            ? lote
            : {
                ...lote,
                pacotes: lote.pacotes.map((pacote) => {
                  if (!pacote.pecas.some((p) => p.id === parseInt(pecaId))) return pacote;
                  const pecasAtualizadas = pacote.pecas.map((p) =>
                    p.id === parseInt(pecaId) ? { ...p, comprimento: novoComprimento, largura: novaLargura } : p
                  );
                  pecasAtualizadas.push(painelPuxador);
                  return { ...pacote, pecas: pecasAtualizadas };
                }),
              }
        );
        localStorage.setItem("lotesProducao", JSON.stringify(lotesAtualizados));
        localStorage.setItem(`op_producao_${newPecaId}`, JSON.stringify([]));
      }

      setDadosPeca(prev => ({ ...prev, comprimento: novoComprimento, largura: novaLargura }));
      setTemPuxador(true);

    } else if (operacao === "Corte 45 graus") {
        if (pos.startsWith("L")) {
          const x = pos === "L3" ? dadosPeca.comprimento - 1 : 0;
          operacoesAtuais.push({ tipo: "Linha", x, y: 0, largura: dadosPeca.largura, comprimento: 1, profundidade: 18.2, estrategia: "Linha" });
        } else {
          const y = pos === "C2" ? dadosPeca.largura - 1 : 0;
          operacoesAtuais.push({ tipo: "Linha", x: 0, y, largura: 1, comprimento: dadosPeca.comprimento, profundidade: 18.2, estrategia: "Linha" });
        }
    } else {
      operacoesAtuais.push({ ...form, tipo: operacao });
    }

    setOperacoes(operacoesAtuais);
    const chaveOp = origemOcorrencia ? "ocedit_op_" + pecaId : "op_producao_" + pecaId;
    localStorage.setItem(chaveOp, JSON.stringify(operacoesAtuais));
    localStorage.setItem(`editado_peca_${pecaId}`, operacoesAtuais.length > 0 ? "true" : "false");
    setForm({ comprimento: "", largura: "", profundidade: "", diametro: "", x: 0, y: 0, estrategia: "Por Dentro", posicao: "C1", face: "Face (F0)" });
    setEspelhar(false);
  };

  const excluirTodas = () => {
    setOperacoes([]);
    const chaveOp = origemOcorrencia ? "ocedit_op_" + pecaId : "op_producao_" + pecaId;
    localStorage.removeItem(chaveOp);
    localStorage.setItem(`editado_peca_${pecaId}`, "false");
  };

  const excluirUma = (index) => {
    const novas = operacoes.filter((_, i) => i !== index);
    setOperacoes(novas);
    const chaveOp = origemOcorrencia ? "ocedit_op_" + pecaId : "op_producao_" + pecaId;
    localStorage.setItem(chaveOp, JSON.stringify(novas));
    localStorage.setItem(`editado_peca_${pecaId}`, novas.length > 0 ? "true" : "false");
  };

  const editarUma = (index) => {
    const op = operacoes[index];
    if (!op) return;
    const novoX = prompt("Novo X", op.x);
    if (novoX === null) return;
    const novoY = prompt("Novo Y", op.y);
    if (novoY === null) return;
    const novas = operacoes.map((o, i) =>
      i === index ? { ...o, x: parseFloat(novoX), y: parseFloat(novoY) } : o
    );
    setOperacoes(novas);
    const chaveOp = origemOcorrencia ? "ocedit_op_" + pecaId : "op_producao_" + pecaId;
    localStorage.setItem(chaveOp, JSON.stringify(novas));
    localStorage.setItem(`editado_peca_${pecaId}`, novas.length > 0 ? "true" : "false");
  };

  const desfazerPuxador = () => {
    const original = localStorage.getItem("puxador_original_" + pecaId);
    if (!original) return;
    const dados = JSON.parse(original);
    const painelId = parseInt(localStorage.getItem("puxador_painel_" + pecaId) || "0");
    setOperacoes(dados.operacoes || []);
    const chaveOp = origemOcorrencia ? "ocedit_op_" + pecaId : "op_producao_" + pecaId;
    localStorage.setItem(chaveOp, JSON.stringify(dados.operacoes || []));
    localStorage.setItem(`editado_peca_${pecaId}`, (dados.operacoes || []).length > 0 ? "true" : "false");
    if (!origemOcorrencia) {
      const lotes = JSON.parse(localStorage.getItem("lotesProducao") || "[]");
      const atualizados = lotes.map(l =>
        l.nome !== nome ? l : {
          ...l,
          pacotes: l.pacotes.map(pac => {
            if (!pac.pecas.some(p => p.id === parseInt(pecaId))) return pac;
            const novasPecas = pac.pecas
              .filter(p => p.id !== painelId)
              .map(p => p.id === parseInt(pecaId) ? { ...p, comprimento: dados.comprimento, largura: dados.largura } : p);
            return { ...pac, pecas: novasPecas };
          })
        }
      );
      localStorage.setItem("lotesProducao", JSON.stringify(atualizados));
    }
    setDadosPeca(prev => ({ ...prev, comprimento: dados.comprimento, largura: dados.largura }));
    localStorage.removeItem("puxador_original_" + pecaId);
    localStorage.removeItem("puxador_painel_" + pecaId);
    setTemPuxador(false);
  };

  const salvarMedidas = () => {
    const comp = parseFloat(novoComprimento);
    const larg = parseFloat(novaLargura);
    if (isNaN(comp) || isNaN(larg)) {
      alert("Medidas inválidas");
      return;
    }

    const fatorX = comp / parseFloat(dadosPeca.comprimento);
    const fatorY = larg / parseFloat(dadosPeca.largura);
    const opsEscaladas = operacoes.map((op) => {
      const novo = { ...op };
      if (novo.x !== undefined) novo.x *= fatorX;
      if (novo.y !== undefined) novo.y *= fatorY;
      if (novo.comprimento !== undefined) novo.comprimento *= fatorX;
      if (novo.largura !== undefined) novo.largura *= fatorY;
      return novo;
    });
    setOperacoes(opsEscaladas);
    const chaveOp = origemOcorrencia ? "ocedit_op_" + pecaId : "op_producao_" + pecaId;
    localStorage.setItem(chaveOp, JSON.stringify(opsEscaladas));
    localStorage.setItem(`editado_peca_${pecaId}`, opsEscaladas.length > 0 ? "true" : "false");

    if (origemOcorrencia) {
      localStorage.setItem(
        "ocedit_dados_" + pecaId,
        JSON.stringify({ comprimento: comp, largura: larg })
      );
    } else {
      const lotes = JSON.parse(localStorage.getItem("lotesProducao") || "[]");
      const atualizados = lotes.map((l) =>
        l.nome !== nome
          ? l
          : {
              ...l,
              pacotes: l.pacotes.map((pac) => {
                if (!pac.pecas.some((p) => p.id === parseInt(pecaId))) return pac;
                return {
                  ...pac,
                  pecas: pac.pecas.map((p) =>
                    p.id === parseInt(pecaId)
                      ? { ...p, comprimento: comp, largura: larg }
                      : p
                  ),
                };
              }),
            }
      );
      localStorage.setItem("lotesProducao", JSON.stringify(atualizados));
    }

    setDadosPeca((prev) => ({ ...prev, comprimento: comp, largura: larg }));
  };

  if (!dadosPeca) return <p className="p-6">Peça não encontrada ou carregando...</p>;

  const orientacao = parseFloat(dadosPeca.comprimento) >= parseFloat(dadosPeca.largura) ? "horizontal" : "vertical";
  const cores = ["blue", "green", "orange", "purple"];

  const campos = () => {
    if (["Puxador Cava", "Puxador Cava Curvo", "Corte 45 graus"].includes(operacao)) {
      return (
        <>
          <label className="block mt-2">Extremidade:
            <select className="input" value={form.posicao} onChange={e => setForm({ ...form, posicao: e.target.value })}>
              <option value="C1">Comprimento (C1)</option>
              {operacao !== "Puxador Cava Curvo" && (
                <option value="C2">Comprimento (C2)</option>
              )}
              <option value="L1">Largura (L1)</option>
              <option value="L3">Largura (L3)</option>
            </select>
          </label>
          {operacao === "Puxador Cava Curvo" && (
            <label className="block mt-2">
              <input type="checkbox" className="mr-1" checked={espelhar} onChange={e => setEspelhar(e.target.checked)} />
              Espelhar
            </label>
          )}
        </>
      );
    }
    if (["Retângulo", "Círculo", "Furo", "Linha"].includes(operacao)) {
        const camposComuns = <>
            <label className="block mt-2">Face:
                <select className="input" value={form.face} onChange={e => setForm({ ...form, face: e.target.value })}>
                    <option value="Face (F0)">Face (F0)</option>
                    <option value="Topo (L1)">Topo (L1)</option>
                    <option value="Topo (L3)">Topo (L3)</option>
                </select>
            </label>
            <label className="block mt-2">X:
                <input type="number" className="input" value={form.x} onChange={e => setForm({ ...form, x: e.target.value })} />
            </label>
            <label className="block mt-2">Y:
                <input type="number" className="input" value={form.y} onChange={e => setForm({ ...form, y: e.target.value })} />
            </label>
            <label className="block mt-2">Profundidade:
                <input type="number" className="input" value={form.profundidade} onChange={e => setForm({ ...form, profundidade: e.target.value })} />
            </label>
        </>;

        if (operacao === "Círculo" || operacao === "Furo") {
            return <>
                {camposComuns}
                <label className="block mt-2">Diâmetro:
                    <input type="number" className="input" value={form.diametro} onChange={e => setForm({ ...form, diametro: e.target.value })} />
                </label>
            </>;
        }

        if (operacao === "Retângulo" || operacao === "Linha") {
            return <>
                {camposComuns}
                <label className="block mt-2">Comprimento:
                    <input type="number" className="input" value={form.comprimento} onChange={e => setForm({ ...form, comprimento: e.target.value })} />
                </label>
                <label className="block mt-2">Largura:
                    <input type="number" className="input" value={form.largura} onChange={e => setForm({ ...form, largura: e.target.value })} />
                </label>
            </>;
        }
    }
    return null;
  };

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <h3 className="text-lg font-medium mb-2">Peça: {dadosPeca.nome}</h3>
      <div className="border p-4 rounded bg-gray-50 overflow-x-auto w-full min-w-[620px]">
        <VisualizacaoPeca comprimento={dadosPeca.comprimento} largura={dadosPeca.largura} orientacao={orientacao} operacoes={operacoes} />
        <p className="mt-2">Medidas: {dadosPeca.comprimento}mm x {dadosPeca.largura}mm</p>
        {origemOcorrencia && (
          <div className="flex gap-2 mt-2">
            <label className="block">
              <span className="text-sm">Comprimento:</span>
              <input
                type="number"
                className="input w-24"
                value={novoComprimento}
                onChange={(e) => setNovoComprimento(e.target.value)}
              />
            </label>
            <label className="block">
              <span className="text-sm">Largura:</span>
              <input
                type="number"
                className="input w-24"
                value={novaLargura}
                onChange={(e) => setNovaLargura(e.target.value)}
              />
            </label>
            <Button size="sm" className="self-end" onClick={salvarMedidas}>Salvar Medidas</Button>
          </div>
        )}
        <label className="block mt-4">Operação:
          <select className="input" value={operacao} onChange={e => setOperacao(e.target.value)}>
            <option>Retângulo</option>
            <option>Círculo</option>
            <option>Furo</option>
            <option>Linha</option>
            <option>Puxador Cava</option>
            <option>Puxador Cava Curvo</option>
            <option>Corte 45 graus</option>
          </select></label>

        {campos()}

        { !["Puxador Cava", "Puxador Cava Curvo", "Corte 45 graus"].includes(operacao) && (operacao === "Furo" ? <p className="mt-2">Estratégia: Por Dentro</p> : (
            <label className="block mt-2">Estratégia:
              <select className="input" value={form.estrategia} onChange={e => setForm({ ...form, estrategia: e.target.value })}>
                <option>Por Dentro</option>
                <option>Por Fora</option>
                <option>Desbaste</option>
                <option>Linha</option>
              </select></label>
          ))
        }
        <div className="flex gap-2 mt-4">
          <Button onClick={salvarOperacao}>Salvar Operação</Button>
          {temPuxador && (
            <Button variant="outline" onClick={desfazerPuxador}>Desfazer Puxador</Button>
          )}
          <Button
            variant="outline"
              onClick={() =>
                origemOcorrencia
                  ? navigate(`/producao/ocorrencias/pacote/${ocId}`)
                  : pacoteIndex !== undefined
                    ? navigate(`/producao/lote/${nome}/pacote/${pacoteIndex}`)
                    : navigate(`/producao/lote/${nome}`)
              }
          >
            Finalizar
          </Button>
          <Button variant="destructive" onClick={excluirTodas}>Excluir Todas</Button>
        </div>

        <ul className="mt-4 space-y-1 text-sm">
          {operacoes.map((op, i) => {
            let detalhes = `@ (${op.x}, ${op.y})`;
            if (op.tipo === "Retângulo" || op.tipo === "Linha") {
              detalhes += ` - ${op.largura} x ${op.comprimento}mm`;
            } else if (op.tipo === "Círculo" || op.tipo === "Furo") {
              detalhes += ` - Ø ${op.diametro}mm`;
            }
            if (op.profundidade) {
              detalhes += ` - Prof: ${op.profundidade}mm`;
            }

            return (
              <li key={i} className="flex justify-between">
                <span style={{ color: cores[i % cores.length] }}>
                  {op.tipo} {detalhes}
                </span>
                <div className="space-x-2">
                  <Button size="sm" variant="outline" onClick={() => editarUma(i)}>Editar</Button>
                  <Button size="sm" variant="ghost" onClick={() => excluirUma(i)}>Excluir</Button>
                </div>
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
};

// Reexporta os componentes para uso no index.jsx do módulo
export { HomeProducao, LoteProducao, EditarPecaProducao, Pacote, Apontamento, ApontamentoVolume, EditarFerragem, ImportarXML, VisualizacaoPeca, Nesting, ConfigMaquina, CadastroChapas, LotesOcorrencia, CadastroMotivos, RelatorioOcorrencias, EditarLoteOcorrencia, PacoteOcorrencia };
