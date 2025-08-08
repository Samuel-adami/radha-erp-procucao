import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Button } from "./ui/button";
import { fetchComAuth } from "../../../utils/fetchComAuth";

const PacoteOcorrencia = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [lote, setLote] = useState(null);
  const [pecasPacote, setPecasPacote] = useState([]);
  const [selecionadas, setSelecionadas] = useState({});
  const [motivosPeca, setMotivosPeca] = useState({});
  const [motivos, setMotivos] = useState([]);

  useEffect(() => {
    fetchComAuth("/motivos-ocorrencias").then(setMotivos).catch(() => {});
    fetchComAuth(`/lotes-ocorrencias/${id}`)
      .then((d) => {
        if (!d) {
          navigate("/producao/ocorrencias");
          return;
        }
        setLote(d);
        const pecas = d.pecas || [];
        setPecasPacote(pecas);
        const sel = {};
        const motSel = {};
        pecas.forEach((p) => {
          sel[p.id] = false;
          motSel[p.id] = p.motivo_codigo || "";
        });
        setSelecionadas(sel);
        setMotivosPeca(motSel);
      })
      .catch(() => navigate("/producao/ocorrencias"));
  }, [id, navigate]);

  const excluirPeca = async (pecaId) => {
    if (!window.confirm(`Excluir peça ID ${pecaId}?`)) return;
    const novas = pecasPacote.filter((p) => p.id !== pecaId);
    await fetchComAuth(`/lotes-ocorrencias/${id}`, {
      method: "PUT",
      body: JSON.stringify({ ...lote, pecas: novas }),
    }).catch(() => {});
    setPecasPacote(novas);
    const { [pecaId]: _, ...restSel } = selecionadas;
    const { [pecaId]: __, ...restMot } = motivosPeca;
    setSelecionadas(restSel);
    setMotivosPeca(restMot);
  };

  const excluirLote = async () => {
    if (!window.confirm("Excluir este lote?")) return;
    await fetchComAuth(`/lotes-ocorrencias/${id}`, { method: "DELETE" }).catch(() => {});
    navigate("/producao/ocorrencias");
  };

  const gerarOcorrencia = async () => {
    if (!lote) return;
    const pecas = pecasPacote
      .filter((p) => selecionadas[p.id])
      .map((p) => ({ ...p, motivo_codigo: motivosPeca[p.id] }));
    if (pecas.length === 0) {
      alert("Selecione ao menos uma peça");
      return;
    }
    const resp = await fetchComAuth("/lotes-ocorrencias", {
      method: "POST",
      body: JSON.stringify({ lote: lote.lote, pacote: lote.pacote, pecas }),
    }).catch(() => null);
    if (!resp || resp.erro) {
      alert(resp?.erro || "Erro ao gerar ocorrência");
      return;
    }
    alert(`OC ${String(resp.oc_numero).padStart(8, "0")} gerada`);
    navigate("/producao/ocorrencias");
  };

  if (!lote) {
    return (
      <div className="p-6 space-y-2">
        <p>Lote não encontrado.</p>
        <Button onClick={() => navigate("/producao/ocorrencias")}>Voltar</Button>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-4">
      <Button onClick={() => navigate("/producao/ocorrencias")}>Voltar aos Lotes</Button>
      <h2 className="text-xl font-semibold">
        Lote {lote.lote} - Pacote {lote.pacote}
      </h2>
      {pecasPacote.length > 0 && (
        <ul className="space-y-2">
          {pecasPacote.map((p) => (
            <li key={p.id} className="border p-2 rounded">
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={!!selecionadas[p.id]}
                  onChange={(e) =>
                    setSelecionadas({ ...selecionadas, [p.id]: e.target.checked })
                  }
                />
                <span className="flex-grow">
                  ID {String(p.id).padStart(6, "0")} ({p.codigo_peca}) - {p.nome} - {p.comprimento} x {p.largura}mm
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
                    const nomeLote = lote.lote.split(/[/\\\\]/).pop();
                    navigate(`/producao/lote/${nomeLote}/peca/${p.id}`, {
                      state: { origem: "ocorrencia", ocId: lote.id },
                    });
                  }}
                >
                  Editar
                </Button>
                <Button variant="destructive" onClick={() => excluirPeca(p.id)}>
                  Excluir
                </Button>
              </div>
            </li>
          ))}
        </ul>
      )}
      <div className="flex gap-2">
        <Button variant="destructive" onClick={excluirLote}>
          Excluir Lote
        </Button>
        <Button onClick={gerarOcorrencia}>Gerar arquivos finais da ocorrência</Button>
      </div>
    </div>
  );
};

export default PacoteOcorrencia;
