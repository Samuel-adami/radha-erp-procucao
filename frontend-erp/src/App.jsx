import React, { useState, useEffect } from "react";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Link,
  Navigate,
  useNavigate,
  Outlet,
} from "react-router-dom";

import MarketingDigitalIA from "./modules/MarketingDigitalIA";
import Producao from "./modules/Producao";
import { fetchComAuth } from "./utils/fetchComAuth";

// Componente de Layout: A "moldura" do ERP para um usuário logado
function Layout({ usuario, onLogout }) {
  const possuiPermissao = (modulo) => {
    return usuario?.permissoes?.includes(modulo);
  };

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col">
    
      <header className="bg-purple-900 text-white p-4 shadow-md flex justify-between items-center">
        <h1 className="text-2xl font-bold">Radha ERP</h1>
        <nav className="flex space-x-4">
          {possuiPermissao("marketing-ia") && (
            <Link to="/marketing-ia" className="hover:underline">Marketing Digital IA</Link>
          )}
          {possuiPermissao("producao") && (
            <Link to="/producao" className="hover:underline">Produção</Link>
          )}
        </nav>
        <button onClick={onLogout} className="bg-red-500 hover:bg-red-600 text-white px-3 py-1 rounded">Sair</button>
      </header>
      <main className="flex-grow p-4">
        {/* As páginas dos módulos (filhas da rota) serão renderizadas aqui */}
        <Outlet />
      </main>
    </div>
  );
}

// Componente principal que gerencia o estado e as rotas
function App() {
  const [usuarioLogado, setUsuarioLogado] = useState(null);
  const [carregando, setCarregando] = useState(true);
  const navigate = useNavigate();

  // Efeito para autenticação automática na inicialização da aplicação
  useEffect(() => {
    const autenticar = async () => {
      const token = localStorage.getItem("token");
      if (token) {
        try {
          const dados = await fetchComAuth("/auth/validate");
          setUsuarioLogado(dados.usuario);
          setCarregando(false);
          return;
        } catch (error) {
          console.error("Token inválido ou expirado, tentando novo login.", error);
          localStorage.removeItem("token");
        }
      }

        const defaultUser = import.meta.env.VITE_DEFAULT_USERNAME;
        const defaultPass = import.meta.env.VITE_DEFAULT_PASSWORD;

        if (defaultUser && defaultPass) {
          try {
            const login = await fetchComAuth("/auth/login", {
              method: "POST",
              body: JSON.stringify({ username: defaultUser, password: defaultPass }),
            });
            localStorage.setItem("token", login.access_token);
            setUsuarioLogado(login.usuario);
          } catch (error) {
            console.error("Falha no login automático:", error);
          } finally {
            setCarregando(false);
          }
        } else {
          setCarregando(false);
        }
    };

    autenticar();
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("token");
    setUsuarioLogado(null);
    navigate("/");
  };
  

  // Enquanto a validação inicial do token está acontecendo, exibe uma mensagem
  if (carregando) {
    return <div className="p-6 text-center text-xl">Carregando...</div>;
  }
  
  return (
      <Routes>
        {/* Rotas principais do ERP */}
        <Route
          element={
            usuarioLogado ? (
              <Layout usuario={usuarioLogado} onLogout={handleLogout} />
            ) : (
              <p className="p-4">Falha na autenticação.</p>
            )
          }
        >
          {/* Rotas filhas do Layout. Elas serão renderizadas no <Outlet /> */}
          <Route index element={<p className="text-center text-lg mt-10">Bem-vindo ao ERP Radha. Selecione um módulo no menu.</p>} />
          <Route path="marketing-ia/*" element={<MarketingDigitalIA />} />
          <Route path="producao/*" element={<Producao />} />
        </Route>

        {/* Rota para qualquer outro caminho não encontrado */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
  );
}

// Componente que envolve toda a aplicação com o Router
function MainApp() {
  return (
    <Router>
      <App />
    </Router>
  );
}

export default MainApp;