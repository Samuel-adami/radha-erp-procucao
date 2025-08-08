import React, { useState, useEffect } from "react";
import * as pdfjsLib from "pdfjs-dist";
import { fetchComAuth } from "../../utils/fetchComAuth";
import defaultDocs from "./defaultDocs";

pdfjsLib.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.js`;

function Treinamentos() {
  const [docs, setDocs] = useState([]);
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    const loadDocs = async () => {
      const resp = await fetchComAuth('/universidade-radha/documentos');
      const dinamicos = resp?.documentos || [];
      const lista = [...defaultDocs, ...dinamicos];
      const processed = await Promise.all(
        lista.map(async (doc) => {
          let content = "";
          let url = doc.url;
          let tipo = doc.tipo;
          try {
            if (typeof doc.id === 'number') {
              const arquivo = await fetchComAuth(doc.url || `/universidade-radha/documentos/${doc.id}/arquivo`, { raw: true });
              const blob = await arquivo.blob();
              url = window.URL.createObjectURL(blob);
              const ct = arquivo.headers.get('content-type') || '';
              tipo = ct.includes('pdf') ? 'pdf' : 'html';
              if (tipo === 'pdf') {
                const pdf = await pdfjsLib.getDocument({ data: await blob.arrayBuffer() }).promise;
                let text = '';
                for (let i = 1; i <= pdf.numPages; i++) {
                  const page = await pdf.getPage(i);
                  const txt = await page.getTextContent();
                  text += txt.items.map((item) => item.str).join(' ');
                }
                content = text;
              } else {
                const html = await blob.text();
                const tmp = document.createElement('div');
                tmp.innerHTML = html;
                content = tmp.textContent || '';
              }
            } else {
              if (tipo === 'pdf') {
                const pdf = await pdfjsLib.getDocument(url).promise;
                let text = '';
                for (let i = 1; i <= pdf.numPages; i++) {
                  const page = await pdf.getPage(i);
                  const txt = await page.getTextContent();
                  text += txt.items.map((item) => item.str).join(' ');
                }
                content = text;
              } else {
                const res = await fetch(url);
                const html = await res.text();
                const tmp = document.createElement('div');
                tmp.innerHTML = html;
                content = tmp.textContent || '';
              }
            }
          } catch (e) {
            console.error('Falha ao processar documento', doc.id || doc.url, e);
          }
          return { ...doc, url, tipo, content: content.toLowerCase() };
        })
      );
      setDocs(processed);
    };
    loadDocs();
  }, []);

  const filtered = docs.filter((doc) => {
    const q = query.toLowerCase();
    return doc.titulo.toLowerCase().includes(q) || doc.content.includes(q);
  });

  return (
    <div>
      <div className="mb-4">
        <input
          type="text"
          placeholder="Buscar..."
          className="border p-2 w-full"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filtered.map((doc) => (
          <div
            key={doc.id}
            className="p-4 border rounded shadow-sm bg-white"
          >
            <h3 className="font-semibold mb-2">{doc.titulo}</h3>
            <button
              className="text-blue-600 hover:underline mr-2"
              onClick={() => setSelected(doc)}
            >
              Abrir
            </button>
            <a
              className="text-blue-600 hover:underline"
              href={doc.url}
              download
            >
              Download
            </a>
          </div>
        ))}
      </div>
      {selected && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
          <div className="bg-white p-4 rounded shadow-lg w-11/12 h-5/6">
            <div className="flex justify-between mb-2">
              <h4 className="font-bold">{selected.titulo}</h4>
              <button
                onClick={() => setSelected(null)}
                className="text-red-600"
              >
                Fechar
              </button>
            </div>
            <iframe
              src={selected.url}
              className="w-full h-full"
              title={selected.titulo}
            />
          </div>
        </div>
      )}
    </div>
  );
}

export default Treinamentos;
