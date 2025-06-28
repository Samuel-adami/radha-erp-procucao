import React, { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Button } from "./ui/button";

const Pacote = () => {
  const { nome, indice } = useParams();
  const navigate = useNavigate();
  const [filtroCampo, setFiltroCampo] = useState("nome");
  const [filtroTexto, setFiltroTexto] = useState("");
  const getPacoteFromStorage = () => {
    const lotes = JSON.parse(localStorage.getItem("lotesProducao") || "[]");
    const lote = lotes.find(l => l.nome === nome);
    return lote?.pacotes?.[parseInt(indice)];
  };

  const [pacote, setPacote] = useState(getPacoteFromStorage());

  if (!pacote) {
    return <p className="p-6">Pacote não encontrado ou dados inválidos.</p>;
  }

  const excluirPeca = (id) => {
    if (!window.confirm(`Tem certeza de que deseja excluir a peça com ID ${id}?`)) return;

    const lotes = JSON.parse(localStorage.getItem("lotesProducao") || "[]");
    const loteAlvo = lotes.find(l => l.nome === nome);
    if (!loteAlvo) return;

    const pacoteAlvo = loteAlvo.pacotes[parseInt(indice)];
    if (!pacoteAlvo || !pacoteAlvo.pecas) return;

    // Filtra para remover a peça
    pacoteAlvo.pecas = pacoteAlvo.pecas.filter(p => p.id !== id);

    // Salva a estrutura de lotes inteira de volta no localStorage
    localStorage.setItem("lotesProducao", JSON.stringify(lotes));
    
    // Atualiza o estado local para forçar a re-renderização
    setPacote({ ...pacoteAlvo });
  };

  const excluirFerragem = (id) => {
    if (!window.confirm(`Excluir ferragem ID ${id}?`)) return;
    const lotes = JSON.parse(localStorage.getItem("lotesProducao") || "[]");
    const loteAlvo = lotes.find(l => l.nome === nome);
    if (!loteAlvo) return;
    const pacoteAlvo = loteAlvo.pacotes[parseInt(indice)];
    if (!pacoteAlvo) return;
    pacoteAlvo.ferragens = (pacoteAlvo.ferragens || []).filter(f => f.id !== id);
    localStorage.setItem("lotesProducao", JSON.stringify(lotes));
    setPacote({ ...pacoteAlvo });
  };

  const pecasFiltradas = (pacote.pecas || []).filter(p => {
    const textoBusca = filtroTexto.toLowerCase();
    const valorCampo = p[filtroCampo] ? String(p[filtroCampo]).toLowerCase() : "";
    const codigoPeca = p['codigo_peca'] ? String(p['codigo_peca']).toLowerCase() : "";

    return valorCampo.includes(textoBusca) || codigoPeca.includes(textoBusca);
  });

  return (
    <div className="p-6">
      <Button className="mb-4" onClick={() => navigate(`/producao/lote/${nome}`)}>Voltar ao Lote</Button>
      {/* CORREÇÃO: Usando nome_pacote que vem do backend em vez de titulo */}
      <h2 className="text-lg font-semibold mb-4">Pacote: {pacote.nome_pacote || `Pacote ${parseInt(indice) + 1}`}</h2>

      <div className="flex gap-2 mt-4 mb-2">
        <select
          className="input w-40"
          value={filtroCampo}
          onChange={e => setFiltroCampo(e.target.value)}
        >
          <option value="nome">Descrição</option>
          <option value="observacoes">Observação</option>
          <option value="id">ID</option>
          <option value="codigo_peca">Código da Peça</option>
        </select>
        <input
          className="input flex-grow"
          placeholder="Filtrar peças..."
          value={filtroTexto}
          onChange={e => setFiltroTexto(e.target.value)}
        />
      </div>

      <ul className="space-y-2">
        {pecasFiltradas.map((p) => {
          const ops = JSON.parse(localStorage.getItem("op_producao_" + p.id) || "[]");
          const editado = ops.length > 0;
          return (
            <li key={p.id} className={`border rounded p-3 ${editado ? 'bg-yellow-100' : ''}`}>
              <p><strong>ID {String(p.id).padStart(6,'0')} ({p.codigo_peca})</strong>: {p.nome} - {p.comprimento} x {p.largura} mm</p>
              <div className="mt-2 space-x-2">
                {/* CORREÇÃO: Sintaxe de navegação para a peça corrigida */}
                <Button onClick={() => navigate(`/producao/lote/${nome}/peca/${p.id}`, { state: { pacoteIndex: indice } })}>Editar</Button>
                <Button variant="destructive" onClick={() => excluirPeca(p.id)}>Excluir</Button>
              </div>
            </li>
          );
        })}
      </ul>

      {pacote.ferragens && pacote.ferragens.length > 0 && (
        <div className="mt-8">
          <h3 className="font-semibold mb-2">Ferragens e Acessórios</h3>
          <ul className="space-y-2">
            {pacote.ferragens.map(f => (
              <li key={f.id} className="border rounded p-3 flex justify-between">
                <span><strong>ID {String(f.id).padStart(6,'0')}</strong>: {f.descricao || f.nome} - {f.quantidade}</span>
                <div className="space-x-2">
                  <Button onClick={() => navigate(`/producao/lote/${nome}/ferragem/${f.id}`)}>Editar</Button>
                  <Button variant="destructive" onClick={() => excluirFerragem(f.id)}>Excluir</Button>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default Pacote;
