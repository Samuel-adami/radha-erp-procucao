import React, { useEffect, useState } from "react";
import { fetchComAuth } from "../../../utils/fetchComAuth";

const CadastroMotivos = () => {
  const [motivos, setMotivos] = useState([]);
  const [novo, setNovo] = useState({ codigo: "", descricao: "", tipo: "Interna", setor: "" });

  const carregar = () => {
    fetchComAuth("/motivos-ocorrencias").then(setMotivos).catch(() => {});
  };

  useEffect(() => {
    carregar();
  }, []);

  const salvar = async (e) => {
    e.preventDefault();
    await fetchComAuth("/motivos-ocorrencias", {
      method: "POST",
      body: JSON.stringify(novo),
    });
    setNovo({ codigo: "", descricao: "", tipo: "Interna", setor: "" });
    carregar();
  };

  const remover = async (codigo) => {
    if (!window.confirm("Excluir motivo?")) return;
    await fetchComAuth(`/motivos-ocorrencias/${codigo}`, { method: "DELETE" });
    carregar();
  };

  return (
    <div className="p-6">
      <h2 className="text-xl font-semibold mb-4">Cadastro de Motivos de Ocorrência</h2>
      <form onSubmit={salvar} className="space-x-2">
        <input className="border p-1" placeholder="Código" value={novo.codigo} onChange={(e) => setNovo({ ...novo, codigo: e.target.value })} />
        <input className="border p-1" placeholder="Descrição" value={novo.descricao} onChange={(e) => setNovo({ ...novo, descricao: e.target.value })} />
        <select className="border p-1" value={novo.tipo} onChange={(e) => setNovo({ ...novo, tipo: e.target.value })}>
          <option value="Interna">Interna</option>
          <option value="Externa">Externa</option>
        </select>
        <input className="border p-1" placeholder="Setor" value={novo.setor} onChange={(e) => setNovo({ ...novo, setor: e.target.value })} />
        <button className="bg-blue-600 text-white px-2" type="submit">Salvar</button>
      </form>
      <table className="mt-4 w-full text-sm">
        <thead>
          <tr>
            <th className="border px-2">Código</th>
            <th className="border px-2">Descrição</th>
            <th className="border px-2">Tipo</th>
            <th className="border px-2">Setor</th>
            <th className="border px-2"></th>
          </tr>
        </thead>
        <tbody>
          {motivos.map((m) => (
            <tr key={m.codigo}>
              <td className="border px-2">{m.codigo}</td>
              <td className="border px-2">{m.descricao}</td>
              <td className="border px-2">{m.tipo}</td>
              <td className="border px-2">{m.setor}</td>
              <td className="border px-2">
                <button className="text-red-500" onClick={() => remover(m.codigo)}>Excluir</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default CadastroMotivos;
