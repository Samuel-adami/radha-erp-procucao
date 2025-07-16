import React, { useEffect, useState } from 'react';
import { fetchComAuth } from '../../../utils/fetchComAuth';

function formatarData(dt) {
  if (!dt) return '';
  const d = new Date(dt);
  return d.toLocaleDateString();
}

function GestaoLeads() {
  const [leads, setLeads] = useState([]);
  const [inicio, setInicio] = useState('');
  const [fim, setFim] = useState('');
  const [estagio, setEstagio] = useState('');
  const [campanha, setCampanha] = useState('');
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState('');

  const carregar = async () => {
    setCarregando(true);
    setErro('');
    try {
      const params = new URLSearchParams();
      if (inicio) params.append('inicio', inicio);
      if (fim) params.append('fim', fim);
      if (campanha) params.append('campanha', campanha);
      if (estagio) params.append('estagio', estagio);
      const dados = await fetchComAuth(`/leads/?${params.toString()}`);
      setLeads(dados.leads || []);
    } catch (e) {
      setErro(e.message || String(e));
    } finally {
      setCarregando(false);
    }
  };

  useEffect(() => {
    carregar();
  }, []);

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">Gestão de Leads</h1>
      <div className="flex flex-wrap gap-2 mb-4">
        <input type="date" value={inicio} onChange={e => setInicio(e.target.value)} className="border rounded px-2 py-1" />
        <input type="date" value={fim} onChange={e => setFim(e.target.value)} className="border rounded px-2 py-1" />
        <input placeholder="Campanha" value={campanha} onChange={e => setCampanha(e.target.value)} className="border rounded px-2 py-1" />
        <input placeholder="Estágio" value={estagio} onChange={e => setEstagio(e.target.value)} className="border rounded px-2 py-1" />
        <button onClick={carregar} className="bg-blue-600 text-white px-3 py-1 rounded">Filtrar</button>
      </div>
      {erro && <div className="text-red-700 mb-2">{erro}</div>}
      <div className="overflow-x-auto">
        <table className="min-w-full bg-white border">
          <thead>
            <tr className="bg-gray-100">
              <th className="p-2 border">Nome</th>
              <th className="p-2 border">E-mail</th>
              <th className="p-2 border">Origem</th>
              <th className="p-2 border">Data</th>
              <th className="p-2 border">Estágio</th>
              <th className="p-2 border">Ações</th>
            </tr>
          </thead>
          <tbody>
            {leads.map(l => (
              <tr key={l.id} className="hover:bg-gray-50">
                <td className="p-2 border whitespace-nowrap">{l.nome}</td>
                <td className="p-2 border whitespace-nowrap">{l.email}</td>
                <td className="p-2 border whitespace-nowrap">{l.origem}</td>
                <td className="p-2 border whitespace-nowrap">{formatarData(l.data_conversao)}</td>
                <td className="p-2 border whitespace-nowrap">{l.estagio}</td>
                <td className="p-2 border">
                  {l.id && (
                    <a href={`https://app.rdstation.com.br/contacts/${l.id}`} target="_blank" rel="noopener noreferrer" className="text-blue-600 underline">
                      Abrir
                    </a>
                  )}
                </td>
              </tr>
            ))}
            {leads.length === 0 && !carregando && (
              <tr>
                <td colSpan="6" className="p-4 text-center text-gray-500">Nenhum lead encontrado.</td>
              </tr>
            )}
            {carregando && (
              <tr>
                <td colSpan="6" className="p-4 text-center">Carregando...</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default GestaoLeads;
