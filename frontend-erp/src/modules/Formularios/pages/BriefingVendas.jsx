import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button } from '../../Producao/components/ui/button';
import { fetchComAuth } from '../../../utils/fetchComAuth';

const AMBIENTES_SUGERIDOS = [
  'Cozinha',
  'Banheiros/Lavabo',
  'Dormitório Casal',
  'Dormitório Solteiro',
  'Dormitório Bebê',
  'Home Office',
  'Sala de Estar',
  'Lavanderia',
];

const ITENS_POR_AMBIENTE = {
  'Cozinha': ['Forno', 'Cooktop', 'Depurador', 'Porta Latas', 'Micro-ondas', 'Lava-louças', 'Outros'],
  'Banheiros/Lavabo': ['Espelho', 'Nicho', 'Armário', 'Outros'],
  'Dormitório Bebê': ['Cômoda', 'Prateleira', 'Berço', 'Outros'],
};

function BriefingVendas() {
  const { atendimentoId, tarefaId } = useParams();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    vendedor: '',
    cliente: '',
    telefone: '',
    email: '',
    rua: '',
    numero: '',
    cidade: '',
    estado: '',
    cep: '',
    ambientes: [],
    origem: [],
    origemOutro: '',
    melhorHorario: '',
    situacaoConstrucao: '',
    obsEspecial: '',
    observacoes: '',
  });
  const [planta, setPlanta] = useState(null);
  const [referencias, setReferencias] = useState([]);
  const [ambientesExtras, setAmbientesExtras] = useState([]);
  const [novoAmb, setNovoAmb] = useState('');
  const [dadosAmbientes, setDadosAmbientes] = useState({});
  const [carregado, setCarregado] = useState(false);
  const [dirty, setDirty] = useState(false);

  useEffect(() => {
    const carregar = async () => {
      const at = await fetchComAuth(`/comercial/atendimentos/${atendimentoId}`);
      const ts = await fetchComAuth(`/comercial/atendimentos/${atendimentoId}/tarefas`);
      const tarefa = (ts.tarefas || []).find(t => String(t.id) === String(tarefaId));
      let dadosExist = {};
      try { dadosExist = tarefa && tarefa.dados ? JSON.parse(tarefa.dados) : {}; } catch {}
      setForm(prev => ({
        ...prev,
        ...(dadosExist.form || {}),
        cliente: at.atendimento.cliente || '',
        ambientes: (dadosExist.form?.ambientes) || (at.atendimento.projetos ? at.atendimento.projetos.split(',').map(p => p.trim()).filter(Boolean) : []),
      }));
      setDadosAmbientes(dadosExist.dadosAmbientes || {});
      setCarregado(true);
    };
    carregar();
  }, [atendimentoId, tarefaId]);

  useEffect(() => { setDirty(true); }, [form, dadosAmbientes, planta, referencias]);

  const toggleAmbiente = amb => {
    setForm(f => {
      const lista = f.ambientes.includes(amb) ? f.ambientes.filter(a => a !== amb) : [...f.ambientes, amb];
      return { ...f, ambientes: lista };
    });
  };

  const handleAmbData = (amb, campo, valor) => {
    setDadosAmbientes(prev => ({ ...prev, [amb]: { ...prev[amb], [campo]: valor } }));
  };

  const salvar = async () => {
    const dados = { form, dadosAmbientes };
    await fetchComAuth(`/comercial/atendimentos/${atendimentoId}/tarefas/${tarefaId}`, {
      method: 'PUT',
      body: JSON.stringify({ concluida: true, dados: JSON.stringify(dados) }),
    });
    navigate(`/comercial/${atendimentoId}`);
  };

  const sair = () => {
    if (dirty && !window.confirm('Deseja sair sem salvar?')) return;
    navigate(`/comercial/${atendimentoId}`);
  };

  if (!carregado) return <p>Carregando...</p>;

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">Briefing de Vendas</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <label className="block">
          <span className="text-sm">Vendedor Responsável*</span>
          <input className="input" value={form.vendedor} onChange={e => setForm({ ...form, vendedor: e.target.value })} />
        </label>
        <label className="block">
          <span className="text-sm">Nome do Cliente*</span>
          <input className="input" value={form.cliente} onChange={e => setForm({ ...form, cliente: e.target.value })} />
        </label>
        <label className="block">
          <span className="text-sm">Telefone*</span>
          <input className="input" value={form.telefone} onChange={e => setForm({ ...form, telefone: e.target.value })} />
        </label>
        <label className="block">
          <span className="text-sm">E-mail*</span>
          <input type="email" className="input" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} />
        </label>
        <label className="block">
          <span className="text-sm">Rua*</span>
          <input className="input" value={form.rua} onChange={e => setForm({ ...form, rua: e.target.value })} />
        </label>
        <label className="block">
          <span className="text-sm">Número*</span>
          <input className="input" value={form.numero} onChange={e => setForm({ ...form, numero: e.target.value })} />
        </label>
        <label className="block">
          <span className="text-sm">Cidade*</span>
          <input className="input" value={form.cidade} onChange={e => setForm({ ...form, cidade: e.target.value })} />
        </label>
        <label className="block">
          <span className="text-sm">Estado*</span>
          <input className="input" value={form.estado} onChange={e => setForm({ ...form, estado: e.target.value })} />
        </label>
        <label className="block">
          <span className="text-sm">CEP*</span>
          <input className="input" value={form.cep} onChange={e => setForm({ ...form, cep: e.target.value })} />
        </label>
        <div className="block md:col-span-2">
          <span className="text-sm">Quais ambientes deseja planejar?*</span>
          <div className="flex flex-wrap gap-4 mt-1">
            {AMBIENTES_SUGERIDOS.concat(ambientesExtras).map(a => (
              <label key={a} className="flex items-center gap-1">
                <input type="checkbox" checked={form.ambientes.includes(a)} onChange={() => toggleAmbiente(a)} />
                {a}
              </label>
            ))}
          </div>
          <div className="flex items-center gap-2 mt-2">
            <input className="input flex-grow" placeholder="Adicionar ambiente" value={novoAmb} onChange={e => setNovoAmb(e.target.value)} />
            <Button size="sm" onClick={() => { if (novoAmb.trim()) { setAmbientesExtras(prev => [...prev, novoAmb.trim()]); toggleAmbiente(novoAmb.trim()); setNovoAmb(''); } }}>Adicionar</Button>
          </div>
        </div>
        <label className="block md:col-span-2">
          <span className="text-sm">Como chegou até nós?</span>
          <div className="flex flex-wrap gap-4">
            {['Google', 'Indicação', 'Instagram', 'Outros'].map(op => (
              <label key={op} className="flex items-center gap-1">
                <input type="checkbox" checked={form.origem.includes(op)} onChange={() => setForm(prev => ({ ...prev, origem: prev.origem.includes(op) ? prev.origem.filter(o => o !== op) : [...prev.origem, op] }))} />
                {op}
              </label>
            ))}
          </div>
          {form.origem.includes('Outros') && (
            <input className="input mt-1" value={form.origemOutro} onChange={e => setForm({ ...form, origemOutro: e.target.value })} />
          )}
        </label>
        <label className="block">
          <span className="text-sm">Melhor horário para contato</span>
          <input className="input" value={form.melhorHorario} onChange={e => setForm({ ...form, melhorHorario: e.target.value })} />
        </label>
        <label className="block">
          <span className="text-sm">Situação Atual da Construção</span>
          <select className="input" value={form.situacaoConstrucao} onChange={e => setForm({ ...form, situacaoConstrucao: e.target.value })}>
            <option value="">Selecione</option>
            <option>início de obra</option>
            <option>reboco</option>
            <option>acabamentos</option>
            <option>em reforma</option>
            <option>pronto/habitado</option>
          </select>
        </label>
        <label className="block">
          <span className="text-sm">Possui planta baixa ou esboço?</span>
          <input type="file" className="input" accept=".pdf,.jpg,.png" onChange={e => setPlanta(e.target.files[0])} />
        </label>
      </div>

      {form.ambientes.map(amb => (
        <div key={amb} className="border-t pt-4 space-y-2">
          <h4 className="font-medium">{amb}</h4>
          <label className="block">
            <span className="text-sm">Estilo desejado</span>
            <div className="flex flex-wrap gap-4">
              {['Madeira', 'Branco', 'Moderno', 'Outro'].map(op => (
                <label key={op} className="flex items-center gap-1">
                  <input
                    type="checkbox"
                    checked={dadosAmbientes[amb]?.estilo?.includes(op)}
                    onChange={() => {
                      const atual = dadosAmbientes[amb]?.estilo || [];
                      const nova = atual.includes(op) ? atual.filter(o => o !== op) : [...atual, op];
                      handleAmbData(amb, 'estilo', nova);
                    }}
                  />
                  {op}
                </label>
              ))}
            </div>
            {dadosAmbientes[amb]?.estilo?.includes('Outro') && (
              <input className="input mt-1" value={dadosAmbientes[amb]?.estiloOutro || ''} onChange={e => handleAmbData(amb, 'estiloOutro', e.target.value)} />
            )}
          </label>
          <label className="block">
            <span className="text-sm">Itens desejados</span>
            <div className="flex flex-wrap gap-4">
              {(ITENS_POR_AMBIENTE[amb] || ['Outros']).map(op => (
                <label key={op} className="flex items-center gap-1">
                  <input
                    type="checkbox"
                    checked={dadosAmbientes[amb]?.itens?.includes(op)}
                    onChange={() => {
                      const atual = dadosAmbientes[amb]?.itens || [];
                      const nova = atual.includes(op) ? atual.filter(o => o !== op) : [...atual, op];
                      handleAmbData(amb, 'itens', nova);
                    }}
                  />
                  {op}
                </label>
              ))}
            </div>
            {dadosAmbientes[amb]?.itens?.includes('Outros') && (
              <input className="input mt-1" value={dadosAmbientes[amb]?.itensOutro || ''} onChange={e => handleAmbData(amb, 'itensOutro', e.target.value)} />
            )}
          </label>
          <label className="block">
            <span className="text-sm">Tipo/Cor de MDF</span>
            <textarea className="input" rows="2" value={dadosAmbientes[amb]?.mdf || ''} onChange={e => handleAmbData(amb, 'mdf', e.target.value)} />
          </label>
          <label className="block">
            <span className="text-sm">Puxadores</span>
            <div className="flex flex-wrap gap-4">
              {['Perfil slim', 'Puxador cava', 'Outro'].map(op => (
                <label key={op} className="flex items-center gap-1">
                  <input
                    type="checkbox"
                    checked={dadosAmbientes[amb]?.puxadores?.includes(op)}
                    onChange={() => {
                      const atual = dadosAmbientes[amb]?.puxadores || [];
                      const nova = atual.includes(op) ? atual.filter(o => o !== op) : [...atual, op];
                      handleAmbData(amb, 'puxadores', nova);
                    }}
                  />
                  {op}
                </label>
              ))}
            </div>
            {dadosAmbientes[amb]?.puxadores?.includes('Outro') && (
              <input className="input mt-1" value={dadosAmbientes[amb]?.puxadorOutro || ''} onChange={e => handleAmbData(amb, 'puxadorOutro', e.target.value)} />
            )}
          </label>
          <label className="block">
            <span className="text-sm">Tampos e Bancadas</span>
            <div className="flex items-center gap-4">
              {['Granito', 'Mármore', 'Outro'].map(op => (
                <label key={op} className="flex items-center gap-1">
                  <input type="radio" name={`tampos-${amb}`} checked={dadosAmbientes[amb]?.tampos === op} onChange={() => handleAmbData(amb, 'tampos', op)} />
                  {op}
                </label>
              ))}
            </div>
            {dadosAmbientes[amb]?.tampos === 'Outro' && (
              <input className="input mt-1" value={dadosAmbientes[amb]?.tamposOutro || ''} onChange={e => handleAmbData(amb, 'tamposOutro', e.target.value)} />
            )}
          </label>
          <label className="block">
            <span className="text-sm">Possui fotos de referência?</span>
            <input type="file" multiple className="input" accept=".pdf,.jpg,.png" onChange={e => handleAmbData(amb, 'fotos', Array.from(e.target.files))} />
          </label>
          <label className="block">
            <span className="text-sm">O que considera indispensável nesse ambiente?</span>
            <textarea className="input" rows="2" value={dadosAmbientes[amb]?.indispensavel || ''} onChange={e => handleAmbData(amb, 'indispensavel', e.target.value)} />
          </label>
        </div>
      ))}

      <div className="border-t pt-4 space-y-2">
        <label className="block">
          <span className="text-sm">Alguma necessidade especial?</span>
          <textarea className="input" rows="3" value={form.obsEspecial} onChange={e => setForm({ ...form, obsEspecial: e.target.value })} />
        </label>
        <label className="block">
          <span className="text-sm">Possui referências?</span>
          <input type="file" multiple className="input" accept=".pdf,.jpg,.png" onChange={e => setReferencias(Array.from(e.target.files))} />
        </label>
        <label className="block">
          <span className="text-sm">Observações finais</span>
          <textarea className="input" rows="3" value={form.observacoes} onChange={e => setForm({ ...form, observacoes: e.target.value })} />
        </label>
      </div>

      <div className="flex gap-2">
        <Button onClick={salvar}>Salvar</Button>
        <Button variant="secondary" onClick={sair}>Sair</Button>
      </div>
    </div>
  );
}

export default BriefingVendas;
