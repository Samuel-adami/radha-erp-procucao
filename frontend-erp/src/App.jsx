import React, { useState, useEffect } from "react";
import {
  HashRouter as Router,
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
import PlanosProducao from "./modules/PlanosProducao";
import Cadastros from "./modules/Cadastros";
import Comercial from "./modules/Comercial";
import Finance from "./modules/Finance";
import Formularios from "./modules/Formularios";
import Login from "./pages/Login";
import { fetchComAuth } from "./utils/fetchComAuth";
import { UserContext } from "./UserContext";

// Componente de Layout: A "moldura" do ERP para um usuário logado
function Layout({ usuario, onLogout }) {
  const possuiPermissao = (modulo) => usuario?.permissoes?.includes(modulo);

  const matchCadastros = useMatch("/cadastros/*");
  const matchMarketing = useMatch("/marketing-ia/*");
  const matchProducao = useMatch("/producao/*");
  const matchComercial = useMatch("/comercial/*");
  const matchFinance = useMatch("/finance/*");
  const matchFormularios = useMatch("/formularios/*");
  const matchPlanosProducao = useMatch("/planos-producao/*");

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
          {possuiPermissao("planos-producao") && (
            <Link
              to="/planos-producao"
              className={`px-2 py-1 rounded ${matchPlanosProducao ? "bg-blue-700" : "hover:bg-blue-700"}`}
            >
              Planos de Produção
            </Link>
          )}
          {possuiPermissao("comercial") && (
            <Link
              to="/comercial"
              className={`px-2 py-1 rounded ${matchComercial ? "bg-blue-700" : "hover:bg-blue-700"}`}
            >
              Comercial
            </Link>
          )}
          {possuiPermissao("finance") && (
            <Link
              to="/finance"
              className={`px-2 py-1 rounded ${matchFinance ? "bg-blue-700" : "hover:bg-blue-700"}`}
            >
              Financeiro
            </Link>
          )}
          {possuiPermissao("formularios") && (
            <Link
              to="/formularios"
              className={`px-2 py-1 rounded ${matchFormularios ? "bg-blue-700" : "hover:bg-blue-700"}`}
            >
              Formulários
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
  const [usuarioLogado, setUsuarioLogado] = useState(() => {
    const stored = localStorage.getItem("usuario");
    return stored ? JSON.parse(stored) : null;
  });
  const [carregando, setCarregando] = useState(true);
  const [logs, setLogs] = useState([]);
  const navigate = useNavigate();

  const handleLoginSuccess = (usuario) => {
    localStorage.setItem("usuario", JSON.stringify(usuario));
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
          localStorage.setItem("usuario", JSON.stringify(dados.usuario));
          setUsuarioLogado(dados.usuario);
          setCarregando(false);
          return;
        } catch (error) {
          console.error("Token inválido ou expirado, tentando novo login.", error);
          // Só remove o token se a falha indicar realmente problema de autorização
          if (error.message.startsWith("Erro 401") || error.message.startsWith("Erro 403")) {
            localStorage.removeItem("token");
            localStorage.removeItem("usuario");
          }
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
            localStorage.setItem("usuario", JSON.stringify(login.usuario));
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
    localStorage.removeItem("usuario");
    setUsuarioLogado(null);
    navigate("/");
  };

  useEffect(() => {
    const handler = (e) => {
      const msg = e.detail;
      setLogs((prev) => [...prev, msg]);
      setTimeout(() => {
        setLogs((prev) => prev.filter((m) => m !== msg));
      }, 5000);
    };
    window.addEventListener('log', handler);
    return () => window.removeEventListener('log', handler);
  }, []);
  

  // Enquanto a validação inicial do token está acontecendo, exibe uma mensagem
  if (carregando) {
    return <div className="p-6 text-center text-xl">Carregando...</div>;
  }
  
  return (
    <>
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
          <Route path="planos-producao/*" element={<PlanosProducao />} />
          <Route path="comercial/*" element={<Comercial />} />
          <Route path="finance/*" element={<Finance />} />
          <Route path="formularios/*" element={<Formularios />} />
        </Route>

        <Route path="/login" element={<Login onLoginSuccess={handleLoginSuccess} />} />

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      {logs.length > 0 && (
        <div className="fixed bottom-2 right-2 space-y-1 z-50">
          {logs.map((msg, i) => (
            <div
              key={i}
              className="bg-red-200 border border-red-400 text-red-800 px-2 py-1 rounded shadow"
            >
              {msg}
            </div>
          ))}
        </div>
      )}
    </>
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
