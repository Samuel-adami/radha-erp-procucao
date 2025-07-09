import React, { useState, useRef, useEffect } from "react";
import { fetchComAuth } from "../../../utils/fetchComAuth";

function Chat({ usuarioLogado }) {
  const [mensagens, setMensagens] = useState([]);
  const [inputMensagem, setInputMensagem] = useState("");
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState("");
  const messagesEndRef = useRef(null);

  useEffect(() => {
    if (erro) {
      console.error("Erro no chat:", erro);
    }
  }, [erro]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(scrollToBottom, [mensagens]);

  const enviarMensagem = async (e) => {
    e.preventDefault();
    if (!inputMensagem.trim()) return;

    const novaMensagem = { remetente: "user", texto: inputMensagem };
    console.log("Enviando mensagem", novaMensagem);
    setMensagens((prevMensagens) => [...prevMensagens, novaMensagem]);
    setInputMensagem("");
    setErro("");
    setCarregando(true);

    try {
      // CORRIGIDO: Removido usuarioLogado.token da chamada, fetchComAuth já cuida disso
      const respostaBackend = await fetchComAuth('/chat/', {
        method: 'POST',
        body: JSON.stringify({ mensagem: inputMensagem, id_assistant: 'asst_OuBtdCCByhjfqPFPZwMK6d9y' }),
      });
      console.log('Resposta do backend', respostaBackend);

      if (!respostaBackend || !respostaBackend.resposta) {
        throw new Error('Resposta inválida do servidor');
      }

      const respostaAI = { remetente: "ai", texto: respostaBackend.resposta };
      setMensagens((prevMensagens) => [...prevMensagens, respostaAI]);
    } catch (error) {
      console.error("Erro ao enviar mensagem:", error);

      setErro(error?.message || String(error));

      setMensagens((prevMensagens) => [
        ...prevMensagens,
        { remetente: "ai", texto: "Desculpe, houve um erro ao processar sua solicitação." },
      ]);
    } finally {
      setCarregando(false);
    }
  };

  return (
    <div className="flex flex-col h-[70vh] bg-white rounded shadow-md">
      <div className="flex-grow overflow-y-auto p-4 space-y-4">
        {mensagens.length === 0 && (
          <p className="text-center text-gray-500 mt-10">
            Olá! Como posso ajudar hoje com sua estratégia de marketing?
          </p>
        )}
        {mensagens.map((msg, index) => (
          <div
            key={index}
            className={`flex ${
              msg.remetente === "user" ? "justify-end" : "justify-start"
            }`}
          >
            <div
              className={`max-w-[70%] p-3 rounded-lg ${
                msg.remetente === "user"
                  ? "bg-blue-500 text-white"
                  : "bg-gray-200 text-gray-800"
              }`}
            >
              <p className="whitespace-pre-wrap">{msg.texto}</p>
            </div>
          </div>
        ))}
        {carregando && (
          <div className="flex justify-start">
            <div className="max-w-[70%] p-3 rounded-lg bg-gray-200 text-gray-800">
              <p>Digitando...</p>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      {erro && (
        <div className="p-2 text-sm text-red-700 bg-red-100 rounded mx-4">
          {erro}
        </div>
      )}

      <form onSubmit={enviarMensagem} className="p-4 border-t flex items-center">
        <input
          type="text"
          value={inputMensagem}
          onChange={(e) => setInputMensagem(e.target.value)}
          className="flex-grow input mr-2"
          placeholder="Digite sua mensagem..."
          disabled={carregando}
        />
        <button
          type="submit"
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
          disabled={carregando}
        >
          Enviar
        </button>
      </form>
    </div>
  );
}
export default Chat;