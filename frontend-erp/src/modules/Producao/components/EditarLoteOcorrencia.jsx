import React from "react";
import { useParams } from "react-router-dom";
import { Button } from "./ui/button";

const EditarLoteOcorrencia = () => {
  const { id } = useParams();
  return (
    <div className="p-6 space-y-2">
      <h3 className="text-lg font-semibold">Editar Lote de Ocorrência {id}</h3>
      <p>Funcionalidade em desenvolvimento.</p>
      <Button onClick={() => window.history.back()}>Voltar</Button>
    </div>
  );
};

export default EditarLoteOcorrencia;
