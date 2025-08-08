import React, { useState, useEffect } from 'react';
import { fetchComAuth } from '../../utils/fetchComAuth';
import defaultDocs from './defaultDocs';

function GerenciarConteudos() {
  const [titulo, setTitulo] = useState('');
  const [autor, setAutor] = useState('');
  const [data, setData] = useState('');
  const [arquivo, setArquivo] = useState(null);
  const [documentos, setDocumentos] = useState([]);

  const carregarDocumentos = async () => {
    try {
      const resp = await fetchComAuth('/universidade-radha/documentos');
      const dinamicos = resp?.documentos || [];
      setDocumentos([...defaultDocs, ...dinamicos]);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    carregarDocumentos();
  }, []);

  const enviar = async (e) => {
    e.preventDefault();
    if (!arquivo) return;
    const fd = new FormData();
    fd.append('titulo', titulo);
    fd.append('autor', autor);
    fd.append('data', data);
    fd.append('arquivo', arquivo);
    try {
      await fetchComAuth('/universidade-radha/documentos', {
        method: 'POST',
        body: fd,
      });

      setTitulo('');
      setAutor('');
      setData('');
      setArquivo(null);
      e.target.reset && e.target.reset();

      await carregarDocumentos();
      window.dispatchEvent(new Event('documentosAtualizados'));
    } catch (e) {
      console.error(e);
    }
  };

  const visualizar = async (doc) => {
    try {
      if (doc.url) {
        window.open(doc.url, '_blank');
        return;
      }
      const resp = await fetchComAuth(`/universidade-radha/documentos/${doc.id}/arquivo`, { raw: true });
      const blob = await resp.blob();
      const url = window.URL.createObjectURL(blob);
      window.open(url, '_blank');
    } catch (e) {
      console.error(e);
    }
  };

  const excluir = async (doc) => {
    if (!window.confirm('Deseja realmente excluir este documento?')) return;
    try {
      if (doc.url) {
        setDocumentos((prev) => prev.filter((d) => d.id !== doc.id));
        window.dispatchEvent(new Event('documentosAtualizados'));
        return;
      }
      await fetchComAuth(`/universidade-radha/documentos/${doc.id}`, { method: 'DELETE' });
      await carregarDocumentos();
      window.dispatchEvent(new Event('documentosAtualizados'));
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div>
      <form onSubmit={enviar} className="space-y-2 mb-6">
        <div>
          <label className="block text-sm">Título</label>
          <input value={titulo} onChange={e => setTitulo(e.target.value)} className="border p-1 w-full" required />
        </div>
        <div>
          <label className="block text-sm">Autor</label>
          <input value={autor} onChange={e => setAutor(e.target.value)} className="border p-1 w-full" required />
        </div>
        <div>
          <label className="block text-sm">Data</label>
          <input type="date" value={data} onChange={e => setData(e.target.value)} className="border p-1" required />
        </div>
        <div>
          <label className="block text-sm">Arquivo (PDF ou HTML)</label>
          <input type="file" accept=".pdf,.html" onChange={e => setArquivo(e.target.files[0])} required />
        </div>
        <button type="submit" className="bg-blue-600 text-white px-4 py-1 rounded">Enviar</button>
      </form>

      {documentos.length > 0 ? (
        <table className="w-full text-left border">
          <thead>
            <tr className="bg-gray-200">
              <th className="p-2">Título</th>
              <th className="p-2">Autor</th>
              <th className="p-2">Data</th>
              <th className="p-2">Ações</th>
            </tr>
          </thead>
          <tbody>
            {documentos.map((doc) => (
              <tr key={doc.id} className="border-t">
                <td className="p-2">{doc.titulo}</td>
                <td className="p-2">{doc.autor}</td>
                <td className="p-2">{doc.data}</td>
                <td className="p-2 space-x-2">
                  <button onClick={() => visualizar(doc)} className="text-blue-600 underline">Visualizar</button>
                  <button onClick={() => excluir(doc)} className="text-red-600 underline">Excluir</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <div>Nenhum documento cadastrado.</div>
      )}
    </div>
  );
}

export default GerenciarConteudos;
