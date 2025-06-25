import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "./ui/button";
import { fetchComAuth } from "../../../utils/fetchComAuth";

const LotesOcorrencia = () => {
  const [lotes, setLotes] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    fetchComAuth("/lotes-ocorrencias").then(setLotes).catch(() => {});
  }, []);

  return (
    <div className="p-6">
      <div className="flex justify-between mb-4">
        <h2 className="text-xl font-semibold">Lotes de Ocorrência</h2>
        <Button onClick={() => navigate("motivos")}>Cadastro de Motivos</Button>
      </div>
      <ul className="space-y-2">
        {lotes.map((l) => (
          <li key={l.id} className="border p-2 rounded">
            OC {l.oc_numero} - Lote {l.lote} - Pacote {l.pacote}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default LotesOcorrencia;
