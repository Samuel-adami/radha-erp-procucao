import React, { useEffect, useState } from "react";
import { fetchComAuth } from "../../../utils/fetchComAuth";
import { Button } from "./ui/button";

const modelo = {
  id: null,
  chapa_id: "",
  descricao: "",
  comprimento: "",
  largura: "",
  origem: "",
};

const EstoqueChapas = () => {
  const [itens, setItens] = useState([]);
  const [chapas, setChapas] = useState([]);
  const [form, setForm] = useState(modelo);

  const carregar = async () => {
    const dados = await fetchComAuth("/chapas-estoque");
    if (Array.isArray(dados)) setItens(dados);
    const ch = await fetchComAuth("/chapas");
    if (Array.isArray(ch)) setChapas(ch);
  };

  useEffect(() => { carregar(); }, []);

  const handle = campo => e => setForm({ ...form, [campo]: e.target.value });

  const handleChapa = e => {
    const id = e.target.value;
    const c = chapas.find(ch => String(ch.id) === String(id));
    setForm({ ...form, chapa_id: id, custo_m2: c?.custo_m2 || "" });
  };

  const editar = item => {
    setForm({
      id: item.id,
      chapa_id: item.chapa_id || "",
      descricao: item.descricao || "",
      comprimento: item.comprimento || "",
      largura: item.largura || "",
      custo_m2: item.custo_m2 || "",
      origem: item.origem || "",
    });
  };

  const salvar = async () => {
    if (form.id) {
      const senha = window.prompt('Digite sua senha para salvar');
      if (!senha) return;
      const usuario = JSON.parse(localStorage.getItem('usuario') || '{}');
      try {
        const auth = await fetchComAuth('/auth/login', { method: 'POST', body: JSON.stringify({ username: usuario.username, password: senha }) });
        if (!['Diretor','Coordenador','Supervisor','Gerente'].includes(auth.usuario?.cargo)) {
          alert('Usuário sem permissão');
          return;
        }
      } catch (err) {
        alert('Senha incorreta');
        return;
      }
    }
    await fetchComAuth("/chapas-estoque", { method: "POST", body: JSON.stringify(form) });
    setForm(modelo);
    carregar();
  };

  const remover = async id => {
    if (!window.confirm("Excluir item de estoque?")) return;
    const senha = window.prompt('Digite sua senha para excluir');
    if (!senha) return;
    const usuario = JSON.parse(localStorage.getItem('usuario') || '{}');
    try {
      const auth = await fetchComAuth('/auth/login', { method: 'POST', body: JSON.stringify({ username: usuario.username, password: senha }) });
      if (!['Diretor','Coordenador','Supervisor','Gerente'].includes(auth.usuario?.cargo)) {
        alert('Usuário sem permissão');
        return;
      }
      await fetchComAuth(`/chapas-estoque/${id}`, { method: 'DELETE', body: JSON.stringify({ destino: usuario.username }) });
      carregar();
    } catch (err) {
      alert('Senha incorreta ou erro');
    }
  };

  const m2 = ((parseFloat(form.comprimento) || 0) * (parseFloat(form.largura) || 0)) / 1000000;
  const total = m2 * (parseFloat(form.custo_m2) || 0);

  return (
    <div className="p-6 space-y-4">
      <h2 className="text-lg font-semibold">Estoque de Chapas</h2>
      <div className="border p-4 rounded space-y-2">
        <label className="block">
          <span className="text-sm">Material</span>
          <select className="input w-full" value={form.chapa_id} onChange={handleChapa}>\
            <option value="">Selecione</option>
            {chapas.map(c => (
              <option key={c.id} value={c.id}>{c.propriedade} {c.espessura}mm</option>
            ))}
          </select>
        </label>
        <label className="block">
          <span className="text-sm">Descrição</span>
          <input className="input w-full" value={form.descricao} onChange={handle("descricao")} />
        </label>
        <label className="block">
          <span className="text-sm">Comprimento</span>
          <input type="number" className="input w-full" value={form.comprimento} onChange={handle("comprimento")} />
        </label>
        <label className="block">
          <span className="text-sm">Largura</span>
          <input type="number" className="input w-full" value={form.largura} onChange={handle("largura")} />
        </label>
        <label className="block">
          <span className="text-sm">Origem</span>
          <input className="input w-full" value={form.origem} onChange={handle("origem")} />
        </label>
        <div className="text-sm">m²: {m2.toFixed(3)} | Custo Total: {total.toFixed(2)}</div>
        <Button onClick={salvar}>Salvar</Button>
      </div>
      <table className="text-sm w-full">
        <thead>
          <tr>
            <th className="border px-2">Descrição</th>
            <th className="border px-2">Origem</th>
            <th className="border px-2">Comp</th>
            <th className="border px-2">Larg</th>
            <th className="border px-2">m²</th>
            <th className="border px-2">Custo m²</th>
            <th className="border px-2">Total</th>
            <th className="border px-2"></th>
          </tr>
        </thead>
        <tbody>
          {itens.map(it => (
            <tr key={it.id}>
              <td className="border px-2">{it.descricao}</td>
              <td className="border px-2">{it.origem}</td>
              <td className="border px-2">{it.comprimento}</td>
              <td className="border px-2">{it.largura}</td>
              <td className="border px-2">{(it.m2 || 0).toFixed(3)}</td>
              <td className="border px-2">{it.custo_m2}</td>
              <td className="border px-2">{(it.custo_total || 0).toFixed(2)}</td>
              <td className="border px-2 space-x-1">
                <Button size="sm" variant="outline" onClick={() => editar(it)}>Editar</Button>
                <Button size="sm" variant="destructive" onClick={() => remover(it.id)}>Excluir</Button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default EstoqueChapas;
