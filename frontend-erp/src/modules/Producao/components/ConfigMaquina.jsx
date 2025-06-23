import React, { useState, useEffect } from "react";
import { Button } from "./ui/button";
import { fetchComAuth } from "../../../utils/fetchComAuth";
import EtiquetaDesigner from "./EtiquetaDesigner";

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

const modeloConfigMaquina = {
  // GERAL
  possuiEtiquetadora: false,
  trocaRapidaBrocas: false,
  removerComentarios: false,
  cantosExternosRetos: false,
  reduzirVelocidadeCurvas: false,
  fabricante: "",
  modelo: "",
  nome: "",
  extensaoArquivo: ".nc",
  tamanhoNomeArquivo: 255,
  fimDeLinha: "Windows",
  comprimentoX: "",
  comprimentoY: "",
  movimentacaoZ: "",
  casasDecimais: "",
  // ETIQUETADORA - Chapa
  pontoReferenciaChapa: "Esquerda Superior",
  xOffsetChapa: "",
  yOffsetChapa: "",
  formatoImagemChapa: "BMP",
  anguloRotacaoChapa: "90 graus",
  inverterXChapa: false,
  inverterYChapa: false,
  // ETIQUETADORA
  tamanhoEtiquetadoraX: "",
  tamanhoEtiquetadoraY: "",
  pontoOrigemEtiqueta: "Esquerda Superior",
  posicaoXRotacaoEtiqueta: "",
  posicaoYRotacaoEtiqueta: "",
  formatoImagemEtiqueta: "BMP",
  rotacionarEtiquetaHorario: false,
  tamanhoMinimoPeca: "",
  mostrarNomeMaterial: false,
  layoutEtiqueta: [],
  // REFERENCIAS
  xHoming: "",
  yHoming: "",
  zHoming: "",
  zSeguranca: "",
  zAntesTrabalho: "",
  toleranciaCorte: "",
  cantoReferencia: "Esquerda Inferior",
  xOffsetReferencia: "",
  yOffsetReferencia: "",
  inverterXReferencia: false,
  inverterYReferencia: false,
  // POS PROCESSADOR
  introducao: "%\n( Powered by https://www.r-hex.com/ )\n( Cria\u00e7\u00e3o: [CREATION_DATE_TIME] )\n( P\u00f3s processador: [POST_PROCESSOR_NAME] )\n( Lote: [BATCH_NAME] )\n( Material: [MATERIAL] )\n( Dimens\u00f5es: X:[X_LENGHT] Y:[Y_LENGHT] Z:[Z_LENGHT] )\n( Ferramentas necess\u00e1rias para a execu\u00e7\u00e3o dos trabalhos: )\n[LIST_OF_USED_TOOLS]\n",
  cabecalho: "(######## HEADER ########)\n( NUMERO DA FERRAMENTA: [T] - [TOOL_DESCRIPTION] )\nG0 Z[ZH]\nM6 T[T]\n[CMD_EXTRA]\n",
  trocaFerramenta: "(######## Troca de ferramentas ########)\n( NUMERO DA FERRAMENTA: [T] - [TOOL_DESCRIPTION] )\nG0 Z[ZH]\nM6 T[T]\n[CMD_EXTRA]\n",
  rodape: "(######## FOOTER ########)\nG0 Z[ZH]\n(G0 X[XH]Y[YH] retirado a pedido do Samuel)\nM5\nM30\n%\n",
  furos: "",
  comandoFinalFuros: "(####### Desliga Magazine de Fura\u00e7\u00e3o #######)\nM15\n",
  movRapida: "",
  primeiraMovCorte: "",
  movCorte: "",
  primeiraMovCorteHorario: "",
  movCorteHorario: "",
  primeiraMovCorteAntiHorario: "",
  movCorteAntiHorario: "",
  // PARAMETROS DE OTIMIZACAO
  espacoEntrePecas: "",
  refiloInferior: "",
  refiloSuperior: "",
  refiloEsquerda: "",
  refiloDireita: "",
  cantoReferenciaOtimizacao: "Esquerda Inferior",
  comprimentoMinSobra: "",
  larguraMinSobra: "",
  ordenarChapasEspessura: "Crescente",
};

