import React from 'react';
import { Operacao } from './ChapaViewer';
import { Button } from '../ui/button';

interface Props {
  operacao: Operacao | null;
  onClose: () => void;
}

const OperacaoDetailModal: React.FC<Props> = ({ operacao, onClose }) => {
  if (!operacao) return null;
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white p-4 space-y-2 rounded shadow max-w-sm w-full">
        <h3 className="font-semibold text-lg">{operacao.nome}</h3>
        {operacao.cliente && (
          <p className="text-sm">Cliente: {operacao.cliente}</p>
        )}
        {operacao.ambiente && (
          <p className="text-sm">Ambiente: {operacao.ambiente}</p>
        )}
        <pre className="text-xs whitespace-pre-wrap">
{JSON.stringify(operacao, null, 2)}
        </pre>
        <Button className="w-full" onClick={onClose}>Fechar</Button>
      </div>
    </div>
  );
};

export default OperacaoDetailModal;
