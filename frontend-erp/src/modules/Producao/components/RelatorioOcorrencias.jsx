import React, { useEffect, useState } from "react";
import { fetchComAuth } from "../../../utils/fetchComAuth";

const RelatorioOcorrencias = () => {
  const [filtro, setFiltro] = useState({ data_inicio: "", data_fim: "", motivo: "", tipo: "", setor: "" });
  const [dados, setDados] = useState([]);
  const [motivos, setMotivos] = useState([]);

  useEffect(() => {
    fetchComAuth("/motivos-ocorrencias").then(setMotivos).catch(() => {});
  }, []);

  const consultar = async () => {
    const params = new URLSearchParams();
    Object.entries(filtro).forEach(([k, v]) => {
      if (v) params.append(k, v);
    });
    const res = await fetchComAuth(`/relatorio-ocorrencias?${params.toString()}`);
    setDados(res || []);
  };

  return (
    <div className="p-6">
      <h2 className="text-xl font-semibold mb-4">Relatório de Ocorrências</h2>
      <div className="flex flex-wrap gap-2 mb-4 text-sm items-end">
        <div>
          <label className="block">De:</label>
          <input type="date" className="border p-1" value={filtro.data_inicio} onChange={(e) => setFiltro({ ...filtro, data_inicio: e.target.value })} />
        </div>
        <div>
          <label className="block">Até:</label>
          <input type="date" className="border p-1" value={filtro.data_fim} onChange={(e) => setFiltro({ ...filtro, data_fim: e.target.value })} />
        </div>
        <div>
          <label className="block">Motivo:</label>
          <select className="border p-1" value={filtro.motivo} onChange={(e) => setFiltro({ ...filtro, motivo: e.target.value })}>
            <option value="">Todos</option>
            {motivos.map((m) => (
              <option key={m.codigo} value={m.codigo}>{m.codigo}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block">Tipo:</label>
          <select className="border p-1" value={filtro.tipo} onChange={(e) => setFiltro({ ...filtro, tipo: e.target.value })}>
            <option value="">Todos</option>
            <option value="Interna">Interna</option>
            <option value="Externa">Externa</option>
          </select>
        </div>
        <div>
          <label className="block">Setor:</label>
          <input className="border p-1" value={filtro.setor} onChange={(e) => setFiltro({ ...filtro, setor: e.target.value })} />
        </div>
        <button className="bg-blue-600 text-white px-2 h-8" onClick={consultar}>Filtrar</button>
      </div>
      <table className="w-full text-sm">
        <thead>
          <tr>
            <th className="border px-2">OC</th>
            <th className="border px-2">Lote</th>
            <th className="border px-2">Pacote</th>
            <th className="border px-2">Peça</th>
            <th className="border px-2">Motivo</th>
            <th className="border px-2">Tipo</th>
            <th className="border px-2">Setor</th>
          </tr>
        </thead>
        <tbody>
          {dados.map((d, i) => (
            <tr key={i}>
              <td className="border px-2">{String(d.oc_numero).padStart(8, '0')}</td>
              <td className="border px-2">{d.lote}</td>
              <td className="border px-2">{d.pacote}</td>
              <td className="border px-2">{d.descricao_peca}</td>
              <td className="border px-2">{d.motivo_codigo}</td>
              <td className="border px-2">{d.tipo}</td>
              <td className="border px-2">{d.setor}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default RelatorioOcorrencias;
