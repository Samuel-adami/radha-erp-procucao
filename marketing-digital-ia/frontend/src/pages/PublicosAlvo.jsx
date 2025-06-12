import React, { useEffect, useState } from 'react';
import { fetchComAuth } from '../utils/fetchComAuth';

function PublicosAlvo() {
  const [publicos, setPublicos] = useState([]);
  const [nome, setNome] = useState('');
  const [descricao, setDescricao] = useState('');
  const [erro, setErro] = useState('');
  const [sucesso, setSucesso] = useState(false);

  const carregarPublicos = async () => {
    try {
      const resultado = await fetchComAuth('/publicos');
      setPublicos(resultado);
    } catch (err) {
      setErro(err.message);
    }
  };

  useEffect(() => {
    carregarPublicos();
  }, []);

  const adicionarPublico = async () => {
    try {
      await fetchComAuth('/publicos', {
        method: 'POST',
        body: JSON.stringify({ nome, descricao })
      });
      setNome('');
      setDescricao('');
      setErro('');
      setSucesso(true);
      carregarPublicos();
    } catch (err) {
      setErro(err.message);
      setSucesso(false);
    }
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Público Alvo</h1>

      <div className="mb-6">
        <input
          className="w-full border rounded px-3 py-2 mb-2"
          placeholder="Nome"
          value={nome}
          onChange={(e) => setNome(e.target.value)}
        />
        <textarea
          className="w-full border rounded px-3 py-2 mb-2"
          placeholder="Descrição"
          value={descricao}
          onChange={(e) => setDescricao(e.target.value)}
          rows="3"
        />
        <button
          onClick={adicionarPublico}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
        >
          Adicionar Público
        </button>

        {sucesso && (
          <div className="mt-4 p-4 bg-green-100 text-green-800 rounded">
            Público adicionado com sucesso!
          </div>
        )}

        {erro && (
          <div className="mt-4 p-4 bg-red-100 text-red-700 rounded">
            Erro: {erro}
          </div>
        )}
      </div>

      <ul className="space-y-2">
        {publicos.map((p, index) => (
          <li key={index} className="p-4 bg-white shadow rounded">
            <strong>{p.nome}</strong> - {p.descricao}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default PublicosAlvo;
