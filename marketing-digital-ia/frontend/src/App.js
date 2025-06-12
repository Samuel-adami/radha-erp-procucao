import React, { useState, useEffect } from "react";
import { BrowserRouter as Router, Routes, Route, Link, Navigate, useNavigate } from "react-router-dom";
import Chat from "./pages/Chat";
import NovaCampanha from "./pages/NovaCampanha";
import NovaPublicacao from "./pages/NovaPublicacao";
import PublicosAlvo from "./pages/PublicosAlvo";
import Login from "./pages/Login";

function AppWrapper() {
  return (
    <Router>
      <App />
    </Router>
  );
}

function App() {
  const [usuarioLogado, setUsuarioLogado] = useState(null);
  const [carregando, setCarregando] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    localStorage.clear();
    setUsuarioLogado(null);
    setCarregando(false);
  }, []);

  const possuiPermissao = (rota) => {
    return usuarioLogado?.permissoes?.includes(rota);
  };

  const ProtectedRoute = ({ children, permissao }) => {
    if (!usuarioLogado) return <Navigate to="/login" />;
    if (!usuarioLogado.permissoes?.includes(permissao)) return <Navigate to="/" />;
    return children;
  };

  if (carregando) {
    return <div className="p-6">Carregando...</div>;
  }

  if (!usuarioLogado) {
    return (
      <Routes>
        <Route path="/login" element={<Login setUsuarioLogado={setUsuarioLogado} />} />
        <Route path="*" element={<Navigate to="/login" />} />
      </Routes>
    );
  }

  return (
    <div className="p-4">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-3xl font-bold text-purple-900 text-center w-full">Radha One</h1>
        <button
          onClick={() => {
            localStorage.clear();
            setUsuarioLogado(null);
            navigate("/login");
          }}
          className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600 ml-4"
        >
          Sair
        </button>
      </div>

      <nav className="flex gap-4 justify-center mb-6">
  {possuiPermissao("chat") && (
    <Link
      to="/"
      className="px-4 py-2 rounded-md font-medium shadow"
      style={{ backgroundColor: "#8f00ff", color: "#ffffff" }}
    >
      Assistente Sara
    </Link>
  )}
  {possuiPermissao("campanhas") && (
    <Link
      to="/nova-campanha"
      className="px-4 py-2 rounded-md font-medium shadow"
      style={{ backgroundColor: "#8f00ff", color: "#ffffff" }}
    >
      Nova Campanha
    </Link>
  )}
  {possuiPermissao("publicacoes") && (
    <Link
      to="/nova-publicacao"
      className="px-4 py-2 rounded-md font-medium shadow"
      style={{ backgroundColor: "#8f00ff", color: "#ffffff" }}
    >
      Nova Publicação
    </Link>
  )}
  {possuiPermissao("publico") && (
    <Link
      to="/publicos-alvo"
      className="px-4 py-2 rounded-md font-medium shadow"
      style={{ backgroundColor: "#8f00ff", color: "#ffffff  " }}
    >
      Públicos Alvo
    </Link>
  )}
</nav>

      <Routes>
        <Route path="/login" element={<Login setUsuarioLogado={setUsuarioLogado} />} />
        <Route path="/" element={<ProtectedRoute permissao="chat"><Chat usuarioLogado={usuarioLogado} /></ProtectedRoute>} />
        <Route path="/nova-campanha" element={<ProtectedRoute permissao="campanhas"><NovaCampanha usuarioLogado={usuarioLogado} /></ProtectedRoute>} />
        <Route path="/nova-publicacao" element={<ProtectedRoute permissao="publicacoes"><NovaPublicacao usuarioLogado={usuarioLogado} /></ProtectedRoute>} />
        <Route path="/publicos-alvo" element={<ProtectedRoute permissao="publico"><PublicosAlvo usuarioLogado={usuarioLogado} /></ProtectedRoute>} />
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </div>
  );
}

export default AppWrapper;
