import React, { useEffect, useState } from "react";
import { fetchComAuth } from "../../../utils/fetchComAuth";
import { Button } from "./ui/button";

const modelo = {
  id: null,
  possui_veio: false,
  propriedade: "",
  espessura: "",
  comprimento: "",
  largura: "",
};

const CadastroChapas = () => {
  const [chapas, setChapas] = useState([]);
  const [form, setForm] = useState(modelo);

  const carregar = async () => {
    const dados = await fetchComAuth("/chapas");
    if (Array.isArray(dados)) setChapas(dados);
  };

  useEffect(() => {
    carregar();
  }, []);

  const handle = (campo) => (e) => {
    const value = e.target.type === "checkbox" ? e.target.checked : e.target.value;
    setForm({ ...form, [campo]: value });
  };

  const editar = (c) => {
    setForm({
      id: c.id,
      possui_veio: !!c.possui_veio,
      propriedade: c.propriedade,
      espessura: c.espessura,
      comprimento: c.comprimento,
      largura: c.largura,
    });
  };

  const salvar = async () => {
    await fetchComAuth("/chapas", { method: "POST", body: JSON.stringify(form) });
    setForm(modelo);
    carregar();
  };

  const remover = async (id) => {
    if (!window.confirm("Excluir chapa?")) return;
    await fetchComAuth(`/chapas/${id}`, { method: "DELETE" });
    carregar();
  };

  return (
    <div className="p-6 space-y-4">
      <h2 className="text-lg font-semibold">Cadastro de Chapas</h2>
      <div className="border p-4 rounded space-y-2">
        <label className="flex items-center gap-2">
          <input type="checkbox" checked={form.possui_veio} onChange={handle("possui_veio")} />
          <span className="text-sm">Possui Veio</span>
        </label>
        <label className="block">
          <span className="text-sm">Propriedade do Material</span>
          <input className="input w-full" value={form.propriedade} onChange={handle("propriedade")} />
        </label>
        <label className="block">
          <span className="text-sm">Espessura (mm)</span>
          <input type="number" className="input w-full" value={form.espessura} onChange={handle("espessura")} />
        </label>
        <label className="block">
          <span className="text-sm">Comprimento</span>
          <input type="number" className="input w-full" value={form.comprimento} onChange={handle("comprimento")} />
        </label>
        <label className="block">
          <span className="text-sm">Largura</span>
          <input type="number" className="input w-full" value={form.largura} onChange={handle("largura")} />
        </label>
        <Button onClick={salvar}>Salvar</Button>
      </div>
      <ul className="space-y-1">
        {chapas.map((c) => (
          <li key={c.id} className="flex justify-between items-center border rounded p-2">
            <span>
              {c.propriedade} ({c.comprimento} x {c.largura}){" "}
              {c.possui_veio ? "- possui veio" : ""}
            </span>
            <div className="space-x-2">
              <Button size="sm" variant="outline" onClick={() => editar(c)}>
                Editar
              </Button>
              <Button size="sm" variant="destructive" onClick={() => remover(c.id)}>
                Excluir
              </Button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default CadastroChapas;
