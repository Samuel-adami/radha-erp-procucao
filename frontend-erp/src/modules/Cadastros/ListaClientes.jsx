import React from 'react';

const ListaClientes = () => {
  // Placeholder list; replace with fetch when API available
  const clientes = [
    { id: 1, nome: 'Cliente Exemplo 1' },
    { id: 2, nome: 'Cliente Exemplo 2' },
  ];

  return (
    <div className="space-y-2">
      <h3 className="text-lg font-semibold">Clientes Cadastrados</h3>
      <ul className="space-y-1">
        {clientes.map((c) => (
          <li key={c.id} className="border rounded p-2">
            {c.nome}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default ListaClientes;
