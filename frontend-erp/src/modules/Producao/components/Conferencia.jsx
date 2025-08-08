import React, { useState } from 'react';
import { Button } from './ui/button';

// Usuários habilitados (placeholder)
const usuarios = ['Alice', 'Bob', 'Carlos'];

// Configuração de prazos em dias para cada tarefa
const PRAZOS = {
  'Agendamento de Medição': 2,
  'Medição Final': 2,
  'Conferência Final': 1,
  'Detalhamento de Produção': 2,
  'Pedidos Diversos': 1,
  'Detalhamento de Montagem': 2,
};

const addDays = (dateStr, days) => {
  const d = new Date(dateStr);
  d.setDate(d.getDate() + days);
  return d.toISOString().slice(0, 10);
};

const initialTasks = Object.keys(PRAZOS).map(nome => ({
  nome,
  responsavel: '',
  previsao: '',
  concluida: false,
  dados: {},
  historico: [],
  obsDraft: '',
}));

export default function Conferencia() {
  const [tarefas, setTarefas] = useState(initialTasks);
  const [mostrarHistorico, setMostrarHistorico] = useState(null);

  const handleField = (idx, field, value) => {
    setTarefas(tfs => {
      const novo = [...tfs];
      novo[idx][field] = value;
      return novo;
    });
  };

  const handleDados = (idx, campo, valor) => {
    setTarefas(tfs => {
      const novo = [...tfs];
      novo[idx].dados = { ...novo[idx].dados, [campo]: valor };
      return novo;
    });
  };

  const addObs = idx => {
    const texto = tarefas[idx].obsDraft?.trim();
    if (!texto) return;
    const registro = { texto, data: new Date().toLocaleString() };
    setTarefas(tfs => {
      const novo = [...tfs];
      novo[idx].historico = [...novo[idx].historico, registro];
      novo[idx].obsDraft = '';
      return novo;
    });
  };

  const finalizar = idx => {
    setTarefas(tfs => {
      const novo = [...tfs];
      novo[idx].concluida = true;
      const hoje = new Date().toISOString().slice(0, 10);
      novo[idx].dados.conclusao = hoje;
      if (novo[idx + 1]) {
        const nextDate = addDays(hoje, PRAZOS[novo[idx + 1].nome]);
        if (!novo[idx + 1].previsao) novo[idx + 1].previsao = nextDate;
      }
      return novo;
    });
  };

  const historicoVisible = idx => mostrarHistorico === idx;

  const allUploads = items => items.every(it => tarefas[it.idx].dados[it.campo]);

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-bold">Tarefas da Conferência</h3>
      <ul className="space-y-4">
        {tarefas.map((t, idx) => {
          const renderObs = t.nome === 'Agendamento de Medição' || t.nome === 'Conferência Final';
          const podeFinalizar = (() => {
            switch (t.nome) {
              case 'Agendamento de Medição':
                return Boolean(t.dados.data_agendada);
              case 'Medição Final':
                return Boolean(t.dados.ficha_upload);
              case 'Conferência Final':
                return t.dados.revisao_layout && t.dados.revisao_mobiliario && t.historico.length > 0;
              case 'Detalhamento de Produção':
                return Boolean(t.dados.detalhamento_upload);
              case 'Pedidos Diversos':
                return (t.dados.pedidos || []).length > 0 && (t.dados.pedidos || []).every(p => p.arquivo);
              case 'Detalhamento de Montagem':
                return Boolean(t.dados.montagem_upload);
              default:
                return false;
            }
          })();

          return (
            <li key={t.nome} className={`p-4 border rounded ${t.concluida ? 'bg-green-200' : 'bg-yellow-100'}`}>
              <div className="font-medium">{t.nome}</div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2 mt-2">
                <label className="flex flex-col text-sm">
                  Responsável
                  <select
                    className="input"
                    value={t.responsavel}
                    onChange={e => handleField(idx, 'responsavel', e.target.value)}
                  >
                    <option value="">Selecione</option>
                    {usuarios.map(u => (
                      <option key={u} value={u}>{u}</option>
                    ))}
                  </select>
                </label>
                <label className="flex flex-col text-sm">
                  Previsão de Finalização
                  <input
                    type="date"
                    className="input"
                    value={t.previsao}
                    onChange={e => handleField(idx, 'previsao', e.target.value)}
                  />
                </label>
              </div>

              {t.nome === 'Agendamento de Medição' && (
                <div className="mt-2 space-y-2">
                  <label className="flex flex-col text-sm">
                    Data Agendada
                    <input
                      type="date"
                      className="input"
                      value={t.dados.data_agendada || ''}
                      onChange={e => handleDados(idx, 'data_agendada', e.target.value)}
                    />
                  </label>
                  <textarea
                    className="input"
                    rows="2"
                    placeholder="Observação"
                    value={t.obsDraft}
                    onChange={e => handleField(idx, 'obsDraft', e.target.value)}
                  />
                  <Button size="sm" className="bg-white text-black" onClick={() => addObs(idx)}>
                    Adicionar Observação
                  </Button>
                </div>
              )}

              {t.nome === 'Medição Final' && (
                <div className="mt-2 space-y-2">
                  <a
                    href="#"
                    className="text-blue-600 underline text-sm"
                    download
                  >
                    Baixar Ficha de Medidas
                  </a>
                  <input
                    type="file"
                    accept=".pdf,.doc,.docx"
                    onChange={e => handleDados(idx, 'ficha_upload', e.target.files[0]?.name)}
                  />
                  {t.dados.ficha_upload && (
                    <div className="text-sm text-gray-700">{t.dados.ficha_upload}</div>
                  )}
                </div>
              )}

              {t.nome === 'Conferência Final' && (
                <div className="mt-2 space-y-2">
                  <label className="flex items-center gap-2 text-sm">
                    <input
                      type="checkbox"
                      checked={t.dados.revisao_layout || false}
                      onChange={e => handleDados(idx, 'revisao_layout', e.target.checked)}
                    />
                    Revisão das Medidas do Layout
                  </label>
                  <label className="flex items-center gap-2 text-sm">
                    <input
                      type="checkbox"
                      checked={t.dados.revisao_mobiliario || false}
                      onChange={e => handleDados(idx, 'revisao_mobiliario', e.target.checked)}
                    />
                    Revisão do projeto de mobiliário
                  </label>
                  <textarea
                    className="input"
                    rows="2"
                    placeholder="Observação"
                    value={t.obsDraft}
                    onChange={e => handleField(idx, 'obsDraft', e.target.value)}
                  />
                  <div className="flex gap-2">
                    <Button size="sm" className="bg-white text-black" onClick={() => addObs(idx)}>
                      Adicionar Observação
                    </Button>
                    <Button
                      size="sm"
                      className="bg-white text-black"
                      onClick={() => setMostrarHistorico(historicoVisible(idx) ? null : idx)}
                    >
                      Histórico da Conferência
                    </Button>
                  </div>
                  {historicoVisible(idx) && (
                    <ul className="text-sm list-disc ml-4">
                      {t.historico.map((h, i) => (
                        <li key={i}>{h.data} - {h.texto}</li>
                      ))}
                    </ul>
                  )}
                </div>
              )}

              {t.nome === 'Detalhamento de Produção' && (
                <div className="mt-2">
                  <input
                    type="file"
                    onChange={e => handleDados(idx, 'detalhamento_upload', e.target.files[0]?.name)}
                  />
                  {t.dados.detalhamento_upload && (
                    <div className="text-sm text-gray-700">{t.dados.detalhamento_upload}</div>
                  )}
                </div>
              )}

              {t.nome === 'Pedidos Diversos' && (
                <div className="mt-2 space-y-2">
                  {(() => {
                    const itens = t.dados.pedidos || ['Custo Adicional 1', 'Custo Adicional 2'].map((label, i) => ({ label, arquivo: null }));
                    if (!t.dados.pedidos) handleDados(idx, 'pedidos', itens);
                    return itens.map((item, i) => (
                      <div key={i} className="flex items-center gap-2">
                        <span className="text-sm">{item.label}</span>
                        <input
                          type="file"
                          onChange={e => {
                            const nome = e.target.files[0]?.name;
                            setTarefas(tfs => {
                              const novo = [...tfs];
                              const list = [...(novo[idx].dados.pedidos || [])];
                              list[i] = { ...list[i], arquivo: nome };
                              novo[idx].dados = { ...novo[idx].dados, pedidos: list };
                              return novo;
                            });
                          }}
                        />
                        {item.arquivo && <span className="text-xs text-gray-700">{item.arquivo}</span>}
                      </div>
                    ));
                  })()}
                </div>
              )}

              {t.nome === 'Detalhamento de Montagem' && (
                <div className="mt-2">
                  <input
                    type="file"
                    onChange={e => handleDados(idx, 'montagem_upload', e.target.files[0]?.name)}
                  />
                  {t.dados.montagem_upload && (
                    <div className="text-sm text-gray-700">{t.dados.montagem_upload}</div>
                  )}
                </div>
              )}

              {renderObs && t.nome !== 'Conferência Final' && t.historico.length > 0 && (
                <ul className="text-sm list-disc ml-4 mt-2">
                  {t.historico.map((h, i) => (
                    <li key={i}>{h.data} - {h.texto}</li>
                  ))}
                </ul>
              )}

              <div className="mt-2">
                <Button
                  size="sm"
                  className="bg-blue-600 text-white"
                  disabled={!podeFinalizar || t.concluida}
                  onClick={() => finalizar(idx)}
                >
                  Finalizar
                </Button>
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

