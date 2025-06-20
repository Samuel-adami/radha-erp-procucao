import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Button } from "./ui/button";

const EditarFerragem = () => {
  const { nome, id } = useParams();
  const navigate = useNavigate();
  const [ferragem, setFerragem] = useState(null);
  const [quantidade, setQuantidade] = useState(1);
  const [substituir, setSubstituir] = useState("");

  useEffect(() => {
    const lotes = JSON.parse(localStorage.getItem("lotesProducao") || "[]");
    const lote = lotes.find(l => l.nome === nome);
    if (!lote) return;
    for (const p of lote.pacotes || []) {
      const f = (p.ferragens || []).find(x => x.id === parseInt(id));
      if (f) {
        setFerragem(f);
        setQuantidade(f.quantidade || 1);
        break;
      }
    }
  }, [nome, id]);

  const tipos = JSON.parse(localStorage.getItem("tiposFerragens") || "[]");

  const salvar = () => {
    const lotes = JSON.parse(localStorage.getItem("lotesProducao") || "[]");
    const lote = lotes.find(l => l.nome === nome);
    if (!lote) return;
    for (const pacote of lote.pacotes || []) {
      const idx = (pacote.ferragens || []).findIndex(x => x.id === parseInt(id));
      if (idx >= 0) {
        pacote.ferragens[idx].quantidade = quantidade;
        if (substituir) {
          pacote.ferragens[idx].descricao = substituir;
          pacote.ferragens[idx].nome = substituir;
        }
      }
    }
    localStorage.setItem("lotesProducao", JSON.stringify(lotes));
    navigate(`/producao/lote/${nome}/pacote/${lote.pacotes.findIndex(p => (p.ferragens||[]).some(x=>x.id===parseInt(id)))}`);
  };

  if (!ferragem) return <p className="p-6">Ferragem não encontrada.</p>;

  return (
    <div className="p-6 space-y-4">
      <h3 className="text-lg font-semibold">Editar Ferragem</h3>
      <p>ID {String(ferragem.id).padStart(6,'0')} - {ferragem.descricao || ferragem.nome}</p>
      <label className="block">Quantidade:
        <input type="number" className="input" value={quantidade} onChange={e => setQuantidade(parseInt(e.target.value))} />
      </label>
      {tipos.length > 0 && (
        <label className="block">Substituir por:
          <select className="input" value={substituir} onChange={e => setSubstituir(e.target.value)}>
            <option value="">-- manter --</option>
            {tipos.map(t => <option key={t} value={t}>{t}</option>)}
          </select>
        </label>
      )}
      <div className="space-x-2">
        <Button onClick={salvar}>Salvar</Button>
        <Button variant="outline" onClick={() => navigate(-1)}>Cancelar</Button>
      </div>
    </div>
  );
};

export default EditarFerragem;
