import React, { useEffect, useState } from 'react';
import { fetchComAuth } from '../../../utils/fetchComAuth';

function PublicosAlvo() {
  const [publicos, setPublicos] = useState([]);
  const [nome, setNome] = useState('');
  const [descricao, setDescricao] = useState('');
  const [idadeMin, setIdadeMin] = useState('');
  const [idadeMax, setIdadeMax] = useState('');
  const [genero, setGenero] = useState('');
  const [interesses, setInteresses] = useState('');
  const [localizacao, setLocalizacao] = useState('');
  const [erro, setErro] = useState('');
  const [sucesso, setSucesso] = useState(false);

  const carregarPublicos = async () => {
    try {
      const resultado = await fetchComAuth('/publicos/');
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
      await fetchComAuth('/publicos/', {
        method: 'POST',
        body: JSON.stringify({
          nome,
          descricao,
          idade_min: idadeMin ? parseInt(idadeMin, 10) : null,
          idade_max: idadeMax ? parseInt(idadeMax, 10) : null,
          genero,
          interesses: interesses
            .split(',')
            .map((i) => i.trim())
            .filter(Boolean),
          localizacao,
        }),
      });
      setNome('');
      setDescricao('');
      setIdadeMin('');
      setIdadeMax('');
      setGenero('');
      setInteresses('');
      setLocalizacao('');
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
        <div className="flex gap-2 mb-2">
          <input
            type="number"
            className="w-full border rounded px-3 py-2"
            placeholder="Idade mínima"
            value={idadeMin}
            onChange={(e) => setIdadeMin(e.target.value)}
          />
          <input
            type="number"
            className="w-full border rounded px-3 py-2"
            placeholder="Idade máxima"
            value={idadeMax}
            onChange={(e) => setIdadeMax(e.target.value)}
          />
        </div>
        <input
          className="w-full border rounded px-3 py-2 mb-2"
          placeholder="Gênero"
          value={genero}
          onChange={(e) => setGenero(e.target.value)}
        />
        <input
          className="w-full border rounded px-3 py-2 mb-2"
          placeholder="Interesses (separados por vírgula)"
          value={interesses}
          onChange={(e) => setInteresses(e.target.value)}
        />
        <input
          className="w-full border rounded px-3 py-2 mb-4"
          placeholder="Localização"
          value={localizacao}
          onChange={(e) => setLocalizacao(e.target.value)}
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
        {publicos.map((p) => (
          <li key={p.id} className="p-4 bg-white shadow rounded">
            <strong>{p.nome}</strong> - {p.descricao}
            {p.idade_min && (
              <> | Idade: {p.idade_min} - {p.idade_max || '∞'}</>
            )}
            {p.genero && <> | Gênero: {p.genero}</>}
            {p.localizacao && <> | Localização: {p.localizacao}</>}
            {p.interesses && p.interesses.length > 0 && (
              <> | Interesses: {p.interesses.join(', ')}</>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default PublicosAlvo;
