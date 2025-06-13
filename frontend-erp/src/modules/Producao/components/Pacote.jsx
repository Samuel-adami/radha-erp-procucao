import React, { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
// Caminho corrigido: de '@/components/ui/button' para './ui/button'
import { Button } from "./ui/button"; 

const Pacote = () => {
  const { nome, indice } = useParams();
  const navigate = useNavigate();
  const [filtroCampo, setFiltroCampo] = useState("nome");
  const [filtroTexto, setFiltroTexto] = useState("");

  const lotes = JSON.parse(localStorage.getItem("lotesProducao") || "[]"); // Usando "lotesProducao"
  const lote = lotes.find(l => l.nome === nome);
  const pacote = lote?.pacotes?.[parseInt(indice)];

  if (!pacote) return <p className="p-6">Pacote não encontrado.</p>;

  const excluirPeca = (id) => {
    const novaLista = pacote.pecas.filter(p => p.id !== id);
    lote.pacotes[parseInt(indice)].pecas = novaLista;
    localStorage.setItem("lotesProducao", JSON.stringify(lotes)); // Usando "lotesProducao"
    window.location.reload();
  };

  const pecasFiltradas = pacote.pecas.filter(p => {
    const campoValor = filtroCampo === "id" ? String(p.id) : (p[filtroCampo] || "");
    const valorPeca = String(p['codigo_peca'] || '').toLowerCase();

    return campoValor.toLowerCase().includes(filtroTexto.toLowerCase()) || 
           valorPeca.includes(filtroTexto.toLowerCase());
  });

  return (
    <div className="p-6">
      <Button className="mb-4" onClick={() => navigate(`/producao/lote/${nome}`)}>Voltar ao Lote</Button>
      <h2 className="text-lg font-semibold mb-4">Pacote: {pacote.titulo}</h2>

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
          placeholder="Contém..."
          value={filtroTexto}
          onChange={e => setFiltroTexto(e.target.value)}
        />
      </div>

      <ul className="space-y-2">
        {pecasFiltradas.map((p) => (
          <li key={p.id} className="border rounded p-3">
            <p><strong>ID {p.id} ({p.codigo_peca})</strong>: {p.nome} - {p.comprimento} x {p.largura} mm</p>
            <div className="mt-2 space-x-2">
              <Button onClick={() => navigate(`/producao/lote/<span class="math-inline">\{nome\}/peca/</span>{p.id}`)}>Editar</Button>
              <Button variant="destructive" onClick={() => excluirPeca(p.id)}>Excluir</Button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default Pacote;