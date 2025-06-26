import React, { useEffect, useState } from "react";
import { Button } from "./ui/button";
import { useNavigate, useLocation } from "react-router-dom";
import { fetchComAuth } from "../../../utils/fetchComAuth";
import CadastroMotivos from "./CadastroMotivos";

const espelharOperacoesY = (ops = [], largura) => {
  const L = parseFloat(largura);
  if (isNaN(L)) return ops;
  return ops.map((op) => {
    const novo = { ...op };
    if (novo.y !== undefined) {
      const y = parseFloat(novo.y);
      if (["Retângulo", "Linha"].includes(novo.tipo)) {
        const h = parseFloat(novo.largura || 0);
        novo.y = L - y - h;
      } else {
        novo.y = L - y;
      }
    }
    return novo;
  });
};

const LotesOcorrencia = () => {
  const [aba, setAba] = useState("lotes");
  const [lotes, setLotes] = useState([]);
  const [lotesProducao, setLotesProducao] = useState([]); // [{pasta,nome}]
  const [loteSel, setLoteSel] = useState("");
  const [pacoteSel, setPacoteSel] = useState("");
  const [pacotesDisponiveis, setPacotesDisponiveis] = useState([]);
  const [lotesLocais, setLotesLocais] = useState([]);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    fetchComAuth("/lotes-ocorrencias")
      .then((d) => {
        if (Array.isArray(d)) {
          setLotes(d);
        } else if (d && Array.isArray(d.lotes)) {
          setLotes(d.lotes);
        } else {
          setLotes([]);
        }
      })
      .catch(() => setLotes([]));
    fetchComAuth("/listar-lotes")
      .then((d) => {
        const lista = (d?.lotes || []).map((p) => ({
          pasta: p,
          nome: p.split(/[/\\\\]/).pop(),
        }));
        setLotesProducao(lista);
      })
      .catch(() => {});
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
    if (!loteSel) {
      setPacotesDisponiveis([]);
      setPacoteSel("");
      return;
    }
    fetchComAuth(`/carregar-lote-final?pasta=${encodeURIComponent(loteSel)}`)
      .then((d) => setPacotesDisponiveis(d?.pacotes || []))
      .catch(() => setPacotesDisponiveis([]));
    setPacoteSel("");
  }, [loteSel]);


  const salvarLotesLocais = (dados) => {
    setLotesLocais(dados);
    localStorage.setItem("lotesOcorrenciaLocal", JSON.stringify(dados));
  };

  const clonarPacote = () => {
    if (!loteSel || pacoteSel === "") {
      alert("Escolha lote e pacote");
      return;
    }
    const pacoteObj = pacotesDisponiveis[parseInt(pacoteSel)];
    if (!pacoteObj) return;
    let nextId = parseInt(localStorage.getItem("globalPecaIdProducao")) || 1;
    const copia = JSON.parse(JSON.stringify(pacoteObj));
    copia.pecas = (copia.pecas || []).map((p) => {
      const opsEspelhadas = espelharOperacoesY(p.operacoes || [], p.largura);
      const id = p.id !== undefined ? p.id : nextId++;
      if (p.operacoes) {
        localStorage.setItem(
          "op_producao_" + id,
          JSON.stringify(opsEspelhadas)
        );
      }
      return { ...p, operacoes: opsEspelhadas, id };
    });
    localStorage.setItem("globalPecaIdProducao", nextId);
    const loteId = Date.now();
    const nomeBase = loteSel.split(/[/\\]/).pop();
    const pacoteNome = pacoteObj.nome_pacote || `Pacote ${parseInt(pacoteSel) + 1}`;
    const novo = { id: loteId, lote: nomeBase, pacote: pacoteNome, pacoteData: copia };
    salvarLotesLocais([...lotesLocais, novo]);
    navigate(`pacote/${loteId}`);
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
                    OC {String(l.oc_numero).padStart(8, "0")} - {l.lote} - {l.pacote}
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
                    OC LOCAL {l.id} - {l.lote} - {l.pacote}
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
                  <option key={l.pasta} value={l.pasta}>
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

