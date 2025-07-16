import React, { useState } from 'react';
import { fetchComAuth } from "../../../utils/fetchComAuth";

function baixarTexto(conteudo, nomeArquivo) {
  const blob = new Blob([conteudo], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = nomeArquivo;
  a.click();
  URL.revokeObjectURL(url);
}

function baixarImagem(src, nome) {
  const a = document.createElement('a');
  a.href = src;
  a.download = nome;
  a.click();
}

function NovaPublicacao() {
  const [tema, setTema] = useState('');
  const [objetivo, setObjetivo] = useState('');
  const [formato, setFormato] = useState('');
  const [quantidade, setQuantidade] = useState(1);
  const [resposta, setResposta] = useState('');
  const [erro, setErro] = useState('');
  const [gerarImagem, setGerarImagem] = useState(false);
  const [imagens, setImagens] = useState([]);

  const enviar = async () => {
    setErro('');
    setResposta('');
    setImagens([]);

    const dados = {
      tema,
      objetivo,
      formato,
      quantidade: parseInt(quantidade) || 1,
      id_assistant: 'asst_OuBtdCCByhjfqPFPZwMK6d9y'
    };

    try {
      const resultado = await fetchComAuth('/nova-publicacao/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(dados)
      });

      setResposta(resultado.publicacao);

      if (gerarImagem) {
        const prompts = [];
        const regex = /\*\*Prompt para imagem:\*\*\s*(.*)/g;
        let match;
        while ((match = regex.exec(resultado.publicacao)) !== null) {
          if (match[1]) prompts.push(match[1].trim());
        }
        if (prompts.length === 0) {
          prompts.push(resultado.publicacao);
        }

        const imagensGeradas = [];
        for (let i = 0; i < prompts.length; i++) {
          const resp = await fetchComAuth('/nova-publicacao/gerar-imagem', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt: prompts[i] })
          });
          imagensGeradas.push(resp.imagem);
        }
        setImagens(imagensGeradas);
      }
    } catch (err) {
      setErro(err.message || JSON.stringify(err));
    }
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Nova Publicação</h1>

      <input
        type="text"
        className="w-full border rounded px-3 py-2 mb-2"
        placeholder="Tema"
        value={tema}
        onChange={(e) => setTema(e.target.value)}
      />

      <select
        className="w-full border rounded px-3 py-2 mb-2"
        value={objetivo}
        onChange={(e) => setObjetivo(e.target.value)}
      >
        <option value="">Selecione o Objetivo</option>
        <option value="Engajamento">Engajamento</option>
        <option value="Reconhecimento de Marca">Reconhecimento de Marca</option>
        <option value="Conversões">Conversões</option>
        <option value="Lançamento de Produto">Lançamento de Produto</option>
      </select>

      <select
        className="w-full border rounded px-3 py-2 mb-2"
        value={formato}
        onChange={(e) => setFormato(e.target.value)}
      >
        <option value="">Selecione o Formato</option>
        <option value="post único">Post Único</option>
        <option value="post carrossel">Post Carrossel</option>
        <option value="reels">Reels</option>
        <option value="story">Story</option>
      </select>

      <input
        type="number"
        className="w-full border rounded px-3 py-2 mb-4"
        value={quantidade}
        onChange={(e) => setQuantidade(e.target.value)}
        min={1}
        placeholder="Quantidade"
      />

      <div className="mb-4">
        <label className="inline-flex items-center">
          <input
            type="checkbox"
            className="form-checkbox"
            checked={gerarImagem}
            onChange={(e) => setGerarImagem(e.target.checked)}
          />
          <span className="ml-2">Gerar imagem com IA</span>
        </label>
      </div>

      <button
        onClick={enviar}
        className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
      >
        Criar Publicação
      </button>

      {resposta && (
        <div className="mt-6 p-4 bg-green-100 text-green-900 whitespace-pre-line rounded">
          <div className="flex justify-between items-start">
            <div>
              <strong>Resposta:</strong><br />{resposta}
            </div>
            <button
              onClick={() => baixarTexto(resposta, 'publicacao.txt')}
              className="ml-4 text-sm text-blue-700 underline"
            >
              Baixar texto
            </button>
          </div>
        </div>
      )}

      {imagens.length > 0 && (
        <div className="mt-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {imagens.map((img, idx) => (
            <div key={idx} className="flex flex-col items-center">
              <img src={img} alt={`Imagem ${idx + 1}`} className="w-full rounded" />
              <button
                onClick={() => baixarImagem(img, `imagem_${idx + 1}.png`)}
                className="mt-1 text-sm text-blue-700 underline"
              >
                Baixar imagem
              </button>
            </div>
          ))}
        </div>
      )}

      {erro && (
        <div className="mt-4 p-4 bg-red-100 text-red-700 rounded">
          Erro: {erro}
        </div>
      )}
    </div>
  );
}

export default NovaPublicacao;
