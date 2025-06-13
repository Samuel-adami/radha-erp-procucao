import React, { useState } from 'react';
import { fetchComAuth } from "../../../utils/fetchComAuth";

function Chat({ usuarioLogado }) {
  const [mensagem, setMensagem] = useState('');
  const [conversas, setConversas] = useState([]);
  const [erro, setErro] = useState('');

  const id_assistant = "asst_OuBtdCCByhjfqPFPZwMK6d9y";

  const enviarMensagem = async () => {
    if (!mensagem.trim()) return;

    const novaConversa = { pergunta: mensagem, resposta: '...' };
    setConversas([...conversas, novaConversa]);
    setMensagem('');
    setErro('');

    try {
      const resultado = await fetchComAuth('/chat', {
        method: 'POST',
        body: JSON.stringify({ mensagem, id_assistant })
      }, usuarioLogado.token);

      setConversas((prev) => {
        const atualizadas = [...prev];
        atualizadas[atualizadas.length - 1].resposta = resultado.resposta || 'Sem resposta';
        return atualizadas;
      });
    } catch (err) {
      setConversas((prev) => {
        const atualizadas = [...prev];
        atualizadas[atualizadas.length - 1].resposta = `Erro: ${err.message}`;
        return atualizadas;
      });
    }
  };

  const baixarConversa = () => {
    const conteudo = conversas
      .map((c, i) => `🔹 Pergunta ${i + 1}: ${c.pergunta}\n🔸 Resposta ${i + 1}: ${c.resposta}\n`)
      .join('\n');

    const blob = new Blob([conteudo], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'conversa_radha.txt';
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Pergunte algo à Sara</h1>

      <div className="space-y-4 mb-4">
        {conversas.map((c, index) => (
          <div key={index} className="bg-gray-100 p-4 rounded">
            <p><strong>Pergunta:</strong> {c.pergunta}</p>
            <p className="mt-2 text-purple-700"><strong>Resposta:</strong> {c.resposta}</p>
          </div>
        ))}
      </div>

      <textarea
        className="w-full border rounded p-2 mb-2"
        rows="4"
        value={mensagem}
        onChange={(e) => setMensagem(e.target.value)}
        placeholder="Digite sua mensagem"
      />

      <div className="flex items-center gap-4">
        <button
          onClick={enviarMensagem}
          className="bg-purple-900 text-white px-4 py-2 rounded hover:bg-blue-700"
        >
          Enviar
        </button>

        <button
          onClick={baixarConversa}
          className="bg-gray-600 text-white px-4 py-2 rounded hover:bg-gray-700"
        >
          Baixar conversa
        </button>
      </div>

      {erro && (
        <div className="mt-4 p-4 bg-red-100 text-red-700 rounded">
          <strong>Erro:</strong> {erro}
        </div>
      )}
    </div>
  );
}

export default Chat;
