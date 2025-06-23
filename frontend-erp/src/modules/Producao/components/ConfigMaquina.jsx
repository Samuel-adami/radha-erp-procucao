import React, { useState, useEffect } from "react";
import { Button } from "./ui/button";

const modeloFerramenta = {
  tipo: "Fresa",
  sentidoCorte: "Horário",
  codigo: "",
  tipoFerramenta: "Fresa de topo raso",
  descricao: "",
  diametro: "",
  areaCorteLimite: "",
  comprimentoUtil: "",
  entradaChapa: "",
  velocidadeRotacao: "",
  velocidadeCorte: "",
  velocidadeEntrada: "",
  velocidadeReduzida: "",
  anguloEntrada: "",
  comandoExtra: "",
};

const ConfigMaquina = () => {
  const [ferramentas, setFerramentas] = useState([]);
  const [mostrarForm, setMostrarForm] = useState(false);
  const [editIndex, setEditIndex] = useState(null);
  const [form, setForm] = useState(modeloFerramenta);

  useEffect(() => {
    const salvas = JSON.parse(localStorage.getItem("ferramentasNesting") || "[]");
    setFerramentas(salvas);
  }, []);

  const salvarLS = (dados) => {
    setFerramentas(dados);
    localStorage.setItem("ferramentasNesting", JSON.stringify(dados));
  };

  const novo = () => {
    setForm(modeloFerramenta);
    setEditIndex(null);
    setMostrarForm(true);
  };

  const editar = (idx) => {
    setForm({ ...ferramentas[idx] });
    setEditIndex(idx);
    setMostrarForm(true);
  };

  const remover = (idx) => {
    const nov = ferramentas.filter((_, i) => i !== idx);
    salvarLS(nov);
  };

  const salvar = () => {
    const lista = [...ferramentas];
    if (editIndex !== null) lista[editIndex] = form; else lista.push(form);
    salvarLS(lista);
    setMostrarForm(false);
  };

  const handle = (campo) => (e) => setForm({ ...form, [campo]: e.target.value });

  const Item = ({f, i}) => (
    <li className="flex justify-between border rounded p-2" key={i}>
      <div>
        <div className="text-sm font-medium">{f.codigo}</div>
        <div className="text-xs">{f.diametro}mm - {f.descricao}</div>
      </div>
      <div className="space-x-1">
        <Button size="sm" variant="outline" onClick={() => editar(i)}>Editar</Button>
        <Button size="sm" variant="destructive" onClick={() => remover(i)}>Excluir</Button>
      </div>
    </li>
  );

  return (
    <div className="p-6 space-y-4">
      <h2 className="text-lg font-semibold">Ferramentas</h2>
      <Button onClick={novo}>Cadastrar Nova Ferramenta</Button>
      {mostrarForm && (
        <div className="border p-4 rounded space-y-2">
          <label className="block">
            <span className="text-sm">Tipo</span>
            <select className="input" value={form.tipo} onChange={handle('tipo')}>
              <option>Fresa</option>
              <option>Broca</option>
            </select>
          </label>
          {form.tipo === 'Fresa' && (
            <>
              <label className="block">
                <span className="text-sm">Sentido do corte</span>
                <select className="input" value={form.sentidoCorte} onChange={handle('sentidoCorte')}>
                  <option>Horário</option>
                  <option>Anti-horário</option>
                </select>
              </label>
              <label className="block">
                <span className="text-sm">Código da ferramenta na máquina</span>
                <input className="input" value={form.codigo} onChange={handle('codigo')} />
              </label>
              <label className="block">
                <span className="text-sm">Tipo de ferramenta</span>
                <select className="input" value={form.tipoFerramenta} onChange={handle('tipoFerramenta')}>
                  <option>Fresa de topo raso</option>
                  <option>Fresa V-Bit</option>
                </select>
              </label>
              <label className="block">
                <span className="text-sm">Descrição da Ferramenta</span>
                <input className="input" value={form.descricao} onChange={handle('descricao')} />
              </label>
              <label className="block">
                <span className="text-sm">Diâmetro da Ferramenta em (mm)</span>
                <input type="number" className="input" value={form.diametro} onChange={handle('diametro')} />
              </label>
              <label className="block">
                <span className="text-sm">Área de Corte Limite em (mm)</span>
                <input type="number" className="input" value={form.areaCorteLimite} onChange={handle('areaCorteLimite')} />
              </label>
              <label className="block">
                <span className="text-sm">Comprimento Ú til da Ferramenta em (mm)</span>
                <input type="number" className="input" value={form.comprimentoUtil} onChange={handle('comprimentoUtil')} />
              </label>
              <label className="block">
                <span className="text-sm">Entrada na Chapa de Sacrifício (mm)</span>
                <input type="number" className="input" value={form.entradaChapa} onChange={handle('entradaChapa')} />
              </label>
              <label className="block">
                <span className="text-sm">Velocidade de Rotação do Spindle (RPM)</span>
                <input type="number" className="input" value={form.velocidadeRotacao} onChange={handle('velocidadeRotacao')} />
              </label>
              <label className="block">
                <span className="text-sm">Velocidade de Corte da Ferramenta (mm/min)</span>
                <input type="number" className="input" value={form.velocidadeCorte} onChange={handle('velocidadeCorte')} />
              </label>
              <label className="block">
                <span className="text-sm">Velocidade de Entrada da Ferramenta no Material (mm/min)</span>
                <input type="number" className="input" value={form.velocidadeEntrada} onChange={handle('velocidadeEntrada')} />
              </label>
              <label className="block">
                <span className="text-sm">Velocidade de Corte Reduzida (mm/min)</span>
                <input type="number" className="input" value={form.velocidadeReduzida} onChange={handle('velocidadeReduzida')} />
              </label>
              <label className="block">
                <span className="text-sm">Â ngulo de Entrada da Ferramenta (°graus)</span>
                <input type="number" className="input" value={form.anguloEntrada} onChange={handle('anguloEntrada')} />
              </label>
              <label className="block">
                <span className="text-sm">Comando Extra</span>
                <input className="input" value={form.comandoExtra} onChange={handle('comandoExtra')} />
              </label>
            </>
          )}
          {form.tipo === 'Broca' && (
            <>
              <label className="block">
                <span className="text-sm">Código da ferramenta na máquina</span>
                <input className="input" value={form.codigo} onChange={handle('codigo')} />
              </label>
              <label className="block">
                <span className="text-sm">Descrição da Ferramenta</span>
                <input className="input" value={form.descricao} onChange={handle('descricao')} />
              </label>
              <label className="block">
                <span className="text-sm">Diâmetro da Ferramenta em (mm)</span>
                <input type="number" className="input" value={form.diametro} onChange={handle('diametro')} />
              </label>
              <label className="block">
                <span className="text-sm">Área de Corte Limite em (mm)</span>
                <input type="number" className="input" value={form.areaCorteLimite} onChange={handle('areaCorteLimite')} />
              </label>
              <label className="block">
                <span className="text-sm">Comprimento Ú til da Ferramenta em (mm)</span>
                <input type="number" className="input" value={form.comprimentoUtil} onChange={handle('comprimentoUtil')} />
              </label>
              <label className="block">
                <span className="text-sm">Entrada na Chapa de Sacrifício (mm)</span>
                <input type="number" className="input" value={form.entradaChapa} onChange={handle('entradaChapa')} />
              </label>
              <label className="block">
                <span className="text-sm">Velocidade de Rotação do Spindle (RPM)</span>
                <input type="number" className="input" value={form.velocidadeRotacao} onChange={handle('velocidadeRotacao')} />
              </label>
              <label className="block">
                <span className="text-sm">Velocidade de Corte da Ferramenta (mm/min)</span>
                <input type="number" className="input" value={form.velocidadeCorte} onChange={handle('velocidadeCorte')} />
              </label>
              <label className="block">
                <span className="text-sm">Comando Extra</span>
                <input className="input" value={form.comandoExtra} onChange={handle('comandoExtra')} />
              </label>
            </>
          )}
          <div className="space-x-2 pt-2">
            <Button onClick={salvar}>Salvar</Button>
            <Button variant="outline" onClick={() => setMostrarForm(false)}>Cancelar</Button>
          </div>
        </div>
      )}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <h3 className="font-semibold">Fresas</h3>
          <ul className="space-y-1">
            {ferramentas.filter(f => f.tipo === 'Fresa').map((f, i) => <Item f={f} i={i} key={i} />)}
          </ul>
        </div>
        <div>
          <h3 className="font-semibold">Brocas</h3>
          <ul className="space-y-1">
            {ferramentas.filter(f => f.tipo === 'Broca').map((f, i) => <Item f={f} i={i} key={i} />)}
          </ul>
        </div>
      </div>
    </div>
  );
};

export default ConfigMaquina;
