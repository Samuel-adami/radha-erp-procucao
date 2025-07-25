import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { fetchComAuth, downloadComAuth } from "../../../utils/fetchComAuth";
import { Button } from "./ui/button";

const modeloLayer = {
  nome: "",
  tipo: "Chapa",
  cortarSobras: false,
  rotacao: "90 graus",
  espessura: "",
  pecaOuSobra: "Peça",
  profundidade: "",
  ferramenta: "",
  estrategia: "",
};

const modeloChapa = {
  possui_veio: false,
  propriedade: '',
  espessura: '',
  comprimento: '',
  largura: '',
};

const criaLayer = (nome) => {
  const matchFuro = nome.match(/^FURO_(\d+)_([\d\.]+)$/i);
  const matchUsinar = nome.match(/^USINAR_([\d\.]+)_([\w]+)/i);
  if (matchFuro) {
    return {
      ...modeloLayer,
      nome,
      tipo: "Operação",
      profundidade: matchFuro[2],
      ferramenta: `BROCA ${matchFuro[1]}MM`,
    };
  }
  if (matchUsinar) {
    return {
      ...modeloLayer,
      nome,
      tipo: "Operação",
      profundidade: matchUsinar[1],
      estrategia: matchUsinar[2],
    };
  }
  return { ...modeloLayer, nome };
};

