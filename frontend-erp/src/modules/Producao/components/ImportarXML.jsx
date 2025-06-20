import React, { useState } from "react";
import { fetchComAuth } from "../../../utils/fetchComAuth"; // Usando o utilitário corrigido

const ImportarXML = ({ onImportarPacote }) => {
  const [carregando, setCarregando] = useState(false);
  const [arquivosSelecionados, setArquivosSelecionados] = useState(0);

  const handleFileChange = (event) => {
    setArquivosSelecionados(event.target.files.length);
    handleUpload(event.target.files);
  };

  const handleUpload = async (files) => {
    if (!files.length) return;

    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      // O nome "files" deve corresponder ao que o backend espera
      formData.append("files", files[i]);
    }

    setCarregando(true);

    try {
      // URL completa apontando para o gateway, que redirecionará para o backend de produção
      const data = await fetchComAuth("/importar-xml", {
        method: "POST",
        body: formData,
        // Não é mais necessário definir headers aqui, fetchComAuth cuidará disso.
      });

      const pacotes = data?.pacotes || [];

      if (onImportarPacote && pacotes.length) {
        pacotes.forEach((p) => onImportarPacote(p));
      } else if (data?.erro) {
        alert(`Erro retornado pelo servidor: ${data.erro}`);
      } else {
        alert("Nenhum pacote válido encontrado nos arquivos importados.");
      }
    } catch (error) {
      console.error("Erro ao importar arquivos:", error);
      alert(`Erro na comunicação com o servidor: ${error.message}`);
    } finally {
      setCarregando(false);
      setArquivosSelecionados(0); // Limpa o contador após o upload
    }
  };

  return (
    <div className="my-4 p-4 border rounded-lg bg-gray-50">
      <label className="block font-semibold mb-2 text-gray-700">
        Importar Arquivos do Lote (XML, DXT, DXF, BPP)
      </label>
      <div className="flex items-center gap-4">
        <label className="cursor-pointer bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors">
          <span>Escolher arquivos</span>
          <input
            type="file"
            accept=".xml,.dxt,.dxf,.bpp,.txt"
            multiple
            onChange={handleFileChange}
            className="hidden" // Esconde o input padrão
            disabled={carregando}
          />
        </label>
        <span className="text-sm text-gray-600">
          {arquivosSelecionados > 0 ? `${arquivosSelecionados} arquivo(s) selecionado(s)` : "Nenhum arquivo selecionado"}
        </span>
      </div>
      {carregando && <p className="mt-2 text-sm text-blue-600">Carregando e processando arquivos...</p>}
    </div>
  );
};

export default ImportarXML;