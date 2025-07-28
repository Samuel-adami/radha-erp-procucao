import React, { useState, useEffect } from 'react';
import { fetchComAuth } from '../../../utils/fetchComAuth';
import { Button } from '../../Producao/components/ui/button';

const Seccionadora = () => {
  const [pastaLote, setPastaLote] = useState('');
  const [lotes, setLotes] = useState([]);
  const [larguraChapa, setLarguraChapa] = useState(2750);
  const [alturaChapa, setAlturaChapa] = useState(1850);
  const [preview, setPreview] = useState([]);
  const [status, setStatus] = useState('');

  useEffect(() => {
    fetchComAuth('/listar-lotes')
      .then((d) => setLotes(d?.lotes || []))
      .catch(() => {});
  }, []);

  const handlePreview = async () => {
    setStatus('Gerando preview...');
    const res = await fetchComAuth('/seccionadora-preview', {
      method: 'POST',
      body: JSON.stringify({ pasta_lote: pastaLote, largura_chapa: larguraChapa, altura_chapa: alturaChapa }),
    });
    if (res.erro) {
      setStatus(res.erro);
    } else {
      setPreview(res.chapas || []);
      setStatus('Preview gerado.');
    }
  };

  const handleExecute = async () => {
    setStatus('Executando seccionadora...');
    const res = await fetchComAuth('/executar-seccionadora', {
      method: 'POST',
      body: JSON.stringify({ pasta_lote: pastaLote, largura_chapa: larguraChapa, altura_chapa: alturaChapa }),
    });
    if (res.erro) {
      setStatus(res.erro);
    } else {
      setStatus(`Seccionadora executada. Artefato: ${res.pasta_resultado}`);
    }
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Seccionadora (Guilhotina)</h1>
      <div className="mb-4">
        <label className="mr-2">Lote:</label>
        <select value={pastaLote} onChange={(e) => setPastaLote(e.target.value)}>
          <option value="">-- selecione --</option>
          {lotes.map((l) => (
            <option key={l} value={l}>{l}</option>
          ))}
        </select>
      </div>
      <div className="mb-4">
        <label className="mr-2">Largura da chapa:</label>
        <input type="number" value={larguraChapa} onChange={(e) => setLarguraChapa(e.target.value)} />
      </div>
      <div className="mb-4">
        <label className="mr-2">Altura da chapa:</label>
        <input type="number" value={alturaChapa} onChange={(e) => setAlturaChapa(e.target.value)} />
      </div>
      <div className="space-x-2 mb-4">
        <Button onClick={handlePreview}>Preview</Button>
        <Button onClick={handleExecute}>Executar Corte</Button>
      </div>
      {status && <p>{status}</p>}
      {preview.length > 0 && (
        <div className="mt-4 overflow-auto">
          <pre>{JSON.stringify(preview, null, 2)}</pre>
        </div>
      )}
    </div>
  );
};

export default Seccionadora;
