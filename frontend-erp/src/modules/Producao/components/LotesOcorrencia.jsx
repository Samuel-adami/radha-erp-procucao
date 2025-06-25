import React, { useEffect, useState } from "react";
import { Button } from "./ui/button";
import { fetchComAuth } from "../../../utils/fetchComAuth";
import CadastroMotivos from "./CadastroMotivos";

const LotesOcorrencia = () => {
  const [aba, setAba] = useState("lotes");
  const [lotes, setLotes] = useState([]);
  const [motivos, setMotivos] = useState([]);
  const [lotesProducao, setLotesProducao] = useState([]);
  const [loteSel, setLoteSel] = useState("");
  const [pacoteSel, setPacoteSel] = useState("");
  const [pacotesDisponiveis, setPacotesDisponiveis] = useState([]);
  const [pecasPacote, setPecasPacote] = useState([]);
  const [selecionadas, setSelecionadas] = useState({});
  const [motivosPeca, setMotivosPeca] = useState({});

  useEffect(() => {
    fetchComAuth("/lotes-ocorrencias").then(setLotes).catch(() => {});
    fetchComAuth("/motivos-ocorrencias").then(setMotivos).catch(() => {});
    const lp = JSON.parse(localStorage.getItem("lotesProducao") || "[]");
    setLotesProducao(lp);
  }, []);

  useEffect(() => {
    const loteObj = lotesProducao.find((l) => l.nome === loteSel);
    if (loteObj) {
      setPacotesDisponiveis(loteObj.pacotes || []);
    } else {
      setPacotesDisponiveis([]);
    }
    setPacoteSel("");
    setPecasPacote([]);
  }, [loteSel, lotesProducao]);

  useEffect(() => {
    const loteObj = lotesProducao.find((l) => l.nome === loteSel);
    const pacoteObj = loteObj?.pacotes?.[parseInt(pacoteSel)];
    if (pacoteObj) {
      setPecasPacote(pacoteObj.pecas || []);
      const sel = {};
      const motSel = {};
      (pacoteObj.pecas || []).forEach((p) => {
        sel[p.id] = true;
        motSel[p.id] = p.motivo_codigo || "";
      });
      setSelecionadas(sel);
      setMotivosPeca(motSel);
    } else {
      setPecasPacote([]);
      setSelecionadas({});
      setMotivosPeca({});
    }
  }, [pacoteSel, loteSel, lotesProducao]);

  const gerarOcorrencia = async () => {
    const pecas = pecasPacote
      .filter((p) => selecionadas[p.id])
      .map((p) => ({
        ...p,
        motivo_codigo: motivosPeca[p.id],
        operacoes: JSON.parse(
          localStorage.getItem("op_producao_" + p.id) || "[]"
        ),
      }));
    if (!loteSel || pacoteSel === "" || pecas.length === 0) {
      alert("Selecione lote, pacote e pelo menos uma peça");
      return;
    }
    const resp = await fetchComAuth("/lotes-ocorrencias", {
      method: "POST",
      body: JSON.stringify({ lote: loteSel, pacote: pacoteSel, pecas }),
    });
    if (resp?.erro) {
      alert(resp.erro);
      return;
    }
    alert(`OC ${resp.oc_numero} gerada`);
    fetchComAuth("/lotes-ocorrencias").then(setLotes).catch(() => {});
  };

  return (
    <div className="p-6 space-y-4">
      <div className="flex gap-2 mb-2">
        <Button
          variant={aba === "lotes" ? "default" : "outline"}
          onClick={() => setAba("lotes")}
        >
          Lotes de Ocorrência
        </Button>
        <Button
          variant={aba === "motivos" ? "default" : "outline"}
          onClick={() => setAba("motivos")}
        >
          Cadastro de Motivos
        </Button>
      </div>
      {aba === "motivos" ? (
        <CadastroMotivos />
      ) : (
        <>
          <div>
            <h2 className="text-xl font-semibold mb-2">Lotes de Ocorrência</h2>
            <ul className="space-y-2 mb-4">
              {lotes.map((l) => (
                <li key={l.id} className="border p-2 rounded">
                  OC {l.oc_numero} - Lote {l.lote} - Pacote {l.pacote}
                </li>
              ))}
            </ul>
          </div>

          <div className="border-t pt-4">
            <h3 className="font-semibold mb-2">
              Gerar novo Lote de Ocorrência
            </h3>
            <div className="flex gap-2 mb-4">
              <select
                className="border p-1"
                value={loteSel}
                onChange={(e) => setLoteSel(e.target.value)}
              >
                <option value="">Escolha o lote</option>
                {lotesProducao.map((l) => (
                  <option key={l.nome} value={l.nome}>
                    {l.nome}
                  </option>
                ))}
              </select>
              <select
                className="border p-1"
                value={pacoteSel}
                onChange={(e) => setPacoteSel(e.target.value)}
              >
                <option value="">Pacote</option>
                {pacotesDisponiveis.map((p, i) => (
                  <option key={i} value={i}>
                    {p.nome_pacote || `Pacote ${i + 1}`}
                  </option>
                ))}
              </select>
            </div>

            {pecasPacote.length > 0 && (
              <ul className="space-y-2 mb-4">
                {pecasPacote.map((p) => (
                  <li key={p.id} className="border p-2 rounded">
                    <div className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={!!selecionadas[p.id]}
                        onChange={(e) =>
                          setSelecionadas({
                            ...selecionadas,
                            [p.id]: e.target.checked,
                          })
                        }
                      />
                      <span className="flex-grow">
                        ID {String(p.id).padStart(6, "0")} - {p.nome}
                      </span>
                      <select
                        className="border p-1"
                        value={motivosPeca[p.id] || ""}
                        onChange={(e) =>
                          setMotivosPeca({
                            ...motivosPeca,
                            [p.id]: e.target.value,
                          })
                        }
                      >
                        <option value="">Motivo</option>
                        {motivos.map((m) => (
                          <option key={m.codigo} value={m.codigo}>
                            {m.codigo}
                          </option>
                        ))}
                      </select>
                    </div>
                  </li>
                ))}
              </ul>
            )}
            <Button onClick={gerarOcorrencia}>
              Gerar arquivos finais da ocorrência
            </Button>
          </div>
        </>
      )}
    </div>
  );
};

export default LotesOcorrencia;
