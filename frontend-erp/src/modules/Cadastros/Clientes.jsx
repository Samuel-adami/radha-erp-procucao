import React, { useState, useEffect } from 'react';
import { Button } from '../Producao/components/ui/button';
import { useNavigate, useParams } from 'react-router-dom';

function gerarCodigo(nome, seq) {
  if (!nome) return '';
  const prefix = nome.trim().substring(0, 3);
  if (!prefix) return '';
  const formatted = prefix[0].toUpperCase() + prefix.slice(1).toLowerCase();
  return `${formatted}${String(seq).padStart(4, '0')}`;
}

function formatTelefone(valor) {
  const dig = valor.replace(/\D/g, '').slice(0, 11);
  return dig.replace(/(\d{0,2})(\d{0,5})(\d{0,4}).*/, (_, a, b, c) =>
    (a ? `(${a}${a.length === 2 ? ') ' : ''}` : '') +
    b +
    (c ? `-${c}` : '')
  );
}

function formatCpfCnpj(valor) {
  const dig = valor.replace(/\D/g, '').slice(0, 14);
  if (dig.length <= 11) {
    return dig.replace(/(\d{0,3})(\d{0,3})(\d{0,3})(\d{0,2}).*/, (_, a, b, c, d) =>
      [a, b, c].filter(Boolean).join('.') + (d ? `-${d}` : '')
    );
  }
  return dig.replace(/(\d{0,2})(\d{0,3})(\d{0,3})(\d{0,4})(\d{0,2}).*/, (_, a, b, c, d, e) =>
    [a, b, c].filter(Boolean).join('.') + (d ? `/${d}` : '') + (e ? `-${e}` : '')
  );
}

function formatCEP(valor) {
  const dig = valor.replace(/\D/g, '').slice(0, 8);
  return dig.replace(/(\d{0,5})(\d{0,3}).*/, (_, a, b) => (a ? a : '') + (b ? `-${b}` : ''));
}

