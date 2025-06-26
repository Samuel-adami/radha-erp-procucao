import React, { useState, useEffect } from "react";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Link,
  Navigate,
  useNavigate,
  Outlet,
  useMatch,
} from "react-router-dom";

import MarketingDigitalIA from "./modules/MarketingDigitalIA";
import Producao from "./modules/Producao";
import Cadastros from "./modules/Cadastros";
import Login from "./pages/Login";
import { fetchComAuth } from "./utils/fetchComAuth";
import { UserContext } from "./UserContext";

// Componente de Layout: A "moldura" do ERP para um usuário logado
function Layout({ usuario, onLogout }) {
  const possuiPermissao = (modulo) => usuario?.permissoes?.includes(modulo);

  const matchCadastros = useMatch("/cadastros/*");
  const matchMarketing = useMatch("/marketing-ia/*");
  const matchProducao = useMatch("/producao/*");

  return (
    <div className="min-h-screen flex">
      <aside className="bg-blue-900 text-white p-4 flex flex-col w-[20%] min-w-[200px]">
        <h1 className="text-2xl font-bold">Radha ERP</h1>
        <p className="text-sm mb-4">Usuário: {usuario?.nome}</p>
        <nav className="flex flex-col space-y-2 flex-grow">
          {possuiPermissao("cadastros") && (
            <Link
              to="/cadastros"
              className={`px-2 py-1 rounded ${matchCadastros ? "bg-blue-700" : "hover:bg-blue-700"}`}
            >
              Cadastros
            </Link>
          )}
          {possuiPermissao("marketing-ia") && (
            <Link
              to="/marketing-ia"
              className={`px-2 py-1 rounded ${matchMarketing ? "bg-blue-700" : "hover:bg-blue-700"}`}
            >
              Marketing Digital IA
            </Link>
          )}
          {possuiPermissao("producao") && (
            <Link
              to="/producao"
              className={`px-2 py-1 rounded ${matchProducao ? "bg-blue-700" : "hover:bg-blue-700"}`}
            >
              Produção
            </Link>
          )}
        </nav>
        <button
          onClick={onLogout}
          className="bg-red-500 hover:bg-red-600 text-white px-3 py-1 rounded mt-4"
        >
          Sair
        </button>
      </aside>
      <main className="flex-grow p-4 bg-gray-100">
        <UserContext.Provider value={usuario}>
          <Outlet />
        </UserContext.Provider>
      </main>
    </div>
  );
}

// Componente principal que gerencia o estado e as rotas
function App() {
  const [usuarioLogado, setUsuarioLogado] = useState(null);
  const [carregando, setCarregando] = useState(true);
  const navigate = useNavigate();

  const handleLoginSuccess = (usuario) => {
    setUsuarioLogado(usuario);
    navigate("/");
  };

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
        <Route
          element={
            usuarioLogado ? (
              <Layout usuario={usuarioLogado} onLogout={handleLogout} />
            ) : (
              <Navigate to="/login" replace />
            )
          }
        >
          <Route index element={<p className="text-center text-lg mt-10">Bem-vindo ao ERP Radha. Selecione um módulo no menu.</p>} />
          <Route path="cadastros/*" element={<Cadastros />} />
          <Route path="marketing-ia/*" element={<MarketingDigitalIA />} />
          <Route path="producao/*" element={<Producao />} />
        </Route>

        <Route path="/login" element={<Login onLoginSuccess={handleLoginSuccess} />} />

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