const modeloLayer = {
  nome: "",
  tipo: "Chapa", // Chapa, Peça/Sobra, Operação
  cortarSobras: false,
  rotacao: "90 graus",
  espessura: "",
  pecaOuSobra: "Peça",
  profundidade: "",
  ferramenta: "",
  estrategia: "",
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
  const [configMaquina, setConfigMaquina] = useState(modeloConfigMaquina);
  const [mostrarExtrasMov, setMostrarExtrasMov] = useState(false);
  const [layers, setLayers] = useState([]);
  const [mostrarFormLayer, setMostrarFormLayer] = useState(false);
  const [editLayerIndex, setEditLayerIndex] = useState(null);
  const [formLayer, setFormLayer] = useState(modeloLayer);

  useEffect(() => {
    const salvas = JSON.parse(localStorage.getItem("ferramentasNesting") || "[]");
    setFerramentas(salvas);
    const cfgCortes = JSON.parse(localStorage.getItem("configuracoesCorte") || "[]");
    setCortes(cfgCortes);
    const cfgMaquinaLocal = JSON.parse(localStorage.getItem("configMaquina") || "null");
    if (cfgMaquinaLocal) setConfigMaquina(cfgMaquinaLocal);
    const cfgLayers = JSON.parse(localStorage.getItem("configLayers") || "[]");
    setLayers(cfgLayers);

    fetchComAuth('/config-maquina')
      .then((data) => {
        if (data) {
          setConfigMaquina(data);
          localStorage.setItem('configMaquina', JSON.stringify(data));
        }
      })
      .catch((err) => console.error('Erro ao carregar configuracao da maquina', err));
  }, []);

  useEffect(() => {
    localStorage.setItem("ferramentasNesting", JSON.stringify(ferramentas));
  }, [ferramentas]);

  useEffect(() => {
    localStorage.setItem("configuracoesCorte", JSON.stringify(cortes));
  }, [cortes]);

  useEffect(() => {
    localStorage.setItem("configMaquina", JSON.stringify(configMaquina));
  }, [configMaquina]);

  useEffect(() => {
    localStorage.setItem("configLayers", JSON.stringify(layers));
  }, [layers]);

  const salvarLS = (dados) => {
    setFerramentas(dados);
    localStorage.setItem("ferramentasNesting", JSON.stringify(dados));
  };

  const salvarCortesLS = (dados) => {
    setCortes(dados);
    localStorage.setItem("configuracoesCorte", JSON.stringify(dados));
  };

  const salvarConfigMaquinaLS = (dados) => {
    setConfigMaquina(dados);
    localStorage.setItem("configMaquina", JSON.stringify(dados));
  };

  const salvarLayersLS = (dados) => {
    setLayers(dados);
    localStorage.setItem("configLayers", JSON.stringify(dados));
  };

  const updateLayoutEtiqueta = (dados) => {
    setConfigMaquina((c) => ({ ...c, layoutEtiqueta: dados }));
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

  const novoLayer = () => {
    setFormLayer(modeloLayer);
    setEditLayerIndex(null);
    setMostrarFormLayer(true);
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

  const editarLayer = (idx) => {
    setFormLayer({ ...layers[idx] });
    setEditLayerIndex(idx);
    setMostrarFormLayer(true);
  };

  const remover = (idx) => {
    const nov = ferramentas.filter((_, i) => i !== idx);
    salvarLS(nov);
  };

  const removerCorte = (idx) => {
    const lista = cortes.filter((_, i) => i !== idx);
    salvarCortesLS(lista);
  };

  const removerLayer = (idx) => {
    const lista = layers.filter((_, i) => i !== idx);
    salvarLayersLS(lista);
  };

  const marcarPadrao = (idx) => {
    const lista = cortes.map((c, i) => ({ ...c, padrao: i === idx }));
    salvarCortesLS(lista);
  };

  const handleLayer = (campo) => (e) => {
    const value = e.target.type === 'checkbox' ? e.target.checked : e.target.value;
    setFormLayer({ ...formLayer, [campo]: value });
  };

  const salvarLayer = () => {
    const lista = [...layers];
    if (editLayerIndex !== null) lista[editLayerIndex] = formLayer; else lista.push(formLayer);
    salvarLayersLS(lista);
    setMostrarFormLayer(false);
  };

  const salvar = () => {
    const lista = [...ferramentas];
    if (editIndex !== null) lista[editIndex] = form; else lista.push(form);
    salvarLS(lista);
    setMostrarForm(false);
  };

  const handleConfig = (campo) => (e) => {
    const value = e.target.type === 'checkbox' ? e.target.checked : e.target.value;
    setConfigMaquina({ ...configMaquina, [campo]: value });
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

  const salvarConfig = async () => {
    try {
      await fetchComAuth('/config-maquina', {
        method: 'POST',
        body: JSON.stringify(configMaquina),
      });
      salvarConfigMaquinaLS({ ...configMaquina });
      alert('Configuração salva com sucesso');
    } catch (err) {
      console.error('Erro ao salvar configuração', err);
      alert('Erro ao salvar configuração: ' + err.message);
    }
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
      <div className="space-y-2">
        <h2 className="text-lg font-semibold">Configurador da Máquina</h2>
        <div className="border p-4 rounded space-y-2">
          <h3 className="font-semibold">Gerais</h3>
          <label className="flex items-center gap-2">
            <input type="checkbox" checked={configMaquina.possuiEtiquetadora} onChange={handleConfig('possuiEtiquetadora')} />
            <span className="text-sm">Possui etiquetadora automática</span>
          </label>
          <label className="flex items-center gap-2">
            <input type="checkbox" checked={configMaquina.trocaRapidaBrocas} onChange={handleConfig('trocaRapidaBrocas')} />
            <span className="text-sm">Possui troca rápida de brocas</span>
          </label>
          <label className="flex items-center gap-2">
            <input type="checkbox" checked={configMaquina.removerComentarios} onChange={handleConfig('removerComentarios')} />
            <span className="text-sm">Remover comentários</span>
          </label>
          <label className="flex items-center gap-2">
            <input type="checkbox" checked={configMaquina.cantosExternosRetos} onChange={handleConfig('cantosExternosRetos')} />
            <span className="text-sm">Cantos externos retos</span>
          </label>
          <label className="flex items-center gap-2">
            <input type="checkbox" checked={configMaquina.reduzirVelocidadeCurvas} onChange={handleConfig('reduzirVelocidadeCurvas')} />
            <span className="text-sm">Diminuir velocidade nas curvas</span>
          </label>
          <label className="block">
            <span className="text-sm">Fabricante</span>
            <input className="input" value={configMaquina.fabricante} onChange={handleConfig('fabricante')} />
          </label>
          <label className="block">
            <span className="text-sm">Modelo</span>
            <input className="input" value={configMaquina.modelo} onChange={handleConfig('modelo')} />
          </label>
          <label className="block">
            <span className="text-sm">Nome da máquina</span>
            <input className="input" value={configMaquina.nome} onChange={handleConfig('nome')} />
          </label>
          <label className="block">
            <span className="text-sm">Extensão do arquivo</span>
            <input className="input" value={configMaquina.extensaoArquivo} onChange={handleConfig('extensaoArquivo')} />
          </label>
          <label className="block">
            <span className="text-sm">Tamanho do nome do arquivo</span>
            <input type="number" className="input" value={configMaquina.tamanhoNomeArquivo} onChange={handleConfig('tamanhoNomeArquivo')} />
          </label>
          <div className="text-sm">Fim de linha: Windows</div>
          <label className="block">
            <span className="text-sm">Comprimento em X (mm)</span>
            <input type="number" className="input" value={configMaquina.comprimentoX} onChange={handleConfig('comprimentoX')} />
          </label>
          <label className="block">
            <span className="text-sm">Comprimento em Y (mm)</span>
            <input type="number" className="input" value={configMaquina.comprimentoY} onChange={handleConfig('comprimentoY')} />
          </label>
          <label className="block">
            <span className="text-sm">Movimentação em Z (mm)</span>
            <input type="number" className="input" value={configMaquina.movimentacaoZ} onChange={handleConfig('movimentacaoZ')} />
          </label>
          <label className="block">
            <span className="text-sm">Casas Decimais</span>
            <input type="number" className="input" value={configMaquina.casasDecimais} onChange={handleConfig('casasDecimais')} />
          </label>
        </div>

        <div className="border p-4 rounded space-y-2">
          <h3 className="font-semibold">Etiquetadora</h3>
          <h4 className="font-medium">Chapa</h4>
          <label className="block">
            <span className="text-sm">Ponto de referência na chapa</span>
            <select className="input" value={configMaquina.pontoReferenciaChapa} onChange={handleConfig('pontoReferenciaChapa')}>
              <option>Esquerda Superior</option>
            </select>
          </label>
          <label className="block">
            <span className="text-sm">X Offset (mm)</span>
            <input type="number" className="input" value={configMaquina.xOffsetChapa} onChange={handleConfig('xOffsetChapa')} />
          </label>
          <label className="block">
            <span className="text-sm">Y Offset (mm)</span>
            <input type="number" className="input" value={configMaquina.yOffsetChapa} onChange={handleConfig('yOffsetChapa')} />
          </label>
          <label className="block">
            <span className="text-sm">Formato da imagem da chapa</span>
            <select className="input" value={configMaquina.formatoImagemChapa} onChange={handleConfig('formatoImagemChapa')}>
              <option>BMP</option>
            </select>
          </label>
          <label className="block">
            <span className="text-sm">Angulo de rotação da chapa em graus (°graus)</span>
            <select className="input" value={configMaquina.anguloRotacaoChapa} onChange={handleConfig('anguloRotacaoChapa')}>
              <option>90 graus</option>
            </select>
          </label>
          <label className="flex items-center gap-2">
            <input type="checkbox" checked={configMaquina.inverterXChapa} onChange={handleConfig('inverterXChapa')} />
            <span className="text-sm">Inverter Eixo X</span>
          </label>
          <label className="flex items-center gap-2">
            <input type="checkbox" checked={configMaquina.inverterYChapa} onChange={handleConfig('inverterYChapa')} />
            <span className="text-sm">Inverter Eixo Y</span>
          </label>

          <h4 className="font-medium">Etiquetadora</h4>
          <label className="block">
            <span className="text-sm">Tamanho da etiquetadora em X (mm)</span>
            <input type="number" className="input" value={configMaquina.tamanhoEtiquetadoraX} onChange={handleConfig('tamanhoEtiquetadoraX')} />
          </label>
          <label className="block">
            <span className="text-sm">Tamanho da etiquetadora em Y (mm)</span>
            <input type="number" className="input" value={configMaquina.tamanhoEtiquetadoraY} onChange={handleConfig('tamanhoEtiquetadoraY')} />
          </label>
          <label className="block">
            <span className="text-sm">Ponto de origem</span>
            <select className="input" value={configMaquina.pontoOrigemEtiqueta} onChange={handleConfig('pontoOrigemEtiqueta')}>
              <option>Esquerda Superior</option>
            </select>
          </label>
          <label className="block">
            <span className="text-sm">Posição X do eixo de rotação (mm)</span>
            <input type="number" className="input" value={configMaquina.posicaoXRotacaoEtiqueta} onChange={handleConfig('posicaoXRotacaoEtiqueta')} />
          </label>
          <label className="block">
            <span className="text-sm">Posição Y do eixo de rotação (mm)</span>
            <input type="number" className="input" value={configMaquina.posicaoYRotacaoEtiqueta} onChange={handleConfig('posicaoYRotacaoEtiqueta')} />
          </label>
          <label className="block">
            <span className="text-sm">Formato da imagem da etiqueta</span>
            <select className="input" value={configMaquina.formatoImagemEtiqueta} onChange={handleConfig('formatoImagemEtiqueta')}>
              <option>BMP</option>
            </select>
          </label>
          <label className="flex items-center gap-2">
            <input type="checkbox" checked={configMaquina.rotacionarEtiquetaHorario} onChange={handleConfig('rotacionarEtiquetaHorario')} />
            <span className="text-sm">Rotacionar etiqueta no sentido horário</span>
          </label>
          <label className="block">
            <span className="text-sm">Tamanho mínimo da peça (mm)</span>
            <input type="number" className="input" value={configMaquina.tamanhoMinimoPeca} onChange={handleConfig('tamanhoMinimoPeca')} />
          </label>
          <label className="flex items-center gap-2">
            <input type="checkbox" checked={configMaquina.mostrarNomeMaterial} onChange={handleConfig('mostrarNomeMaterial')} />
            <span className="text-sm">Mostrar nome completo do material (longo)</span>
          </label>
          <div>
            <h4 className="font-medium mb-1">Layout da Etiqueta</h4>
            <EtiquetaDesigner
              layout={configMaquina.layoutEtiqueta || []}
              onChange={updateLayoutEtiqueta}
              largura={configMaquina.tamanhoEtiquetadoraX}
              altura={configMaquina.tamanhoEtiquetadoraY}
            />
          </div>
        </div>

        <div className="border p-4 rounded space-y-2">
          <h3 className="font-semibold">Referências</h3>
          <label className="block">
            <span className="text-sm">X Homing (mm)</span>
            <input type="number" className="input" value={configMaquina.xHoming} onChange={handleConfig('xHoming')} />
          </label>
          <label className="block">
            <span className="text-sm">Y Homing (mm)</span>
            <input type="number" className="input" value={configMaquina.yHoming} onChange={handleConfig('yHoming')} />
          </label>
          <label className="block">
            <span className="text-sm">Z Homing (mm)</span>
            <input type="number" className="input" value={configMaquina.zHoming} onChange={handleConfig('zHoming')} />
          </label>
          <label className="block">
            <span className="text-sm">Z de segurança (mm)</span>
            <input type="number" className="input" value={configMaquina.zSeguranca} onChange={handleConfig('zSeguranca')} />
          </label>
          <label className="block">
            <span className="text-sm">Z antes de iniciar um trabalho (mm)</span>
            <input type="number" className="input" value={configMaquina.zAntesTrabalho} onChange={handleConfig('zAntesTrabalho')} />
          </label>
          <label className="block">
            <span className="text-sm">Tolerância de corte (mm)</span>
            <input type="number" className="input" value={configMaquina.toleranciaCorte} onChange={handleConfig('toleranciaCorte')} />
          </label>
          <label className="block">
            <span className="text-sm">Canto de referência</span>
            <select className="input" value={configMaquina.cantoReferencia} onChange={handleConfig('cantoReferencia')}>
              <option>Esquerda Inferior</option>
            </select>
          </label>
          <label className="block">
            <span className="text-sm">X Offset (mm)</span>
            <input type="number" className="input" value={configMaquina.xOffsetReferencia} onChange={handleConfig('xOffsetReferencia')} />
          </label>
          <label className="block">
            <span className="text-sm">Y Offset (mm)</span>
            <input type="number" className="input" value={configMaquina.yOffsetReferencia} onChange={handleConfig('yOffsetReferencia')} />
          </label>
          <label className="flex items-center gap-2">
            <input type="checkbox" checked={configMaquina.inverterXReferencia} onChange={handleConfig('inverterXReferencia')} />
            <span className="text-sm">Inverter Eixo X</span>
          </label>
          <label className="flex items-center gap-2">
            <input type="checkbox" checked={configMaquina.inverterYReferencia} onChange={handleConfig('inverterYReferencia')} />
            <span className="text-sm">Inverter Eixo Y</span>
          </label>
        </div>

        <div className="border p-4 rounded space-y-2">
          <h3 className="font-semibold">Pós-Processador</h3>
          <label className="block">
            <span className="text-sm">Introdução</span>
            <textarea className="input" rows="4" value={configMaquina.introducao} onChange={handleConfig('introducao')} />
          </label>
          <label className="block">
            <span className="text-sm">Cabeçalho</span>
            <textarea className="input" rows="3" value={configMaquina.cabecalho} onChange={handleConfig('cabecalho')} />
          </label>
          <label className="block">
            <span className="text-sm">Troca de ferramentas</span>
            <textarea className="input" rows="3" value={configMaquina.trocaFerramenta} onChange={handleConfig('trocaFerramenta')} />
          </label>
          <label className="block">
            <span className="text-sm">Rodapé</span>
            <textarea className="input" rows="3" value={configMaquina.rodape} onChange={handleConfig('rodape')} />
          </label>
          <label className="block">
            <span className="text-sm">Furos</span>
            <textarea className="input" rows="2" value={configMaquina.furos} onChange={handleConfig('furos')} />
          </label>
          <label className="block">
            <span className="text-sm">Comando ao finalizar furos</span>
            <textarea className="input" rows="2" value={configMaquina.comandoFinalFuros} onChange={handleConfig('comandoFinalFuros')} />
          </label>
          <Button variant="outline" onClick={() => setMostrarExtrasMov(!mostrarExtrasMov)}>
            Configurações Extras de Movimentação
          </Button>
          {mostrarExtrasMov && (
            <div className="pl-4 space-y-2">
              <label className="block">
                <span className="text-sm">Movimentação Rápida</span>
                <input className="input" value={configMaquina.movRapida} onChange={handleConfig('movRapida')} />
              </label>
              <label className="block">
                <span className="text-sm">Primeira Movimentação de Corte</span>
                <input className="input" value={configMaquina.primeiraMovCorte} onChange={handleConfig('primeiraMovCorte')} />
              </label>
              <label className="block">
                <span className="text-sm">Movimentação de Corte</span>
                <input className="input" value={configMaquina.movCorte} onChange={handleConfig('movCorte')} />
              </label>
              <label className="block">
                <span className="text-sm">Primeira Movimentação de Corte em Arco no Sentido Horário</span>
                <input className="input" value={configMaquina.primeiraMovCorteHorario} onChange={handleConfig('primeiraMovCorteHorario')} />
              </label>
              <label className="block">
                <span className="text-sm">Movimentação de Corte em Arco no Sentido Horário</span>
                <input className="input" value={configMaquina.movCorteHorario} onChange={handleConfig('movCorteHorario')} />
              </label>
              <label className="block">
                <span className="text-sm">Primeira Movimentação de Corte em Arco no Sentido Anti-Horário</span>
                <input className="input" value={configMaquina.primeiraMovCorteAntiHorario} onChange={handleConfig('primeiraMovCorteAntiHorario')} />
              </label>
              <label className="block">
                <span className="text-sm">Movimentação de Corte em Arco no Sentido Anti-Horário</span>
                <input className="input" value={configMaquina.movCorteAntiHorario} onChange={handleConfig('movCorteAntiHorario')} />
              </label>
            </div>
          )}
        </div>

        <div className="border p-4 rounded space-y-2">
          <h3 className="font-semibold">Parâmetros de Otimização</h3>
          <label className="block">
            <span className="text-sm">Espaço entre peças (mm)</span>
            <input type="number" className="input" value={configMaquina.espacoEntrePecas} onChange={handleConfig('espacoEntrePecas')} />
          </label>
          <label className="block">
            <span className="text-sm">Refilo inferior (mm)</span>
            <input type="number" className="input" value={configMaquina.refiloInferior} onChange={handleConfig('refiloInferior')} />
          </label>
          <label className="block">
            <span className="text-sm">Refilo superior (mm)</span>
            <input type="number" className="input" value={configMaquina.refiloSuperior} onChange={handleConfig('refiloSuperior')} />
          </label>
          <label className="block">
            <span className="text-sm">Refilo à esquerda (mm)</span>
            <input type="number" className="input" value={configMaquina.refiloEsquerda} onChange={handleConfig('refiloEsquerda')} />
          </label>
          <label className="block">
            <span className="text-sm">Refilo à direita (mm)</span>
            <input type="number" className="input" value={configMaquina.refiloDireita} onChange={handleConfig('refiloDireita')} />
          </label>
          <label className="block">
            <span className="text-sm">Canto de referência</span>
            <select className="input" value={configMaquina.cantoReferenciaOtimizacao} onChange={handleConfig('cantoReferenciaOtimizacao')}>
              <option>Esquerda Inferior</option>
              <option>Esquerda Superior</option>
              <option>Direita Superior</option>
              <option>Direita Inferior</option>
            </select>
          </label>
          <label className="block">
            <span className="text-sm">Comprimento mínimo da sobra (mm)</span>
            <input type="number" className="input" value={configMaquina.comprimentoMinSobra} onChange={handleConfig('comprimentoMinSobra')} />
          </label>
          <label className="block">
            <span className="text-sm">Largura mínima da sobra (mm)</span>
            <input type="number" className="input" value={configMaquina.larguraMinSobra} onChange={handleConfig('larguraMinSobra')} />
          </label>
          <label className="block">
            <span className="text-sm">Ordenar chapas por espessura</span>
            <select className="input" value={configMaquina.ordenarChapasEspessura} onChange={handleConfig('ordenarChapasEspessura')}>
              <option>Crescente</option>
              <option>Decrescente</option>
            </select>
          </label>
        </div>

        <Button onClick={salvarConfig}>Salvar Configuração da Máquina</Button>
      </div>

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
      <div className="mt-8 space-y-2">
        <h2 className="text-lg font-semibold">Cadastro de Layers</h2>
        <Button onClick={novoLayer}>Cadastrar Novo Layer</Button>
        {mostrarFormLayer && (
          <div className="border p-4 rounded space-y-2">
            <label className="block">
              <span className="text-sm">Nome do Layer</span>
              <input className="input" value={formLayer.nome} onChange={handleLayer('nome')} />
            </label>
            <label className="block">
              <span className="text-sm">Configuração</span>
              <select className="input" value={formLayer.tipo} onChange={handleLayer('tipo')}>
                <option>Chapa</option>
                <option>Peça/Sobra</option>
                <option>Operação</option>
              </select>
            </label>
            {formLayer.tipo === 'Chapa' && (
              <>
                <label className="flex items-center gap-2">
                  <input type="checkbox" checked={formLayer.cortarSobras} onChange={handleLayer('cortarSobras')} />
                  <span className="text-sm">Cortar sobras após cortar peças</span>
                </label>
                <label className="block">
                  <span className="text-sm">Rotacionar DXF</span>
                  <select className="input" value={formLayer.rotacao} onChange={handleLayer('rotacao')}>
                    <option>90 graus</option>
                    <option>180 graus</option>
                    <option>270 graus</option>
                  </select>
                </label>
                <label className="block">
                  <span className="text-sm">Espessura do Material (mm)</span>
                  <input type="number" className="input" value={formLayer.espessura} onChange={handleLayer('espessura')} />
                </label>
              </>
            )}
            {formLayer.tipo === 'Peça/Sobra' && (
              <label className="block">
                <span className="text-sm">Tipo</span>
                <select className="input" value={formLayer.pecaOuSobra} onChange={handleLayer('pecaOuSobra')}>
                  <option>Peça</option>
                  <option>Sobra</option>
                </select>
              </label>
            )}
            {formLayer.tipo === 'Operação' && (
              <>
                <label className="block">
                  <span className="text-sm">Profundidade (mm)</span>
                  <input type="number" className="input" value={formLayer.profundidade} onChange={handleLayer('profundidade')} />
                </label>
                <label className="block">
                  <span className="text-sm">Ferramenta</span>
                  <input className="input" value={formLayer.ferramenta} onChange={handleLayer('ferramenta')} />
                </label>
                <label className="block">
                  <span className="text-sm">Estratégia</span>
                  <select className="input" value={formLayer.estrategia} onChange={handleLayer('estrategia')}>
                    <option value="">Selecione</option>
                    <option>Por Dentro</option>
                    <option>Por Fora</option>
                    <option>Desbaste</option>
                  </select>
                </label>
              </>
            )}
            <div className="space-x-2 pt-2">
              <Button onClick={salvarLayer}>Salvar</Button>
              <Button variant="outline" onClick={() => setMostrarFormLayer(false)}>Cancelar</Button>
            </div>
          </div>
        )}
        <ul className="space-y-1">
          {layers.map((l, i) => (
            <li key={i} className="grid grid-cols-4 gap-2 items-center border rounded p-2">
              <span>{l.nome}</span>
              <span>{l.tipo}</span>
              <span className="text-xs">
                {l.tipo === 'Chapa' && `Espessura: ${l.espessura}mm / Rotação ${l.rotacao}`}
                {l.tipo === 'Peça/Sobra' && `${l.pecaOuSobra}`}
                {l.tipo === 'Operação' && `Ferramenta: ${l.ferramenta} Prof: ${l.profundidade}`}
              </span>
              <div className="space-x-1">
                <Button size="sm" variant="outline" onClick={() => editarLayer(i)}>Editar</Button>
                <Button size="sm" variant="destructive" onClick={() => removerLayer(i)}>Excluir</Button>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};

export default ConfigMaquina;
