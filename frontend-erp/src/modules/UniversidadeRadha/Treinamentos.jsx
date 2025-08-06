import React, { useState, useEffect } from "react";
import * as pdfjsLib from "pdfjs-dist";

pdfjsLib.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.js`;

const docsList = [
  { title: "Guia PDF", url: "/treinamentos/guia.pdf", type: "pdf" },
  { title: "Introdução HTML", url: "/treinamentos/introducao.html", type: "html" },
];

function Treinamentos() {
  const [docs, setDocs] = useState([]);
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    const loadDocs = async () => {
      const processed = await Promise.all(
        docsList.map(async (doc) => {
          let content = "";
          try {
            if (doc.type === "pdf") {
              const pdf = await pdfjsLib.getDocument(doc.url).promise;
              let text = "";
              for (let i = 1; i <= pdf.numPages; i++) {
                const page = await pdf.getPage(i);
                const txt = await page.getTextContent();
                text += txt.items.map((item) => item.str).join(" ");
              }
              content = text;
            } else {
              const res = await fetch(doc.url);
              const html = await res.text();
              const tmp = document.createElement("div");
              tmp.innerHTML = html;
              content = tmp.textContent || "";
            }
          } catch (e) {
            console.error("Falha ao processar documento", doc.url, e);
          }
          return { ...doc, content: content.toLowerCase() };
        })
      );
      setDocs(processed);
    };
    loadDocs();
  }, []);

  const filtered = docs.filter((doc) => {
    const q = query.toLowerCase();
    return doc.title.toLowerCase().includes(q) || doc.content.includes(q);
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
            key={doc.url}
            className="p-4 border rounded shadow-sm bg-white"
          >
            <h3 className="font-semibold mb-2">{doc.title}</h3>
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
              <h4 className="font-bold">{selected.title}</h4>
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
              title={selected.title}
            />
          </div>
        </div>
      )}
    </div>
  );
}

export default Treinamentos;
