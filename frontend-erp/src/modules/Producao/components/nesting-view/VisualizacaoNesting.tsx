import React, { useEffect, useState } from 'react';
import { fetchComAuth } from '../../../../utils/fetchComAuth';
import { Button } from '../ui/button';
import FiltroChapa from './FiltroChapa';
import ChapaViewer, { Chapa, Operacao } from './ChapaViewer';
import OperacaoList from './OperacaoList';
import OperacaoDetailModal from './OperacaoDetailModal';

const VisualizacaoNesting: React.FC = () => {
  const [chapas, setChapas] = useState<Chapa[]>([]);
  const [larguraViewer, setLarguraViewer] = useState(600);
  const [descricao, setDescricao] = useState('');
  const [indice, setIndice] = useState(0);
  const [selecionada, setSelecionada] = useState<Operacao | null>(null);
  const [destaque, setDestaque] = useState<number | null>(null);
  const [confirmado, setConfirmado] = useState(false);
  const [enviando, setEnviando] = useState(false);

  useEffect(() => {
    async function carregar() {
      const cfg = localStorage.getItem('ultimaExecucaoNesting');
      const objKey = localStorage.getItem('visualizarNestingObjKey');

      if (objKey) {
        const dadosSalvos = localStorage.getItem(`nestingPreview_${objKey}`);
        if (dadosSalvos) {
          try {
            setChapas(JSON.parse(dadosSalvos));
            setConfirmado(true);
            return;
          } catch {}
        }
      }

      try {
        const params = cfg ? JSON.parse(cfg) : {};
        const dados = await fetchComAuth('/nesting-preview', {
          method: 'POST',
          body: JSON.stringify({
            pasta_lote: params.pastaLote,
            largura_chapa: params.larguraChapa,
            altura_chapa: params.alturaChapa,
            ferramentas: JSON.parse(localStorage.getItem('ferramentasNesting') || '[]'),
            config_maquina: JSON.parse(localStorage.getItem('configMaquina') || 'null'),
            config_layers: JSON.parse(localStorage.getItem('configLayers') || '[]'),
            sobras_ids: JSON.parse(localStorage.getItem('sobrasSelecionadas') || '[]'),
          }),
        });
        if (dados?.erro) {
          alert(dados.erro);
        } else if (Array.isArray(dados?.chapas)) {
          setChapas(dados.chapas);
        }
      } catch {
        // dados fictícios
        setChapas([
          {
            id: 1,
            codigo: '001',
            descricao: 'MDF 18mm',
            largura: 2750,
            altura: 1850,
            operacoes: [
              { id: 1, nome: 'Peca 1', tipo: 'Peca', x: 10, y: 10, largura: 400, altura: 300 },
              { id: 2, nome: 'Sobra 1', tipo: 'Sobra', x: 420, y: 10, largura: 200, altura: 300 },
            ],
          },
        ]);
      }
    }
    carregar();
  }, []);

  useEffect(() => {
    const atualizar = () => {
      const w = Math.min(window.innerWidth - 420, 900);
      setLarguraViewer(w > 300 ? w : 300);
    };
    atualizar();
    window.addEventListener('resize', atualizar);
    return () => window.removeEventListener('resize', atualizar);
  }, []);

  const materiais = Array.from(new Set(chapas.map((c) => c.descricao)));

  useEffect(() => {
    if (!descricao && materiais.length > 0) {
      setDescricao(materiais[0]);
    }
  }, [materiais]);

  const filtradas = chapas.filter((c) => (!descricao || c.descricao === descricao));

  const chapaAtual = filtradas[indice] || null;

  useEffect(() => {
    setIndice(0);
  }, [descricao]);

  useEffect(() => {
    if (indice >= filtradas.length) setIndice(0);
  }, [filtradas.length]);

  const confirmar = async () => {
    setEnviando(true);
    try {
      const cfg = localStorage.getItem('ultimaExecucaoNesting');
      const params = cfg ? JSON.parse(cfg) : {};
      const resp = await fetchComAuth('/executar-nesting-final', {
        method: 'POST',
        body: JSON.stringify({
          pasta_lote: params.pastaLote,
          largura_chapa: params.larguraChapa,
          altura_chapa: params.alturaChapa,
          ferramentas: JSON.parse(localStorage.getItem('ferramentasNesting') || '[]'),
          config_maquina: JSON.parse(localStorage.getItem('configMaquina') || 'null'),
          config_layers: JSON.parse(localStorage.getItem('configLayers') || '[]'),
          sobras_ids: JSON.parse(localStorage.getItem('sobrasSelecionadas') || '[]'),
        }),
      });
      if (resp?.pasta_resultado) {
        localStorage.setItem(`nestingPreview_${resp.pasta_resultado}`, JSON.stringify(chapas));
      }
      localStorage.removeItem('sobrasSelecionadas');
      setConfirmado(true);
    } catch (e) {
      alert('Falha ao confirmar');
    }
    setEnviando(false);
  };

  const desfazer = () => {
    const cfg = localStorage.getItem('ultimaExecucaoNesting');
    if (cfg) {
      try {
        const params = JSON.parse(cfg);
        fetchComAuth('/limpar-nesting-preview', {
          method: 'POST',
          body: JSON.stringify({ pasta_lote: params.pastaLote })
        }).catch(() => {});
      } catch {}
    }
    localStorage.removeItem('ultimaExecucaoNesting');
    localStorage.removeItem('visualizarNestingObjKey');
    setChapas([]);
  };

  useEffect(() => {
    return () => {
      if (!confirmado) {
        const cfg = localStorage.getItem('ultimaExecucaoNesting');
        if (cfg) {
          try {
            const params = JSON.parse(cfg);
            fetchComAuth('/limpar-nesting-preview', {
              method: 'POST',
              body: JSON.stringify({ pasta_lote: params.pastaLote })
            }).catch(() => {});
          } catch {}
        }
      }
      localStorage.removeItem('visualizarNestingObjKey');
    };
  }, [confirmado]);

  return (
    <div className="p-6 space-y-4">
      <h2 className="text-lg font-semibold">Visualização de Nesting</h2>
      <FiltroChapa
        descricao={descricao}
        setDescricao={setDescricao}
        opcoesDescricao={materiais}
      />
      <div className="flex flex-wrap gap-4 items-center">
        <Button
          variant="outline"
          size="sm"
          disabled={indice === 0}
          onClick={() => setIndice((i) => Math.max(i - 1, 0))}
        >
          ◀
        </Button>
        {chapaAtual && (
          <div key={chapaAtual.id} className="flex gap-4 items-start w-full">
            <ChapaViewer
              chapa={chapaAtual}
              width={larguraViewer}
              onSelect={(op) => {
                setSelecionada(op);
                setDestaque(op.id);
              }}
              destaqueId={destaque}
            />
            <div className="w-72">
              <OperacaoList
                operacoes={chapaAtual.operacoes}
                onSelect={(op) => {
                  setSelecionada(op);
                  setDestaque(op.id);
                }}
                destaqueId={destaque}
              />
            </div>
          </div>
        )}
        <Button
          variant="outline"
          size="sm"
          disabled={indice >= filtradas.length - 1}
          onClick={() => setIndice((i) => Math.min(i + 1, filtradas.length - 1))}
        >
          ▶
        </Button>
      </div>
      <div className="pt-4 space-x-2">
        <Button disabled={confirmado || enviando} onClick={confirmar}>
          Confirmar e Gerar Arquivos
        </Button>
        <Button variant="outline" onClick={desfazer}>
          Desfazer Otimização Nesting
        </Button>
        {confirmado && <span className="ml-2 text-green-600">Concluído!</span>}
      </div>
      <OperacaoDetailModal operacao={selecionada} onClose={() => setSelecionada(null)} />
    </div>
  );
};

export default VisualizacaoNesting;
