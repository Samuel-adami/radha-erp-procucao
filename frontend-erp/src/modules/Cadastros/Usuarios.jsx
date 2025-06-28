import React, { useState, useEffect } from 'react';
import { Button } from '../Producao/components/ui/button';
import { useNavigate, useParams } from 'react-router-dom';
import { fetchComAuth } from '../../utils/fetchComAuth';

const PERMISSOES_DISPONIVEIS = {
  'Marketing Digital IA': [
    'marketing-ia',
    'marketing-ia/chat',
    'marketing-ia/nova-campanha',
    'marketing-ia/nova-publicacao',
    'marketing-ia/publicos-alvo'
  ],
  'Produção': [
    'producao',
    'producao/lote',
    'producao/apontamento',
    'producao/apontamento-volume',
    'producao/nesting',
    'producao/chapas',
    'producao/ocorrencias',
    'producao/relatorios/ocorrencias'
  ],
  'Cadastros': [
    'cadastros',
    'cadastros/dados-empresa',
    'cadastros/clientes',
    'cadastros/fornecedores',
    'cadastros/usuarios',
    'cadastros/condicoes-pagamento'
  ],
  'Comercial': [
    'comercial',
    'comercial/atendimentos'
  ]
};

function Usuarios() {
  const navigate = useNavigate();
  const { id } = useParams();
  const initialForm = { username: '', password: '', email: '', nome: '', cargo: '', permissoes: [] };
  const [form, setForm] = useState(initialForm);
  const [dirty, setDirty] = useState(false);

  useEffect(() => {
    if (id) {
      fetchComAuth('/usuarios')
        .then(d => {
          const u = (d?.usuarios || []).find(x => String(x.id) === String(id));
          if (u) setForm(u);
        })
        .catch(() => {});
    }
  }, [id]);
  const handle = campo => e => {
    setForm(prev => ({ ...prev, [campo]: e.target.value }));
    setDirty(true);
  };
  const togglePermissao = (perm, checked) => {
    setForm(prev => ({
      ...prev,
      permissoes: checked
        ? [...prev.permissoes, perm]
        : prev.permissoes.filter(p => p !== perm)
    }));
    setDirty(true);
  };
  const toggleGrupo = (grupo, checked) => {
    const permissoes = PERMISSOES_DISPONIVEIS[grupo];
    setForm(prev => ({
      ...prev,
      permissoes: checked
        ? Array.from(new Set([...prev.permissoes, ...permissoes]))
        : prev.permissoes.filter(p => !permissoes.includes(p))
    }));
    setDirty(true);
  };

  const salvar = async () => {
    const url = id ? `/usuarios/${id}` : '/usuarios';
    const metodo = id ? 'PUT' : 'POST';
    await fetchComAuth(url, { method: metodo, body: JSON.stringify(form) });
    if (id) {
      navigate('../lista');
    } else {
      setForm(initialForm);
    }
    alert('Usuário salvo');
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
        <label className="block"><span className="text-sm">Usuário</span><input className="input" value={form.username} onChange={handle('username')} /></label>
        <label className="block"><span className="text-sm">Senha</span><input type="text" className="input" value={form.password} onChange={handle('password')} /></label>
        <label className="block"><span className="text-sm">Email</span><input className="input" value={form.email} onChange={handle('email')} /></label>
        <label className="block"><span className="text-sm">Nome</span><input className="input" value={form.nome} onChange={handle('nome')} /></label>
        <label className="block"><span className="text-sm">Cargo</span><input className="input" value={form.cargo} onChange={handle('cargo')} /></label>
        <label className="block md:col-span-2">
          <span className="text-sm">Permissões</span>
          <div className="border rounded p-2 max-h-40 overflow-y-auto space-y-2">
            {Object.entries(PERMISSOES_DISPONIVEIS).map(([grupo, permissoes]) => {
              const [pai, ...filhos] = permissoes;
              const todosMarcados = permissoes.every(p => form.permissoes.includes(p));
              return (
                <fieldset key={grupo} className="border-b last:border-b-0 pb-1">
                  <label className="inline-flex items-center gap-1 font-medium">
                    <input
                      type="checkbox"
                      checked={todosMarcados}
                      onChange={e => toggleGrupo(grupo, e.target.checked)}
                    />
                    {grupo}
                  </label>
                  <div className="flex flex-col pl-4">
                    {filhos.map(p => (
                      <label key={p} className="inline-flex items-center gap-1">
                        <input
                          type="checkbox"
                          value={p}
                          checked={form.permissoes.includes(p)}
                          onChange={e => togglePermissao(p, e.target.checked)}
                        />
                        <span>{p}</span>
                      </label>
                    ))}
                  </div>
                </fieldset>
              );
            })}
          </div>
        </label>
      </div>
      <div className="flex gap-2">
        <Button type="submit">Salvar</Button>
        <Button type="button" variant="secondary" onClick={cancelar}>
          Cancelar
        </Button>
        <Button type="button" variant="secondary" onClick={sair}>Sair</Button>
      </div>
    </form>
  );
}

export default Usuarios;
