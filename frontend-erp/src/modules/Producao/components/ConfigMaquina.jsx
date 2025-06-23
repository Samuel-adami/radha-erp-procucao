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

const modeloCorte = {
  ordenarPecas: false,
  corteConcordante: true,
  tamanhoMaximo: "",
  ferramenta: "",
  ferramentaGrossa: "",
  configurarUltimoPasso: false,
  agruparUltimoPasso: false,
  profundidadeUltimoPasso: "",
  ferramentaUltimoPasso: "",
  ferramentaGrossaUltimoPasso: "",
  distanciaVelReduzida: "",
  padrao: false,
};

const ConfigMaquina = () => {
  const [ferramentas, setFerramentas] = useState([]);
  const [mostrarForm, setMostrarForm] = useState(false);
  const [editIndex, setEditIndex] = useState(null);
  const [form, setForm] = useState(modeloFerramenta);
  const [cortes, setCortes] = useState([]);
  const [mostrarFormCorte, setMostrarFormCorte] = useState(false);
  const [editCorteIndex, setEditCorteIndex] = useState(null);
  const [formCorte, setFormCorte] = useState(modeloCorte);

  useEffect(() => {
    const salvas = JSON.parse(localStorage.getItem("ferramentasNesting") || "[]");
    setFerramentas(salvas);
    const cfgCortes = JSON.parse(localStorage.getItem("configuracoesCorte") || "[]");
    setCortes(cfgCortes);
  }, []);

  const salvarLS = (dados) => {
    setFerramentas(dados);
    localStorage.setItem("ferramentasNesting", JSON.stringify(dados));
  };

  const salvarCortesLS = (dados) => {
    setCortes(dados);
    localStorage.setItem("configuracoesCorte", JSON.stringify(dados));
  };

  const novo = () => {
    setForm(modeloFerramenta);
    setEditIndex(null);
    setMostrarForm(true);
  };

  const novoCorte = () => {
    setFormCorte(modeloCorte);
    setEditCorteIndex(null);
    setMostrarFormCorte(true);
  };

  const editar = (idx) => {
    setForm({ ...ferramentas[idx] });
    setEditIndex(idx);
    setMostrarForm(true);
  };

  const editarCorte = (idx) => {
    setFormCorte({ ...cortes[idx] });
    setEditCorteIndex(idx);
    setMostrarFormCorte(true);
  };

  const remover = (idx) => {
    const nov = ferramentas.filter((_, i) => i !== idx);
    salvarLS(nov);
  };

  const removerCorte = (idx) => {
    const lista = cortes.filter((_, i) => i !== idx);
    salvarCortesLS(lista);
  };

  const marcarPadrao = (idx) => {
    const lista = cortes.map((c, i) => ({ ...c, padrao: i === idx }));
    salvarCortesLS(lista);
  };

  const salvar = () => {
    const lista = [...ferramentas];
    if (editIndex !== null) lista[editIndex] = form; else lista.push(form);
    salvarLS(lista);
    setMostrarForm(false);
  };

  const handleCorte = (campo) => (e) => {
    const value = e.target.type === 'checkbox' ? e.target.checked : e.target.value;
    setFormCorte({ ...formCorte, [campo]: value });
  };

  const salvarCorte = () => {
    const lista = [...cortes];
    if (editCorteIndex !== null) lista[editCorteIndex] = formCorte; else lista.push(formCorte);
    salvarCortesLS(lista);
    setMostrarFormCorte(false);
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

  const CorteItem = ({c, i}) => (
    <li className="grid grid-cols-6 gap-2 items-center border rounded p-2" key={i}>
      <span>{c.tamanhoMaximo}</span>
      <span>{c.ferramenta}</span>
      <input type="checkbox" checked={c.padrao} onChange={() => marcarPadrao(i)} />
      <input type="checkbox" checked={c.configurarUltimoPasso} disabled />
      <input type="checkbox" checked={c.ordenarPecas} disabled />
      <div className="space-x-1">
        <Button size="sm" variant="outline" onClick={() => editarCorte(i)}>Editar</Button>
        <Button size="sm" variant="destructive" onClick={() => removerCorte(i)}>Excluir</Button>
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
      <div className="mt-8 space-y-2">
        <h2 className="text-lg font-semibold">Configurador de Corte</h2>
        <Button onClick={novoCorte}>Cadastrar Nova Configuração</Button>
        {mostrarFormCorte && (
          <div className="border p-4 rounded space-y-2">
            <label className="flex items-center gap-2">
              <input type="checkbox" checked={formCorte.ordenarPecas} onChange={handleCorte('ordenarPecas')} />
              <span className="text-sm">Ordenar Peças da menor para maior</span>
            </label>
            <label className="flex items-center gap-2">
              <input type="checkbox" checked={formCorte.corteConcordante} onChange={handleCorte('corteConcordante')} />
              <span className="text-sm">Corte Concordante</span>
            </label>
            <label className="block">
              <span className="text-sm">Comprimento ou largura máxima da peça (mm)</span>
              <input type="number" className="input" value={formCorte.tamanhoMaximo} onChange={handleCorte('tamanhoMaximo')} />
            </label>
            <label className="block">
              <span className="text-sm">Ferramenta</span>
              <select className="input" value={formCorte.ferramenta} onChange={handleCorte('ferramenta')}>
                <option value="">Selecione</option>
                {ferramentas.filter(f => f.tipo === 'Fresa').map((f,i) => (
                  <option key={i} value={f.codigo}>{f.codigo} - {f.descricao}</option>
                ))}
              </select>
            </label>
            <label className="block">
              <span className="text-sm">Ferramentas para chapas grossas</span>
              <select className="input" value={formCorte.ferramentaGrossa} onChange={handleCorte('ferramentaGrossa')}>
                <option value="">Selecione</option>
                {ferramentas.filter(f => f.tipo === 'Fresa').map((f,i) => (
                  <option key={i} value={f.codigo}>{f.codigo} - {f.descricao}</option>
                ))}
              </select>
            </label>
            <label className="flex items-center gap-2">
              <input type="checkbox" checked={formCorte.configurarUltimoPasso} onChange={handleCorte('configurarUltimoPasso')} />
              <span className="text-sm">Configurar último passo de corte</span>
            </label>
            {formCorte.configurarUltimoPasso && (
              <div className="pl-4 space-y-2">
                <label className="flex items-center gap-2">
                  <input type="checkbox" checked={formCorte.agruparUltimoPasso} onChange={handleCorte('agruparUltimoPasso')} />
                  <span className="text-sm">Agrupar o último passo de corte de todas as peças</span>
                </label>
                <label className="block">
                  <span className="text-sm">Profundidade do último passo (mm)</span>
                  <input type="number" className="input" value={formCorte.profundidadeUltimoPasso} onChange={handleCorte('profundidadeUltimoPasso')} />
                </label>
                <label className="block">
                  <span className="text-sm">Ferramenta utilizada no último passo</span>
                  <select className="input" value={formCorte.ferramentaUltimoPasso} onChange={handleCorte('ferramentaUltimoPasso')}>
                    <option value="">Selecione</option>
                    {ferramentas.filter(f => f.tipo === 'Fresa').map((f,i) => (
                      <option key={i} value={f.codigo}>{f.codigo} - {f.descricao}</option>
                    ))}
                  </select>
                </label>
                <label className="block">
                  <span className="text-sm">Ferramenta utilizada para chapas grossas no último passo</span>
                  <select className="input" value={formCorte.ferramentaGrossaUltimoPasso} onChange={handleCorte('ferramentaGrossaUltimoPasso')}>
                    <option value="">Selecione</option>
                    {ferramentas.filter(f => f.tipo === 'Fresa').map((f,i) => (
                      <option key={i} value={f.codigo}>{f.codigo} - {f.descricao}</option>
                    ))}
                  </select>
                </label>
                <label className="block">
                  <span className="text-sm">Distância do final para aplicar velocidade reduzida de corte (mm)</span>
                  <input type="number" className="input" value={formCorte.distanciaVelReduzida} onChange={handleCorte('distanciaVelReduzida')} />
                </label>
              </div>
            )}
            <div className="space-x-2 pt-2">
              <Button onClick={salvarCorte}>Salvar</Button>
              <Button variant="outline" onClick={() => setMostrarFormCorte(false)}>Cancelar</Button>
            </div>
          </div>
        )}
        <ul className="space-y-1">
          {cortes.map((c, i) => <CorteItem c={c} i={i} key={i} />)}
        </ul>
      </div>
    </div>
  );
};

export default ConfigMaquina;
