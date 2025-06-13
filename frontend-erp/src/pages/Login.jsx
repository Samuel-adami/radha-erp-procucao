import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
// Não é necessário importar fetchComAuth aqui, pois o fetch direto é usado.
// Mas se quiser usar fetchComAuth, a linha seria: import { fetchComAuth } from '../utils/fetchComAuth';

function Login({ setUsuarioLogado }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [erro, setErro] = useState('');
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setErro('');

    try {
      // Requisição corrigida para o Backend Gateway na porta 8010
      const response = await fetch('http://localhost:8010/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username, password })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Usuário ou senha inválidos');
      }

      const data = await response.json();
      localStorage.setItem("token", data.access_token);
      // O backend-gateway deve retornar um objeto 'usuario' com permissões
      setUsuarioLogado(data.usuario); 
      navigate("/"); // Redireciona para a home do ERP após login
    } catch (err) {
      console.error("Erro no login:", err); // Adicionado console.error para mais detalhes no console do navegador
      setErro(err.message);
    }
  };

  return (
    <div className="min-h-screen flex flex-col justify-center items-center bg-gray-100 p-6">
      <form
        onSubmit={handleLogin}
        className="bg-white shadow-md rounded px-8 py-6 w-full max-w-md"
      >
        <h2 className="text-2xl font-bold mb-6 text-center">Login ERP Radha</h2>

        {erro && <p className="text-red-500 mb-4 text-center">{erro}</p>}

        <div className="mb-4">
          <label className="block text-gray-700">Usuário:</label>
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="w-full border rounded px-3 py-2 mt-1"
            placeholder="Digite seu usuário"
            required
          />
        </div>

        <div className="mb-6">
          <label className="block text-gray-700">Senha:</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full border rounded px-3 py-2 mt-1"
            placeholder="Digite sua senha"
            required
          />
        </div>

        <button
          type="submit"
          className="w-full bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700"
        >
          Entrar
        </button>
      </form>
    </div>
  );
}

export default Login;