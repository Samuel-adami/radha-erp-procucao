import React, { useState } from 'react';
import { Button } from '../Producao/components/ui/button';
import { Link } from 'react-router-dom';

function CadastroMenu({ basePath, ListaComponente }) {
  const [mostrarLista, setMostrarLista] = useState(false);

  return (
    <div className="space-y-2">
      <Button asChild>
        <Link to={`${basePath}/novo`}>Novo Cadastro</Link>
      </Button>
      <Button
        type="button"
        variant="secondary"
        onClick={() => setMostrarLista(!mostrarLista)}
      >
        Listar Cadastros
      </Button>
      {mostrarLista && ListaComponente && <ListaComponente />}
    </div>
  );
}

export default CadastroMenu;
