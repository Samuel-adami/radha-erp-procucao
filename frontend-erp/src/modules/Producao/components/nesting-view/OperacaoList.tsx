import React from 'react';
import { Operacao } from './ChapaViewer';
import { Button } from '../ui/button';

interface Props {
  operacoes: Operacao[];
  onSelect: (o: Operacao) => void;
  destaqueId?: number | null;
}

const OperacaoList: React.FC<Props> = ({ operacoes, onSelect, destaqueId }) => {
  return (
    <div className="space-y-2 max-h-80 overflow-auto">
      {operacoes.map((op) => (
        <div
          key={op.id}
          className={`p-2 border rounded flex justify-between items-center ${destaqueId === op.id ? 'bg-blue-100' : ''}`}
        >
          <div className="text-sm">
            <p className="font-semibold">{op.nome}</p>
            <p className="text-xs text-muted-foreground">
              {op.tipo}
              {op.layer ? ` - ${op.layer}` : ''}
            </p>
          </div>
          <Button variant="outline" size="sm" onClick={() => onSelect(op)}>
            Destacar
          </Button>
        </div>
      ))}
    </div>
  );
};

export default OperacaoList;
