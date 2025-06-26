import React, { useState } from 'react';
import { Button } from '../Producao/components/ui/button';
import { useNavigate } from 'react-router-dom';
import { fetchComAuth } from '../../utils/fetchComAuth';

function Usuarios() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ username: '', password: '', email: '', nome: '', cargo: '', permissoes: '' });
  const handle = campo => e => setForm(prev => ({ ...prev, [campo]: e.target.value }));

  const salvar = async e => {
    e.preventDefault();
    await fetchComAuth('/usuarios', { method: 'POST', body: JSON.stringify({
      ...form,
      permissoes: form.permissoes.split(',').map(p => p.trim()).filter(Boolean)
    }) });
    setForm({ username: '', password: '', email: '', nome: '', cargo: '', permissoes: '' });
    alert('Usuário salvo');
  };

  return (
    <form onSubmit={salvar} className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <label className="block"><span className="text-sm">Usuário</span><input className="input" value={form.username} onChange={handle('username')} /></label>
        <label className="block"><span className="text-sm">Senha</span><input type="password" className="input" value={form.password} onChange={handle('password')} /></label>
        <label className="block"><span className="text-sm">Email</span><input className="input" value={form.email} onChange={handle('email')} /></label>
        <label className="block"><span className="text-sm">Nome</span><input className="input" value={form.nome} onChange={handle('nome')} /></label>
        <label className="block"><span className="text-sm">Cargo</span><input className="input" value={form.cargo} onChange={handle('cargo')} /></label>
        <label className="block md:col-span-2"><span className="text-sm">Permissões (separadas por vírgula)</span><input className="input" value={form.permissoes} onChange={handle('permissoes')} /></label>
      </div>
      <div className="flex gap-2">
        <Button type="submit">Salvar</Button>
        <Button type="button" variant="secondary" onClick={() => navigate('lista')}>Listar Usuários</Button>
      </div>
    </form>
  );
}

export default Usuarios;
