import React, { useState } from "react";

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
      const response = await fetch("http://localhost:8009/importar-xml", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Erro ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      const pacotes = data.pacotes || [];

      if (onImportarPacote && pacotes.length) {
        pacotes.forEach((p) => onImportarPacote(p));
      } else {
        alert("Nenhum pacote encontrado no XML importado.");
      }
    } catch (error) {
      console.error("Erro ao importar XML:", error);
      alert("Erro ao importar XML. Verifique se o backend está rodando corretamente.");
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
