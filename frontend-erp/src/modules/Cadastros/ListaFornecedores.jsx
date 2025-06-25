import React from 'react';

const ListaFornecedores = () => {
  const fornecedores = [
    { id: 1, nome: 'Fornecedor Exemplo 1' },
    { id: 2, nome: 'Fornecedor Exemplo 2' },
  ];

  return (
    <div className="space-y-2">
      <h3 className="text-lg font-semibold">Fornecedores Cadastrados</h3>
      <ul className="space-y-1">
        {fornecedores.map((f) => (
          <li key={f.id} className="border rounded p-2">
            {f.nome}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default ListaFornecedores;
