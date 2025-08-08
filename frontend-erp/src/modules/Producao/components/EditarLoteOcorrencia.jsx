import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Button } from "./ui/button";
import { fetchComAuth } from "../../../utils/fetchComAuth";

const EditarLoteOcorrencia = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [erro, setErro] = useState("");

  useEffect(() => {
    const carregar = async () => {
      try {
        const resp = await fetchComAuth("/lotes-ocorrencias");
        const lista = Array.isArray(resp?.lotes) ? resp.lotes : [];
        const lote = lista.find((l) => l.id === parseInt(id));
        if (!lote) {
          setErro("Lote de ocorrência não encontrado.");
          return;
        }
        const dadosPacote = await fetchComAuth(
          `/carregar-lote-final?pasta=${encodeURIComponent(lote.obj_key)}`
        );
        const pacoteData = (dadosPacote?.pacotes || [])[0] || { pecas: [] };

        const lotesLocais = JSON.parse(
          localStorage.getItem("lotesOcorrenciaLocal") || "[]"
        );
        const novo = {
          id: lote.id,
          lote: lote.lote,
          pacote: lote.pacote,
          pacoteData,
        };
        const idx = lotesLocais.findIndex((l) => l.id === lote.id);
        if (idx >= 0) {
          lotesLocais[idx] = novo;
        } else {
          lotesLocais.push(novo);
        }

        let maxId = 0;
        (pacoteData.pecas || []).forEach((p) => {
          if (p.id > maxId) maxId = p.id;
          if (p.operacoes) {
            localStorage.setItem(
              "op_producao_" + p.id,
              JSON.stringify(p.operacoes)
            );
          }
          localStorage.setItem("editado_peca_" + p.id, "false");
        });
        const nextId = Math.max(
          parseInt(localStorage.getItem("globalPecaIdProducao")) || 1,
          maxId + 1
        );
        localStorage.setItem("globalPecaIdProducao", nextId);
        localStorage.setItem(
          "lotesOcorrenciaLocal",
          JSON.stringify(lotesLocais)
        );
        navigate(`/producao/ocorrencias/pacote/${lote.id}`, { replace: true });
      } catch (e) {
        setErro("Erro ao carregar lote.");
      }
    };
    carregar();
  }, [id, navigate]);

  if (erro) {
    return (
      <div className="p-6 space-y-2">
        <p>{erro}</p>
        <Button onClick={() => navigate("/producao/ocorrencias")}>Voltar</Button>
      </div>
    );
  }

  return (
    <div className="p-6">
      <p>Carregando lote...</p>
    </div>
  );
};

export default EditarLoteOcorrencia;

