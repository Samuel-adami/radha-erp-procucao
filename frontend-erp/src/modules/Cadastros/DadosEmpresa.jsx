import React, { useState, useEffect } from 'react';
import { Button } from '../Producao/components/ui/button';
import { fetchComAuth } from '../../utils/fetchComAuth';
import { useParams, useNavigate } from 'react-router-dom';

function gerarCodigo(nomeFantasia, sequencial) {
  if (!nomeFantasia) return '';
  const prefixo = nomeFantasia.trim().substring(0,3);
  if (!prefixo) return '';
  const formatado = prefixo[0].toUpperCase() + prefixo.slice(1).toLowerCase();
  return `${formatado}${String(sequencial).padStart(3,'0')}`;
}

function DadosEmpresa() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [sequencial, setSequencial] = useState(1);
  const initialForm = {
    razaoSocial: '',
    nomeFantasia: '',
    codigo: '',
    cnpj: '',
    inscricaoEstadual: '',
    cep: '',
    rua: '',
    numero: '',
    bairro: '',
    cidade: '',
    estado: '',
    telefone1: '',
    telefone2: '',
    logo: null,
  };
  const [form, setForm] = useState(initialForm);

  useEffect(() => {
    const seq = parseInt(localStorage.getItem('empresaCodigoSeq') || '1', 10);
    setSequencial(seq);
  }, []);

  useEffect(() => {
    if (id) {
      fetchComAuth(`/empresa/${id}`).then(dados => {
        if (dados && dados.empresa) {
          const e = dados.empresa;
          setForm({
            razaoSocial: e.razao_social || '',
            nomeFantasia: e.nome_fantasia || '',
            codigo: e.codigo || '',
            cnpj: e.cnpj || '',
            inscricaoEstadual: e.inscricao_estadual || '',
            cep: e.cep || '',
            rua: e.rua || '',
            numero: e.numero || '',
            bairro: e.bairro || '',
            cidade: e.cidade || '',
            estado: e.estado || '',
            telefone1: e.telefone1 || '',
            telefone2: e.telefone2 || '',
            logo: null,
          });
        }
      });
    }
  }, [id]);

  useEffect(() => {
    setForm(f => ({ ...f, codigo: gerarCodigo(f.nomeFantasia, sequencial) }));
  }, [form.nomeFantasia, sequencial]);

  const handle = campo => e => {
    const value = campo === 'logo' ? e.target.files[0] : e.target.value;
    setForm(prev => ({ ...prev, [campo]: value }));
  };

  const buscarCEP = async () => {
    const cep = form.cep.replace(/\D/g,'');
    if (cep.length !== 8) return;
    try {
      const resp = await fetch(`https://viacep.com.br/ws/${cep}/json/`);
      const dados = await resp.json();
      if (!dados.erro) {
        setForm(prev => ({
          ...prev,
          rua: dados.logradouro || '',
          bairro: dados.bairro || '',
          cidade: dados.localidade || '',
          estado: dados.uf || '',
        }));
      }
    } catch(err) {
      console.error('Erro ao buscar CEP', err);
    }
  };

  const salvar = async (e) => {
    e.preventDefault();
    // Exemplo de envio ao backend - ajusta conforme API
    const data = new FormData();
    Object.entries(form).forEach(([k,v]) => {
      if (v) data.append(k, v);
    });
    try {
      const url = id ? `/empresa/${id}` : '/empresa';
      const method = id ? 'PUT' : 'POST';
      await fetchComAuth(url, { method, body: data });
    } catch(err) {
      console.warn('Falha ao salvar remotamente, usando localStorage', err);
    }

    const lista = JSON.parse(localStorage.getItem('empresas') || '[]');
    if (id) {
      const idx = lista.findIndex(e => String(e.id) === String(id));
      if (idx >= 0) lista[idx] = { ...form, id };
    } else {
      const novo = { ...form, id: Date.now() };
      lista.push(novo);
      localStorage.setItem('empresaCodigoSeq', String(sequencial + 1));
      setSequencial(s => s + 1);
    }
    localStorage.setItem('empresas', JSON.stringify(lista));
    if (!id) setForm(f => ({ ...f, ...initialForm }));
    alert('Dados salvos');
  };

  return (
    <form onSubmit={salvar} className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <label className="block">
          <span className="text-sm">Razão Social</span>
          <input className="input" value={form.razaoSocial} onChange={handle('razaoSocial')} />
        </label>
        <label className="block">
          <span className="text-sm">Nome Fantasia</span>
          <input className="input" value={form.nomeFantasia} onChange={handle('nomeFantasia')} />
        </label>
        <label className="block">
          <span className="text-sm">Código</span>
          <input className="input bg-gray-100" value={form.codigo} readOnly />
        </label>
        <label className="block">
          <span className="text-sm">CNPJ</span>
          <input className="input" value={form.cnpj} onChange={handle('cnpj')} pattern="\d{14}" />
        </label>
        <label className="block">
          <span className="text-sm">Inscrição Estadual</span>
          <input className="input" value={form.inscricaoEstadual} onChange={handle('inscricaoEstadual')} />
        </label>
        <label className="block">
          <span className="text-sm">CEP</span>
          <input className="input" value={form.cep} onChange={handle('cep')} onBlur={buscarCEP} />
        </label>
        <label className="block">
          <span className="text-sm">Rua</span>
          <input className="input" value={form.rua} onChange={handle('rua')} />
        </label>
        <label className="block">
          <span className="text-sm">Número</span>
          <input className="input" value={form.numero} onChange={handle('numero')} />
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
          <span className="text-sm">Telefone 1</span>
          <input className="input" value={form.telefone1} onChange={handle('telefone1')} placeholder="(11) 99999-9999" />
        </label>
        <label className="block">
          <span className="text-sm">Telefone 2</span>
          <input className="input" value={form.telefone2} onChange={handle('telefone2')} placeholder="(11) 99999-9999" />
        </label>
        <label className="block">
          <span className="text-sm">Logotipo</span>
          <input type="file" accept="image/jpeg,image/png,image/svg+xml" onChange={handle('logo')} />
        </label>
      </div>
      <div className="flex gap-2">
        <Button type="submit">Salvar</Button>
        <Button type="button" variant="secondary" onClick={() => navigate('lista')}>
          Listar Empresas
        </Button>
      </div>
    </form>
  );
}

export default DadosEmpresa;