function Clientes() {
  const navigate = useNavigate();
  const { id } = useParams();
  const [sequencial, setSequencial] = useState(1);
  const initialForm = {
    procedencia: '',
    estadoImovel: '',
    previsaoFechamento: '',
    codigo: '',
    nome: '',
    documento: '',
    rgIe: '',
    sexo: '',
    dataNascimento: '',
    telefone1: '',
    telefone2: '',
    pais: 'Brasil',
    profissao: '',
    cep: '',
    cidade: '',
    estado: '',
    endereco: '',
    numero: '',
    complemento: '',
    bairro: '',
    email: '',
  };
  const [form, setForm] = useState(initialForm);
  const [dirty, setDirty] = useState(false);

  useEffect(() => {
    const seq = parseInt(localStorage.getItem('clienteCodigoSeq') || '1', 10);
    setSequencial(seq);
  }, []);

  useEffect(() => {
    if (id) {
      const lista = JSON.parse(localStorage.getItem('clientes') || '[]');
      const existente = lista.find(c => String(c.id) === String(id));
      if (existente) {
        setForm(existente);
      }
    }
  }, [id]);

  useEffect(() => {
    if (!id) {
      setForm(f => ({ ...f, codigo: gerarCodigo(f.nome, sequencial) }));
    }
  }, [form.nome, sequencial, id]);

  const handle = campo => e => {
    let value = e.target.value;
    if (campo === 'telefone1' || campo === 'telefone2') {
      value = formatTelefone(value);
    } else if (campo === 'documento') {
      value = formatCpfCnpj(value);
    } else if (campo === 'cep') {
      value = formatCEP(value);
    }
    setForm(prev => ({ ...prev, [campo]: value }));
    setDirty(true);
  };

  const buscarCEP = async () => {
    const cep = form.cep.replace(/\D/g, '');
    if (cep.length !== 8) return;
    try {
      const resp = await fetch(`https://viacep.com.br/ws/${cep}/json/`);
      const dados = await resp.json();
      if (!dados.erro) {
        setForm(prev => ({
          ...prev,
          endereco: dados.logradouro || '',
          bairro: dados.bairro || '',
          cidade: dados.localidade || '',
          estado: dados.uf || '',
        }));
      }
    } catch (err) {
      console.error('Erro ao buscar CEP', err);
    }
  };

  const salvar = () => {
    const lista = JSON.parse(localStorage.getItem('clientes') || '[]');
    if (id) {
      const idx = lista.findIndex(c => String(c.id) === String(id));
      if (idx >= 0) lista[idx] = { ...form, id };
    } else {
      const novo = { ...form, id: Date.now() };
      lista.push(novo);
      localStorage.setItem('clienteCodigoSeq', String(sequencial + 1));
      setSequencial(s => s + 1);
    }
    localStorage.setItem('clientes', JSON.stringify(lista));
    alert('Cliente salvo');
    if (!id) setForm(initialForm);
    setDirty(false);
  };

  const estados = [
    'AC','AL','AP','AM','BA','CE','DF','ES','GO','MA','MT','MS','MG','PA','PB','PR','PE','PI','RJ','RN','RS','RO','RR','SC','SP','SE','TO'
  ];

  const handleSubmit = e => {
    e.preventDefault();
    salvar();
  };

  const cancelar = () => {
    setForm(initialForm);
    setDirty(false);
  };

  const sair = () => {
    if (dirty) {
      if (window.confirm('Deseja salvar as informações adicionadas?')) {
        salvar();
      }
    }
    navigate('..');
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <label className="block">
          <span className="text-sm">Procedência</span>
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
          <span className="text-sm">Estado do Imóvel</span>
          <select className="input" value={form.estadoImovel} onChange={handle('estadoImovel')}>
            <option value="">Selecione</option>
            <option>Pronto</option>
            <option>ínicio de obra</option>
            <option>em reforma</option>
            <option>final de obra</option>
          </select>
        </label>
        <label className="block">
          <span className="text-sm">Previsão de Fechamento</span>
          <input type="date" className="input" value={form.previsaoFechamento} onChange={handle('previsaoFechamento')} />
        </label>
        <label className="block">
          <span className="text-sm">Código</span>
          <input className="input bg-gray-100" value={form.codigo} readOnly />
        </label>
        <label className="block">
          <span className="text-sm">Nome/Empresa</span>
          <input className="input" value={form.nome} onChange={handle('nome')} />
        </label>
        <label className="block">
          <span className="text-sm">CPF/CNPJ</span>
          <input className="input" value={form.documento} onChange={handle('documento')} placeholder="000.000.000-00" />
        </label>
        <label className="block">
          <span className="text-sm">R.G/Insc. Est</span>
          <input className="input" value={form.rgIe} onChange={handle('rgIe')} />
        </label>
        <label className="block">
          <span className="text-sm">Sexo</span>
          <select className="input" value={form.sexo} onChange={handle('sexo')}>
            <option value="">Selecione</option>
            <option>Masculino</option>
            <option>Feminino</option>
            <option>Outro</option>
          </select>
        </label>
        <label className="block">
          <span className="text-sm">Data nascimento</span>
          <input type="date" className="input" value={form.dataNascimento} onChange={handle('dataNascimento')} />
        </label>
        <label className="block">
          <span className="text-sm">Telefone 1</span>
          <input className="input" value={form.telefone1} onChange={handle('telefone1')} placeholder="(99) 99999-9999" />
        </label>
        <label className="block">
          <span className="text-sm">Telefone 2</span>
          <input className="input" value={form.telefone2} onChange={handle('telefone2')} placeholder="(99) 99999-9999" />
        </label>
        <label className="block">
          <span className="text-sm">País</span>
          <select className="input" value={form.pais} onChange={handle('pais')}>
            <option>Brasil</option>
          </select>
        </label>
        <label className="block">
          <span className="text-sm">Profissão</span>
          <input className="input" list="listaProf" value={form.profissao} onChange={handle('profissao')} />
          <datalist id="listaProf">
            <option>Administrador</option>
            <option>Arquiteto</option>
            <option>Engenheiro</option>
            <option>Designer</option>
            <option>Outros</option>
          </datalist>
        </label>
        <label className="block">
          <span className="text-sm">CEP</span>
          <input className="input" value={form.cep} onChange={handle('cep')} onBlur={buscarCEP} placeholder="99999-999" />
        </label>
        <label className="block">
          <span className="text-sm">Cidade</span>
          <input className="input" value={form.cidade} onChange={handle('cidade')} />
        </label>
        <label className="block">
          <span className="text-sm">Estado</span>
          <select className="input" value={form.estado} onChange={handle('estado')}>
            <option value="">Selecione</option>
            {estados.map(uf => <option key={uf}>{uf}</option>)}
          </select>
        </label>
        <label className="block md:col-span-2">
          <span className="text-sm">Endereço</span>
          <input className="input" value={form.endereco} onChange={handle('endereco')} />
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
          <span className="text-sm">Email</span>
          <input type="email" className="input" value={form.email} onChange={handle('email')} />
        </label>
      </div>
      <div className="flex gap-2">
        <Button type="button" onClick={handleSubmit}>Salvar</Button>
        <Button type="button" variant="secondary" onClick={cancelar}>
          Cancelar
        </Button>
        <Button type="button" variant="secondary" onClick={sair}>
          Sair
        </Button>
      </div>
    </form>
  );
}

export default Clientes;