const Nesting = () => {
  console.log("Componente Nesting MONTADO");
  
  const navigate = useNavigate();
  const [pastaLote, setPastaLote] = useState("");
  const [lotes, setLotes] = useState([]);
  const [larguraChapa, setLarguraChapa] = useState(2750);
  const [alturaChapa, setAlturaChapa] = useState(1850);
  const [resultado, setResultado] = useState("");
  const [layers, setLayers] = useState(() =>
    JSON.parse(localStorage.getItem("configLayers") || "[]")
  );
  const [fila, setFila] = useState([]);
  const [layerAtual, setLayerAtual] = useState(null);
  const [ferramentas, setFerramentas] = useState(() =>
    JSON.parse(localStorage.getItem("ferramentasNesting") || "[]")
  );
  const [aguardarExecucao, setAguardarExecucao] = useState(false);
  const [nestings, setNestings] = useState([]);
  const [chapas, setChapas] = useState([]);
  const [filaChapas, setFilaChapas] = useState([]);
  const [chapaAtual, setChapaAtual] = useState(null);
  const [sobrasDisp, setSobrasDisp] = useState({});
  const [sobrasSel, setSobrasSel] = useState([]);
  const [mostrarSobras, setMostrarSobras] = useState(false);

  useEffect(() => {
    const cfg = JSON.parse(localStorage.getItem("nestingConfig") || "{}");
    if (cfg.pastaLote) setPastaLote(cfg.pastaLote);
    if (cfg.larguraChapa) setLarguraChapa(cfg.larguraChapa);
    if (cfg.alturaChapa) setAlturaChapa(cfg.alturaChapa);

    fetchComAuth("/listar-lotes")
      .then((d) => {
        console.log("Lotes recebidos:", d);
        setLotes(d?.lotes || []);
      })
      .catch((e) => console.error("Falha ao carregar lotes", e));

    fetchComAuth("/nestings")
      .then((d) => setNestings(d?.nestings || []))
      .catch((e) => console.error("Falha ao carregar nestings", e));
    fetchComAuth("/chapas")
      .then((d) => setChapas(Array.isArray(d) ? d : []))
      .catch((e) => console.error("Falha ao carregar chapas", e));
  }, []);

  useEffect(() => {
    localStorage.setItem("configLayers", JSON.stringify(layers));
  }, [layers]);

  const salvar = () => {
    localStorage.setItem(
      "nestingConfig",
      JSON.stringify({ pastaLote, larguraChapa, alturaChapa })
    );
    alert("Configurações salvas");
  };

  const handleLayer = (campo) => (e) => {
    const value = e.target.type === 'checkbox' ? e.target.checked : e.target.value;
    setLayerAtual({ ...layerAtual, [campo]: value });
  };

  const handleChapa = (campo) => (e) => {
    const value = e.target.type === 'checkbox' ? e.target.checked : e.target.value;
    setChapaAtual({ ...chapaAtual, [campo]: value });
  };

  const normalizar = (s) =>
    String(s || '')
      .replace(/(\d+)\.\d+(?=mm)/gi, '$1')
      .trim()
      .toLowerCase();

  const verificarChapas = async () => {
    try {
      if (!chapas.length) {
        const dados = await fetchComAuth('/chapas');
        if (Array.isArray(dados)) setChapas(dados);
      }
      const resp = await fetchComAuth('/coletar-chapas', {
        method: 'POST',
        body: JSON.stringify({ pasta_lote: pastaLote }),
      });
      if (resp?.erro) {
        alert(resp.erro);
        return false;
      }
      const materiais = resp.materiais || [];
      const estoque = await fetchComAuth('/chapas-estoque-batch', {
        method: 'POST',
        body: JSON.stringify({ materiais }),
      });
      if (!estoque || typeof estoque !== 'object') return { ok: false };
      setSobrasDisp(estoque);
      const faltantes = materiais.filter(
        (m) => !chapas.some((c) => normalizar(c.propriedade) === normalizar(m))
      );
      if (faltantes.length) {
        const filaInicial = faltantes.map((p) => ({ ...modeloChapa, propriedade: p }));
        setFilaChapas(filaInicial);
        setChapaAtual(filaInicial[0]);
        setAguardarExecucao(true);
        return { ok: false };
      }
      const temSobras = Object.keys(estoque).length > 0;
      setMostrarSobras(temSobras);
      return { ok: true, temSobras };
    } catch (err) {
      alert('Erro ao verificar chapas');
      return { ok: false };
    }
  };

  const executarBackend = async () => {
    try {
      const data = await fetchComAuth("/executar-nesting", {
        method: "POST",
        body: JSON.stringify({
          pasta_lote: pastaLote,
          largura_chapa: parseFloat(larguraChapa),
          altura_chapa: parseFloat(alturaChapa),
          ferramentas,
          config_maquina: JSON.parse(localStorage.getItem("configMaquina") || "null"),
          config_layers: layers,
          sobras_ids: sobrasSel,
        }),
      });
      if (data?.erro) {
        alert(data.erro);
      } else if (Array.isArray(data?.layers)) {
        const faltantes = data.layers.filter(
          (n) => !layers.some((l) => l.nome === n)
        );
        if (faltantes.length) {
          const filaInicial = faltantes.map(criaLayer);
          setFila(filaInicial);
          setLayerAtual(filaInicial[0]);
          setAguardarExecucao(true);
          return;
        }
      }
    } catch (err) {
      alert("Falha ao executar nesting");
      console.error(err);
    }
  };

  const executar = async () => {
    const cfgMaquina = JSON.parse(localStorage.getItem("configMaquina") || "null");
    const cortes = JSON.parse(localStorage.getItem("configuracoesCorte") || "[]");

    if (!cfgMaquina) {
      alert("Configuração da máquina não cadastrada.");
      return navigate("config-maquina");
    }
    if (!ferramentas.length) {
      alert("Cadastre ao menos uma ferramenta.");
      return navigate("config-maquina");
    }
    if (!cortes.length) {
      alert("Configure o módulo de corte.");
      return navigate("config-maquina");
    }
    try {
      const resp = await fetchComAuth("/coletar-layers", {
        method: "POST",
        body: JSON.stringify({ pasta_lote: pastaLote }),
      });
      if (resp?.erro) {
        alert(resp.erro);
        return;
      }
      const faltantes = (resp.layers || []).filter(
        (n) => !layers.some((l) => l.nome === n)
      );
      if (faltantes.length) {
        const filaInicial = faltantes.map(criaLayer);
        setFila(filaInicial);
        setLayerAtual(filaInicial[0]);
        setAguardarExecucao(true);
        return;
      }
    } catch (err) {
      alert("Erro ao verificar layers");
      return;
    }
    
    const respChapas = await verificarChapas();
    if (!respChapas.ok) return;
    if (!respChapas.temSobras) await executarBackend();

    localStorage.setItem(
      'ultimaExecucaoNesting',
      JSON.stringify({
        pastaLote,
        larguraChapa,
        alturaChapa,
      })
    );
    localStorage.setItem('sobrasSelecionadas', JSON.stringify(sobrasSel));
    navigate('visualizacao');
  };

  const removerNesting = async (n) => {
    if (!window.confirm('Deseja remover esta otimização?')) return;
    try {
      await fetchComAuth('/remover-nesting', {
        method: 'POST',
        body: JSON.stringify({ id: n.id, pasta_resultado: n.pasta_resultado })
      });
      setNestings((prev) => prev.filter((x) => x.pasta_resultado !== n.pasta_resultado));
    } catch (e) {
      alert('Falha ao remover nesting');
    }
  };

  const baixarNesting = async (n) => {
    const url = `/download-nesting/${n.id}`;
    try {
      const loteBase = n.lote.split(/[/\\]/).pop().replace(/\.zip$/i, '');
      await downloadComAuth(url, `Nesting_${loteBase}.zip`);
    } catch (err) {
      alert('Falha ao baixar otimização');
    }
  };

  const visualizarNesting = (n) => {
    localStorage.setItem(
      'ultimaExecucaoNesting',
      JSON.stringify({
        pastaLote: n.lote,
        larguraChapa,
        alturaChapa,
      })
    );
    if (n.obj_key) {
      localStorage.setItem('visualizarNestingObjKey', n.obj_key);
    }
    navigate('visualizacao');
  };

  return (
    <div className="p-6 space-y-4">
      <h2 className="text-lg font-semibold">Configuração de Nesting</h2>
      <label className="block">
        <span className="text-sm">Pasta do Lote</span>
        <select
          className="input w-full"
          value={pastaLote}
          onChange={(e) => setPastaLote(e.target.value)}
        >
          <option value="">Selecione...</option>
          {lotes.map((l) => (
            <option key={l} value={l}>
              {l.split(/[/\\]/).pop().replace(/\.zip$/i, '')}
            </option>
          ))}
        </select>
      </label>
      <label className="block">
        <span className="text-sm">Largura da chapa (mm)</span>
        <input
          type="number"
          className="input w-full"
          value={larguraChapa}
          onChange={(e) => setLarguraChapa(e.target.value)}
        />
      </label>
      <label className="block">
        <span className="text-sm">Altura da chapa (mm)</span>
        <input
          type="number"
          className="input w-full"
          value={alturaChapa}
          onChange={(e) => setAlturaChapa(e.target.value)}
        />
      </label>
      <div className="space-x-2">
        <Button variant="outline" onClick={() => navigate('config-maquina')}>Configurar Máquina</Button>
        <Button onClick={salvar}>Salvar</Button>
        <Button onClick={executar}>Executar Nesting</Button>
      </div>
      {resultado && (
        <p className="text-sm">Arquivos gerados em: {resultado}</p>
      )}
      {mostrarSobras && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white p-4 space-y-2 rounded shadow max-w-sm w-full">
            <h3 className="font-semibold">Selecione Sobras para Utilizar</h3>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={Object.values(sobrasDisp).flat().every((s) => sobrasSel.includes(s.id))}
                onChange={(e) => {
                  if (e.target.checked) setSobrasSel(Object.values(sobrasDisp).flat().map((s) => s.id));
                  else setSobrasSel([]);
                }}
              />
              <span>Marcar Todas</span>
            </label>
            <div className="max-h-60 overflow-y-auto text-sm">
              {Object.entries(sobrasDisp).map(([m, lista]) => (
                <div key={m} className="mt-2">
                  <div className="font-semibold">{m}</div>
                  {lista.map((s) => (
                    <label key={s.id} className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={sobrasSel.includes(s.id)}
                        onChange={(e) => {
                          if (e.target.checked) setSobrasSel((prev) => [...prev, s.id]);
                          else setSobrasSel((prev) => prev.filter((x) => x !== s.id));
                        }}
                      />
                      <span>{s.descricao}</span>
                    </label>
                  ))}
                </div>
              ))}
            </div>
            <div className="space-x-2 pt-2">
              <Button onClick={() => { setMostrarSobras(false); executarBackend(); }}>
                Confirmar
              </Button>
              <Button variant="outline" onClick={() => { setSobrasSel([]); setMostrarSobras(false); executarBackend(); }}>
                Ignorar
              </Button>
            </div>
          </div>
        </div>
      )}
      {nestings.length > 0 && (
        <div className="mt-4">
          <h3 className="font-semibold mb-2">Otimizações</h3>
          <ul className="space-y-2">
            {nestings.map((n) => (
              <li key={n.id} className="flex justify-between items-center border p-2 rounded">
                <span>{n.lote.split(/[/\\]/).pop().replace(/\.zip$/i, '')}</span>
                <div className="space-x-2">
                  <Button size="sm" onClick={() => visualizarNesting(n)}>
                    Visualizar
                  </Button>
                  <Button size="sm" onClick={() => baixarNesting(n)}>Baixar</Button>
                  <Button variant="destructive" size="sm" onClick={() => removerNesting(n)}>
                    Excluir
                  </Button>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
      {layerAtual && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white p-4 space-y-2 rounded shadow max-w-sm w-full">
            <h3 className="font-semibold">Cadastrar Layer</h3>
            <label className="block">
              <span className="text-sm">Nome do Layer</span>
              <input
                className="input w-full"
                value={layerAtual.nome}
                onChange={handleLayer('nome')}
              />
            </label>
            <label className="block">
              <span className="text-sm">Configuração</span>
              <select className="input w-full" value={layerAtual.tipo} onChange={handleLayer('tipo')}>
                <option>Chapa</option>
                <option>Peça/Sobra</option>
                <option>Operação</option>
              </select>
            </label>
            {layerAtual.tipo === 'Chapa' && (
              <>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={layerAtual.cortarSobras}
                    onChange={handleLayer('cortarSobras')}
                  />
                  <span className="text-sm">Cortar sobras após cortar peças</span>
                </label>
                <label className="block">
                  <span className="text-sm">Rotacionar DXF</span>
                  <select className="input w-full" value={layerAtual.rotacao} onChange={handleLayer('rotacao')}>
                    <option>90 graus</option>
                    <option>180 graus</option>
                    <option>270 graus</option>
                  </select>
                </label>
                <label className="block">
                  <span className="text-sm">Espessura do Material (mm)</span>
                  <input
                    type="number"
                    className="input w-full"
                    value={layerAtual.espessura}
                    onChange={handleLayer('espessura')}
                  />
                </label>
              </>
            )}
            {layerAtual.tipo === 'Peça/Sobra' && (
              <label className="block">
                <span className="text-sm">Tipo</span>
                <select className="input w-full" value={layerAtual.pecaOuSobra} onChange={handleLayer('pecaOuSobra')}>
                  <option>Peça</option>
                  <option>Sobra</option>
                </select>
              </label>
            )}
            {layerAtual.tipo === 'Operação' && (
              <>
                <label className="block">
                  <span className="text-sm">Profundidade (mm)</span>
                  <input
                    type="number"
                    className="input w-full"
                    value={layerAtual.profundidade}
                    onChange={handleLayer('profundidade')}
                  />
                </label>
                <label className="block">
                  <span className="text-sm">Ferramenta</span>
                  <select className="input w-full" value={layerAtual.ferramenta} onChange={handleLayer('ferramenta')}>
                    <option value="">Selecione...</option>
                    {ferramentas.map((f, i) => (
                      <option key={i} value={f.codigo}>
                        {f.codigo} {f.descricao ? `- ${f.descricao}` : ''}
                      </option>
                    ))}
                  </select>
                  <Button size="sm" variant="outline" onClick={() => navigate('config-maquina')} className="mt-1 w-full">
                    Gerenciar Ferramentas
                  </Button>
                </label>
                <label className="block">
                  <span className="text-sm">Estratégia</span>
                  <select className="input w-full" value={layerAtual.estrategia} onChange={handleLayer('estrategia')}>
                    <option value="">Selecione</option>
                    <option>Por Dentro</option>
                    <option>Por Fora</option>
                    <option>Desbaste</option>
                    <option>Linha</option>
                  </select>
                </label>
              </>
            )}
            <div className="space-x-2 pt-2">
                <Button
                  onClick={async () => {
                    const prox = fila.slice(1);
                    const lista = [...layers, layerAtual];
                    setLayers(lista);
                    localStorage.setItem('configLayers', JSON.stringify(lista));
                    try {
                      await fetchComAuth('/config-layers', {
                        method: 'POST',
                        body: JSON.stringify(lista),
                      });
                    } catch (err) {
                      console.error('Erro ao salvar layers', err);
                    }
                    setFila(prox);
                    setLayerAtual(prox[0] || null);
                    if (prox.length === 0 && aguardarExecucao) {
                      setAguardarExecucao(false);
                      executarBackend();
                    }
                  }}
              >
                Cadastrar
              </Button>
              <Button variant="outline" onClick={() => { setFila([]); setLayerAtual(null); setAguardarExecucao(false); }}>
                Cancelar
              </Button>
            </div>
          </div>
        </div>
      )}
      {chapaAtual && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white p-4 space-y-2 rounded shadow max-w-sm w-full">
            <h3 className="font-semibold">Cadastrar Chapa</h3>
            <label className="flex items-center gap-2">
              <input type="checkbox" checked={chapaAtual.possui_veio} onChange={handleChapa('possui_veio')} />
              <span className="text-sm">Possui Veio</span>
            </label>
            <label className="block">
              <span className="text-sm">Propriedade do Material</span>
              <input className="input w-full" value={chapaAtual.propriedade} onChange={handleChapa('propriedade')} />
            </label>
            <label className="block">
              <span className="text-sm">Espessura (mm)</span>
              <input type="number" className="input w-full" value={chapaAtual.espessura} onChange={handleChapa('espessura')} />
            </label>
            <label className="block">
              <span className="text-sm">Comprimento</span>
              <input type="number" className="input w-full" value={chapaAtual.comprimento} onChange={handleChapa('comprimento')} />
            </label>
            <label className="block">
              <span className="text-sm">Largura</span>
              <input type="number" className="input w-full" value={chapaAtual.largura} onChange={handleChapa('largura')} />
            </label>
            <div className="space-x-2 pt-2">
              <Button
                onClick={async () => {
                  const prox = filaChapas.slice(1);
                  try {
                    await fetchComAuth('/chapas', { method: 'POST', body: JSON.stringify(chapaAtual) });
                  } catch (err) {
                    console.error('Erro ao salvar chapa', err);
                  }
                  setChapas([...chapas, chapaAtual]);
                  setFilaChapas(prox);
                  setChapaAtual(prox[0] || null);
                  if (prox.length === 0 && aguardarExecucao) {
                    setAguardarExecucao(false);
                    executarBackend();
                  }
                }}
              >
                Cadastrar
              </Button>
              <Button variant="outline" onClick={() => { setFilaChapas([]); setChapaAtual(null); setAguardarExecucao(false); }}>
                Cancelar
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Nesting;
