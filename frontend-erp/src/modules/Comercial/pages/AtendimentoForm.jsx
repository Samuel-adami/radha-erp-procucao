import React, { useState, useEffect } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import { Button } from '../../Producao/components/ui/button';
import { fetchComAuth } from '../../../utils/fetchComAuth';

const PROJETOS = [
  'Cozinha',
  'Banheiro',
  'Lavabo',
  'B. Social',
  'B. Suíte',
  'Lavanderia',
  'D. Casal',
  'Suíte',
  'Closet',
  'Home Office',
  'A. Gourmet',
  'D. Solteiro',
  'D. Hóspedes',
  'D. Infantil',
  'D. Bebê',
  'Ambiente Comercial',
];

function AtendimentoForm() {
  const [form, setForm] = useState({
    cliente: '',
    codigo: '',
    procedencia: '',
    vendedor: '',
    telefone: '',
    email: '',
    rua: '',
    numero: '',
    complemento: '',
    bairro: '',
    cidade: '',
    estado: '',
    cep: '',
    projetos: [],
    previsao_fechamento: '',
    temperatura: '',
    tem_especificador: false,
    especificador_nome: '',
    rt_percent: '',
    entrega_diferente: '',
    historico: '',
  });
  const [initialForm, setInitialForm] = useState({
    cliente: '',
    codigo: '',
    procedencia: '',
    vendedor: '',
    telefone: '',
    email: '',
    rua: '',
    numero: '',
    complemento: '',
    bairro: '',
    cidade: '',
    estado: '',
    cep: '',
    projetos: [],
    previsao_fechamento: '',
    temperatura: '',
    tem_especificador: false,
    especificador_nome: '',
    rt_percent: '',
    entrega_diferente: '',
    historico: '',
  });
  const [files, setFiles] = useState([]);
  const [sugestoesClientes, setSugestoesClientes] = useState([]);
  const [clienteInfo, setClienteInfo] = useState(null);
  const [sequencial, setSequencial] = useState(1);
  const [projetosOpen, setProjetosOpen] = useState(false);
  const [entregaOpcao, setEntregaOpcao] = useState('');
  const navigate = useNavigate();
  const { id } = useParams();

  useEffect(() => {
    setEntregaOpcao(form.entrega_diferente || '');
  }, [form.entrega_diferente]);

  useEffect(() => {
    const seq = parseInt(localStorage.getItem('atendimentoCodigoSeq') || '1', 10);
    setSequencial(seq);
    setInitialForm({
      cliente: '',
      codigo: '',
      procedencia: '',
      vendedor: '',
      telefone: '',
      email: '',
      rua: '',
      numero: '',
      complemento: '',
      bairro: '',
      cidade: '',
      estado: '',
      cep: '',
      projetos: [],
      previsao_fechamento: '',
      temperatura: '',
      tem_especificador: false,
      especificador_nome: '',
      rt_percent: '',
      entrega_diferente: '',
      historico: '',
    });
  }, []);

  useEffect(() => {
    if (!id) return;
    const carregar = async () => {
      try {
        const dados = await fetchComAuth(`/comercial/atendimentos/${id}`);
        const at = dados.atendimento;
        setForm({
          cliente: at.cliente || '',
          codigo: at.codigo || '',
          procedencia: at.procedencia || '',
          vendedor: at.vendedor || '',
          telefone: at.telefone || '',
          email: at.email || '',
          rua: at.rua || '',
          numero: at.numero || '',
          complemento: at.complemento || '',
          bairro: at.bairro || '',
          cidade: at.cidade || '',
          estado: at.estado || '',
          cep: at.cep || '',
          projetos: at.projetos ? at.projetos.split(',').map(p => p.trim()).filter(Boolean) : [],
          previsao_fechamento: at.previsao_fechamento || '',
          temperatura: at.temperatura || '',
          tem_especificador: Boolean(at.tem_especificador),
          especificador_nome: at.especificador_nome || '',
          rt_percent: at.rt_percent || '',
          entrega_diferente: at.entrega_diferente || '',
          historico: at.historico || '',
        });
        setInitialForm({
          cliente: at.cliente || '',
          codigo: at.codigo || '',
          procedencia: at.procedencia || '',
          vendedor: at.vendedor || '',
          telefone: at.telefone || '',
          email: at.email || '',
          rua: at.rua || '',
          numero: at.numero || '',
          complemento: at.complemento || '',
          bairro: at.bairro || '',
          cidade: at.cidade || '',
          estado: at.estado || '',
          cep: at.cep || '',
          projetos: at.projetos ? at.projetos.split(',').map(p => p.trim()).filter(Boolean) : [],
          previsao_fechamento: at.previsao_fechamento || '',
          temperatura: at.temperatura || '',
          tem_especificador: Boolean(at.tem_especificador),
          especificador_nome: at.especificador_nome || '',
          rt_percent: at.rt_percent || '',
          entrega_diferente: at.entrega_diferente || '',
          historico: at.historico || '',
        });
      } catch (err) {
        console.error('Erro ao carregar atendimento', err);
      }
    };
    carregar();
  }, [id]);

  useEffect(() => {
    if (!form.cliente) return;
    const lista = JSON.parse(localStorage.getItem('clientes') || '[]');
    const encontrado = lista.find(c => c.nome === form.cliente);
    setClienteInfo(encontrado || null);
  }, [form.cliente, id]);

  useEffect(() => {
    if (entregaOpcao === 'Sim' && clienteInfo) {
      setForm(prev => ({
        ...prev,
        rua: clienteInfo.endereco || '',
        numero: clienteInfo.numero || '',
        complemento: clienteInfo.complemento || '',
        bairro: clienteInfo.bairro || '',
        cidade: clienteInfo.cidade || '',
        estado: clienteInfo.estado || '',
        cep: clienteInfo.cep || '',
      }));
    }
  }, [clienteInfo, entregaOpcao]);

  useEffect(() => {
    if (id) return;
    const codigo = `AT-${String(sequencial).padStart(4, '0')}`;
    setForm(prev => ({ ...prev, codigo }));
  }, [sequencial, id]);

  const handle = campo => e => {
    let value = e.target.value;
    if (campo === 'tem_especificador') {
      value = value === 'Sim';
    }
    setForm(prev => ({ ...prev, [campo]: value }));
  };

  const handleProjetosToggle = projeto => {
    setForm(prev => {
      const selecionados = prev.projetos.includes(projeto)
        ? prev.projetos.filter(p => p !== projeto)
        : [...prev.projetos, projeto];
      return { ...prev, projetos: selecionados };
    });
  };

  const handleClienteChange = e => {
    const value = e.target.value;
    setForm(prev => ({ ...prev, cliente: value }));
    const lista = JSON.parse(localStorage.getItem('clientes') || '[]');
    if (value.length >= 3) {
      const termo = value.toLowerCase();
      setSugestoesClientes(
        lista.filter(c => c.nome && c.nome.toLowerCase().startsWith(termo))
      );
    } else {
      setSugestoesClientes([]);
    }
    const encontrado = lista.find(c => c.nome === value);
    setClienteInfo(encontrado || null);
    if (encontrado) {
      setForm(prev => ({
        ...prev,
        procedencia: encontrado.procedencia || '',
        telefone: encontrado.telefone1 || '',
        email: encontrado.email || '',
        rua: encontrado.endereco || '',
        numero: encontrado.numero || '',
        complemento: encontrado.complemento || '',
        bairro: encontrado.bairro || '',
        cidade: encontrado.cidade || '',
        estado: encontrado.estado || '',
        cep: encontrado.cep || '',
      }));
    }
  };

  const handleEntregaOpcao = e => {
    const val = e.target.value;
    setEntregaOpcao(val);
    if (val === 'Sim' && clienteInfo) {
      setForm(prev => ({
        ...prev,
        entrega_diferente: val,
        rua: clienteInfo.endereco || '',
        numero: clienteInfo.numero || '',
        complemento: clienteInfo.complemento || '',
        bairro: clienteInfo.bairro || '',
        cidade: clienteInfo.cidade || '',
        estado: clienteInfo.estado || '',
        cep: clienteInfo.cep || '',
      }));
    } else if (val === 'Não') {
      setForm(prev => ({
        ...prev,
        entrega_diferente: val,
        rua: '',
        numero: '',
        complemento: '',
        bairro: '',
        cidade: '',
        estado: '',
        cep: '',
      }));
    } else {
      setForm(prev => ({ ...prev, entrega_diferente: val }));
    }
  };

  const handleFileChange = async e => {
    const fileList = Array.from(e.target.files || []);
    const lidos = await Promise.all(
      fileList.map(
        f =>
          new Promise(resolve => {
            const reader = new FileReader();
            reader.onload = ev => resolve({ nome: f.name, conteudo: ev.target.result });
            reader.readAsDataURL(f);
          })
      )
    );
    setFiles(lidos);
  };

  const salvar = async () => {
    const payload = {
      ...form,
      projetos: form.projetos.join(','),
      tem_especificador: form.tem_especificador ? 1 : 0,
      arquivos: files,
    };
    if (id) {
      await fetchComAuth(`/comercial/atendimentos/${id}`, {
        method: 'PUT',
        body: JSON.stringify(payload),
      });
    } else {
      await fetchComAuth('/comercial/atendimentos', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
      localStorage.setItem('atendimentoCodigoSeq', String(sequencial + 1));
      setSequencial(s => s + 1);
    }
  };

  const handleSubmit = async e => {
    e.preventDefault();
    try {
      await salvar();
      navigate('..');
    } catch (err) {
      console.error('Erro ao salvar atendimento', err);
    }
  };

  const handleSair = async () => {
    const changed =
      JSON.stringify(form) !== JSON.stringify(initialForm) || files.length > 0;
    if (changed) {
      const salvarAntes = window.confirm('Deseja salvar o formulário antes de sair?');
      if (salvarAntes) {
        try {
          await salvar();
        } catch (err) {
          console.error('Erro ao salvar atendimento', err);
        }
      }
    }
    navigate('..');
  };

  useEffect(() => {
    const fechar = e => {
      if (!e.target.closest('.projetos-select')) {
        setProjetosOpen(false);
      }
    };
    document.addEventListener('click', fechar);
    return () => document.removeEventListener('click', fechar);
  }, []);

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {clienteInfo && (
        <div className="p-2 bg-gray-100 rounded text-sm space-y-1">
          <div className="flex justify-between items-start">
            <div>
              <div className="font-semibold">{clienteInfo.nome}</div>
              <div>CPF/CNPJ: {clienteInfo.documento}</div>
              <div>Tel: {clienteInfo.telefone1}</div>
              <div>Email: {clienteInfo.email}</div>
              <div>
                {clienteInfo.endereco} {clienteInfo.numero}
                {clienteInfo.complemento ? ` - ${clienteInfo.complemento}` : ''} - {clienteInfo.bairro}
              </div>
              <div>
                {clienteInfo.cidade}/{clienteInfo.estado}
              </div>
            </div>
            <Link
              to={`/cadastros/clientes/editar/${clienteInfo.id}`}
              className="px-2 py-1 text-sm rounded bg-blue-600 text-white"
            >
              Editar
            </Link>
          </div>
        </div>
      )}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <label className="block">
          <span className="text-sm">Cliente</span>
          <input
            className="input"
            list="lista-clientes"
            value={form.cliente}
            onChange={handleClienteChange}
          />
          <datalist id="lista-clientes">
            {sugestoesClientes.map(c => (
              <option key={c.id} value={c.nome} />
            ))}
          </datalist>
        </label>
        <label className="block">
          <span className="text-sm">Vendedor Responsável</span>
          <input className="input" value={form.vendedor} onChange={handle('vendedor')} />
        </label>
        <label className="block">
          <span className="text-sm">Como chegou até nós?</span>
          <select className="input" value={form.procedencia} onChange={handle('procedencia')}>
            <option value="">Selecione</option>
            <option>Google</option>
            <option>Instagram</option>
            <option>Facebook</option>
            <option>Indicação Clientes</option>
            <option>Indicação Corretor</option>
            <option>Indicação Arquiteto</option>
            <option>Ja é Cliente</option>
            <option>Vitrine</option>
            <option>Telefone</option>
            <option>Outros</option>
          </select>
        </label>
        <label className="block">
          <span className="text-sm">Código</span>
          <input
            className="input bg-gray-100"
            value={form.codigo}
            readOnly
          />
        </label>
        <div className="block md:col-span-2 projetos-select relative">
          <span className="text-sm">Projetos do Atendimento</span>
          <div
            className="input cursor-pointer"
            onClick={() => setProjetosOpen(o => !o)}
          >
            {form.projetos.length ? form.projetos.join(', ') : 'Selecione'}
          </div>
          {projetosOpen && (
            <div className="absolute z-10 mt-1 bg-white border rounded shadow max-h-60 overflow-auto w-full">
              {PROJETOS.map(p => (
                <label key={p} className="block px-2 py-1 hover:bg-gray-100">
                  <input
                    type="checkbox"
                    className="mr-2"
                    checked={form.projetos.includes(p)}
                    onChange={() => handleProjetosToggle(p)}
                  />
                  {p}
                </label>
              ))}
            </div>
          )}
        </div>
      </div>
      <label className="block">
        <span className="text-sm">Endereço de entrega é o mesmo do cadastro?</span>
        <select className="input" value={entregaOpcao} onChange={handleEntregaOpcao}>
          <option value="">Selecione</option>
          <option>Sim</option>
          <option>Não</option>
        </select>
      </label>
      {entregaOpcao && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <label className="block">
            <span className="text-sm">Rua</span>
            <input className="input" value={form.rua} onChange={handle('rua')} />
          </label>
          <label className="block">
            <span className="text-sm">Número</span>
            <input className="input" value={form.numero} onChange={handle('numero')} />
          </label>
          <label className="block">
            <span className="text-sm">Complemento</span>
            <input className="input" value={form.complemento} onChange={handle('complemento')} />
          </label>
          <label className="block">
            <span className="text-sm">Bairro</span>
            <input className="input" value={form.bairro} onChange={handle('bairro')} />
          </label>
          <label className="block">
            <span className="text-sm">Cidade</span>
            <input className="input" value={form.cidade} onChange={handle('cidade')} />
          </label>
          <label className="block">
            <span className="text-sm">Estado</span>
            <input className="input" value={form.estado} onChange={handle('estado')} />
          </label>
          <label className="block">
            <span className="text-sm">CEP</span>
            <input className="input" value={form.cep} onChange={handle('cep')} />
          </label>
        </div>
      )}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <label className="block">
          <span className="text-sm">Previsão Fechamento</span>
          <input
            type="date"
            className="input"
            value={form.previsao_fechamento}
            onChange={handle('previsao_fechamento')}
          />
        </label>
        <label className="block">
          <span className="text-sm">Temperatura</span>
          <select
            className="input"
            value={form.temperatura}
            onChange={handle('temperatura')}
          >
            <option value="">Selecione</option>
            <option>Gelado</option>
            <option>Frio</option>
            <option>Morno</option>
            <option>Quente</option>
          </select>
        </label>
        <label className="block">
          <span className="text-sm">Tem Especificador?</span>
          <select
            className="input"
            value={form.tem_especificador ? 'Sim' : 'Não'}
            onChange={handle('tem_especificador')}
          >
            <option>Não</option>
            <option>Sim</option>
          </select>
        </label>
        {form.tem_especificador && (
          <>
            <label className="block">
              <span className="text-sm">Nome do Especificador</span>
              <input
                className="input"
                value={form.especificador_nome}
                onChange={handle('especificador_nome')}
              />
            </label>
            <label className="block">
              <span className="text-sm">% RT</span>
              <input
                type="number"
                step="0.01"
                className="input"
                value={form.rt_percent}
                onChange={handle('rt_percent')}
              />
            </label>
          </>
        )}
        <label className="block md:col-span-2">
          <span className="text-sm">Histórico</span>
          <textarea
            className="input"
            rows="4"
            value={form.historico}
            onChange={handle('historico')}
          />
          <input
            type="file"
            multiple
            className="mt-2"
            accept=".pdf,.txt,.png,.jpg,.jpeg,.xls,.xlsx"
            onChange={handleFileChange}
          />
        </label>
      </div>
      <div className="flex gap-2">
        <Button type="submit">Salvar</Button>
        <Button type="button" variant="outline" onClick={handleSair}>
          Sair
        </Button>
      </div>
    </form>
  );
}

export default AtendimentoForm;
