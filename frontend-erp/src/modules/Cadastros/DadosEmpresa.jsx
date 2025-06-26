import React, { useState, useEffect } from 'react';
import { Button } from '../Producao/components/ui/button';
import { fetchComAuth } from '../../utils/fetchComAuth';
import { useNavigate } from 'react-router-dom';

function DadosEmpresa() {
  const navigate = useNavigate();
  const initialForm = {
    razaoSocial: '',
    nomeFantasia: '',
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
  const [dirty, setDirty] = useState(false);

  useEffect(() => {
    const existente = JSON.parse(localStorage.getItem('empresa') || 'null');
    if (existente) setForm({ ...initialForm, ...existente });
  }, []);

  const handle = campo => e => {
    const value = campo === 'logo' ? e.target.files[0] : e.target.value;
    setForm(prev => ({ ...prev, [campo]: value }));
    setDirty(true);
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

  const salvar = async () => {
    const data = new FormData();
    Object.entries(form).forEach(([k, v]) => {
      if (v) data.append(k, v);
    });
    try {
      await fetchComAuth('/empresa', { method: 'PUT', body: data });
    } catch (err) {
      console.warn('Falha ao salvar remotamente, usando localStorage', err);
    }

    localStorage.setItem('empresa', JSON.stringify(form));
    alert('Dados salvos');
    setDirty(false);
  };

  const handleSubmit = e => {
    e.preventDefault();
    salvar();
  };

  const cancelar = () => {
    setForm(initialForm);
    setDirty(false);
  };

  const sair = async () => {
    if (dirty) {
      if (window.confirm('Deseja salvar as informações adicionadas?')) {
        await salvar();
      }
    }
    navigate('..');
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
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

export default DadosEmpresa;
