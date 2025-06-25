import React, { useEffect, useState } from "react";
import { Button } from "./ui/button";
import { useNavigate, useLocation } from "react-router-dom";
import { fetchComAuth } from "../../../utils/fetchComAuth";
import CadastroMotivos from "./CadastroMotivos";

const LotesOcorrencia = () => {
  const [aba, setAba] = useState("lotes");
  const [lotes, setLotes] = useState([]);
  const [lotesProducao, setLotesProducao] = useState([]);
  const [loteSel, setLoteSel] = useState("");
  const [pacoteSel, setPacoteSel] = useState("");
  const [pacotesDisponiveis, setPacotesDisponiveis] = useState([]);
  const [lotesLocais, setLotesLocais] = useState([]);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    fetchComAuth("/lotes-ocorrencias").then(setLotes).catch(() => {});
    const lp = JSON.parse(localStorage.getItem("lotesProducao") || "[]");
    setLotesProducao(lp);
    const loc = JSON.parse(localStorage.getItem("lotesOcorrenciaLocal") || "[]");
    setLotesLocais(loc);
  }, []);

  useEffect(() => {
    const id = location.state?.ocId;
    if (id) {
      editarLoteLocal(id);
      navigate('.', { replace: true, state: {} });
    }
  }, [location.state]);

  useEffect(() => {
    const loteObj = lotesProducao.find((l) => l.nome === loteSel);
    if (loteObj) {
      setPacotesDisponiveis(loteObj.pacotes || []);
    } else {
      setPacotesDisponiveis([]);
    }
    setPacoteSel("");
  }, [loteSel, lotesProducao]);


  const salvarLotesLocais = (dados) => {
    setLotesLocais(dados);
    localStorage.setItem("lotesOcorrenciaLocal", JSON.stringify(dados));
  };

  const clonarPacote = () => {
    if (!loteSel || pacoteSel === "") {
      alert("Escolha lote e pacote");
      return;
    }
    const loteObj = lotesProducao.find((l) => l.nome === loteSel);
    const pacoteObj = loteObj?.pacotes?.[parseInt(pacoteSel)];
    if (!pacoteObj) return;
    const copia = JSON.parse(JSON.stringify(pacoteObj));
    const id = Date.now();
    const novo = { id, lote: loteSel, pacote: pacoteSel, pacoteData: copia };
    salvarLotesLocais([...lotesLocais, novo]);
    navigate(`pacote/${id}`);
  };

  const editarLoteLocal = (id) => {
    const l = lotesLocais.find((x) => x.id === id);
    if (!l) return;
    navigate(`pacote/${id}`);
  };

  const excluirLoteLocal = (id) => {
    if (!window.confirm("Excluir este lote local?")) return;
    const novos = lotesLocais.filter((l) => l.id !== id);
    salvarLotesLocais(novos);
  };


  const excluirLote = async (id) => {
    if (!window.confirm("Excluir este lote de ocorrência?")) return;
    const resp = await fetchComAuth(`/lotes-ocorrencias/${id}`, {
      method: "DELETE",
    }).catch(() => ({}));
    if (resp?.erro) {
      alert(resp.erro);
      return;
    }
    setLotes(lotes.filter((l) => l.id !== id));
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
                <li key={l.id} className="border p-2 rounded flex justify-between items-center gap-2">
                  <span>
                    OC {l.oc_numero} - Lote {l.lote} - Pacote {l.pacote}
                  </span>
                  <div className="space-x-2">
                    <Button size="sm" onClick={() => navigate(`ocorrencias/editar/${l.id}`)}>Editar</Button>
                    <Button
                      size="sm"
                      variant="destructive"
                      onClick={() => excluirLote(l.id)}
                    >
                      Excluir
                    </Button>
                  </div>
                </li>
              ))}
              {lotesLocais.map((l) => (
                <li key={l.id} className="border p-2 rounded flex justify-between items-center gap-2 bg-gray-50">
                  <span>
                    OC LOCAL {l.id} - Lote {l.lote} - Pacote {l.pacote}
                  </span>
                  <div className="space-x-2">
                    <Button size="sm" onClick={() => editarLoteLocal(l.id)}>Editar</Button>
                    <Button
                      size="sm"
                      variant="destructive"
                      onClick={() => excluirLoteLocal(l.id)}
                    >
                      Excluir
                    </Button>
                  </div>
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
              <Button onClick={clonarPacote}>Copiar Pacote</Button>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default LotesOcorrencia;

