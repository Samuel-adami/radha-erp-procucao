import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Button } from "./ui/button";
import { fetchComAuth } from "../../../utils/fetchComAuth";

const PacoteOcorrencia = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [loteLocal, setLoteLocal] = useState(null);
  const [pecasPacote, setPecasPacote] = useState([]);
  const [selecionadas, setSelecionadas] = useState({});
  const [motivosPeca, setMotivosPeca] = useState({});
  const [motivos, setMotivos] = useState([]);

  useEffect(() => {
    fetchComAuth("/motivos-ocorrencias").then(setMotivos).catch(() => {});
    const lotes = JSON.parse(localStorage.getItem("lotesOcorrenciaLocal") || "[]");
    const lote = lotes.find((l) => l.id === parseInt(id));
    if (lote) {
      setLoteLocal(lote);
      const pecasComEdicoes = (lote.pacoteData.pecas || []).map((p) => {
        const dadosEdit = localStorage.getItem("ocedit_dados_" + p.id);
        return dadosEdit ? { ...p, ...JSON.parse(dadosEdit) } : p;
      });
      setPecasPacote(pecasComEdicoes);
      const sel = {};
      const motSel = {};
      (lote.pacoteData.pecas || []).forEach((p) => {
        sel[p.id] = false;
        motSel[p.id] = p.motivo_codigo || "";
      });
      setSelecionadas(sel);
      setMotivosPeca(motSel);
    }
  }, [id]);

  const salvarLotesLocais = (dados) => {
    localStorage.setItem("lotesOcorrenciaLocal", JSON.stringify(dados));
  };

  const excluirLoteLocal = (perguntar = true) => {
    if (perguntar && !window.confirm("Excluir este lote local?")) return;
    const lotes = JSON.parse(localStorage.getItem("lotesOcorrenciaLocal") || "[]");
    const novos = lotes.filter((l) => l.id !== parseInt(id));
    salvarLotesLocais(novos);
    navigate("/producao/ocorrencias");
  };

  const gerarOcorrencia = async () => {
    if (!loteLocal) return;
    let nextId = parseInt(localStorage.getItem("globalPecaIdProducao")) || 1;
    const idsOriginais = [];
    const pecas = pecasPacote
      .filter((p) => selecionadas[p.id])
      .map((p) => {
        const opsOc = localStorage.getItem("ocedit_op_" + p.id);
        const ops = opsOc
          ? JSON.parse(opsOc)
          : JSON.parse(localStorage.getItem("op_producao_" + p.id) || "[]");
        const dadosEdit = localStorage.getItem("ocedit_dados_" + p.id);
        const medidas = dadosEdit ? JSON.parse(dadosEdit) : {};
        const novoId = nextId++;
        idsOriginais.push(p.id);
        localStorage.setItem("op_producao_" + novoId, JSON.stringify(ops));
        const editFlag = localStorage.getItem("editado_peca_" + p.id) || "false";
        localStorage.setItem("editado_peca_" + novoId, editFlag);
        return {
          ...p,
          ...medidas,
          motivo_codigo: motivosPeca[p.id],
          operacoes: ops,
          id: novoId,
        };
      });
    localStorage.setItem("globalPecaIdProducao", nextId);
    if (pecas.length === 0) {
      alert("Selecione ao menos uma peça");
      return;
    }
    const resp = await fetchComAuth("/lotes-ocorrencias", {
      method: "POST",
      body: JSON.stringify({ lote: loteLocal.lote, pacote: loteLocal.pacote, pecas }),
    });
    if (resp?.erro) {
      alert(resp.erro);
      return;
    }
    alert(`OC ${String(resp.oc_numero).padStart(8, "0")} gerada`);
    const nomeLoteFinal = `${loteLocal.lote}_OC${resp.oc_numero}`;
    const lotesProd = JSON.parse(localStorage.getItem("lotesProducao") || "[]");
    lotesProd.push({
      nome: nomeLoteFinal,
      pacotes: [
        { nome_pacote: loteLocal.pacote, pecas },
      ],
    });
    localStorage.setItem("lotesProducao", JSON.stringify(lotesProd));
    idsOriginais.forEach((oldId) => {
      localStorage.removeItem("ocedit_op_" + oldId);
      localStorage.removeItem("ocedit_dados_" + oldId);
      localStorage.removeItem("editado_peca_" + oldId);
    });
    excluirLoteLocal(false);
  };

  if (!loteLocal) {
    return (
      <div className="p-6 space-y-2">
        <p>Lote local não encontrado.</p>
        <Button onClick={() => navigate("/producao/ocorrencias")}>Voltar</Button>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-4">
      <Button onClick={() => navigate("/producao/ocorrencias")}>Voltar aos Lotes</Button>
      <h2 className="text-xl font-semibold">
        Lote {loteLocal.lote} - Pacote {loteLocal.pacote}
      </h2>
      {pecasPacote.length > 0 && (
        <ul className="space-y-2">
          {pecasPacote.map((p) => {
            const editado = localStorage.getItem("editado_peca_" + p.id) === "true";
            return (
            <li key={p.id} className={`border p-2 rounded ${editado ? 'bg-yellow-100' : ''}`}>
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={!!selecionadas[p.id]}
                  onChange={(e) =>
                    setSelecionadas({ ...selecionadas, [p.id]: e.target.checked })
                  }
                />
                <span className="flex-grow">
                  ID {String(p.id).padStart(6, "0")} - {p.nome}
                </span>
                <select
                  className="border p-1"
                  value={motivosPeca[p.id] || ""}
                  onChange={(e) =>
                    setMotivosPeca({ ...motivosPeca, [p.id]: e.target.value })
                  }
                >
                  <option value="">Motivo</option>
                  {motivos.map((m) => (
                    <option key={m.codigo} value={m.codigo}>
                      {m.codigo}
                    </option>
                  ))}
                </select>
                <Button
                  onClick={() => {
                    const nomeLote = loteLocal.lote.split(/[/\\\\]/).pop();
                    navigate(`/producao/lote/${nomeLote}/peca/${p.id}`, {
                      state: { origem: "ocorrencia", ocId: loteLocal.id },
                    });
                  }}
                >
                  Editar
                </Button>
              </div>
            </li>
          );
        })}
        </ul>
      )}
      <div className="flex gap-2">
        <Button variant="destructive" onClick={excluirLoteLocal}>
          Excluir Lote Local
        </Button>
        <Button onClick={gerarOcorrencia}>Gerar arquivos finais da ocorrência</Button>
      </div>
    </div>
  );
};

export default PacoteOcorrencia;
