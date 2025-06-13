import React, { useState } from "react";
// Importar fetchComAuth do diretório utils do frontend-erp
import { fetchComAuth } from "../../../utils/fetchComAuth";

const ImportarXML = ({ onImportarPacote }) => {
  const [carregando, setCarregando] = useState(false);

  const handleUpload = async (event) => {
    const files = event.target.files;
    if (!files.length) return;

    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append("files", files[i]); // Nome do campo deve bater com o backend
    }

    setCarregando(true);

    try {
      // Usando fetchComAuth e a URL correta do Gateway para o módulo de Produção
      const response = await fetchComAuth("http://localhost:8010/producao/importar-xml", {
        method: "POST",
        body: formData,
        // fetchComAuth já cuida dos headers e token, não precisamos passar aqui
        headers: {
          // 'Content-Type': 'multipart/form-data' não é necessário com FormData
          // Ele é definido automaticamente pelo navegador
        },
      });

      // fetchComAuth já verifica response.ok, então não precisamos de if (!response.ok)
      const data = response; // fetchComAuth já retorna o JSON parseado

      const pacotes = data.pacotes || [];

      if (onImportarPacote && pacotes.length) {
        pacotes.forEach((p) => onImportarPacote(p));
      } else {
        alert("Nenhum pacote encontrado no XML importado.");
      }
    } catch (error) {
      console.error("Erro ao importar XML:", error);
      alert(`Erro ao importar XML. Detalhes: ${error.message}. Verifique se o backend está rodando corretamente.`);
    } finally {
      setCarregando(false);
    }
  };

  return (
    <div className="my-4">
      <label className="block font-medium mb-2">Importar XML do Promob:</label>
      <input
        type="file"
        accept=".xml,.dxf,.dxt,.bpp,.txt"
        multiple
        onChange={handleUpload}
        className="border p-2"
      />
      {carregando && <p className="mt-2 text-sm text-gray-500">Carregando...</p>}
    </div>
  );
};

export default ImportarXML;