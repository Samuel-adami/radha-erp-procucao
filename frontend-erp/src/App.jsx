import React, { useState, useEffect } from "react";
import { BrowserRouter as Router, Routes, Route, Link, useNavigate, Navigate } from "react-router-dom";
import Login from "./pages/Login"; // Componente de Login a ser criado
import MarketingDigitalIA from "./modules/MarketingDigitalIA"; // Módulo de Marketing Digital IA
import Producao from "./modules/Producao"; // Módulo de Produção
import { fetchComAuth } from "./utils/fetchComAuth"; // Utilitário para requisições com autenticação

function AppWrapper() {
  const [usuarioLogado, setUsuarioLogado] = useState(null);
  const [carregando, setCarregando] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const validateToken = async () => {
      const token = localStorage.getItem("token");
      if (token) {
        try {
          // Validar token no Backend Gateway (PORTA CORRIGIDA PARA 8010)
          const response = await fetchComAuth("http://localhost:8010/auth/validate", {
            headers: { Authorization: `Bearer ${token}` }
          });
          // Assumindo que a resposta inclui o objeto de usuário, talvez com permissões
          setUsuarioLogado(response.usuario); 
        } catch (error) {
          console.error("Erro ao validar token:", error);
          localStorage.removeItem("token");
          setUsuarioLogado(null);
        }
      }
      setCarregando(false);
    };
    validateToken();
  }, []);

  const possuiPermissao = (modulo) => {
    // Lógica para verificar se o usuário tem permissão para acessar o módulo
    // Isso pode ser baseado em 'usuarioLogado.permissoes' que vem do backend
    return usuarioLogado && usuarioLogado.permissoes && usuarioLogado.permissoes.includes(modulo);
  };

  if (carregando) {
    return <div className="p-6 text-center text-xl">Carregando ERP...</div>;
  }

  // Se o usuário não está logado, renderiza apenas a tela de login
  if (!usuarioLogado) {
    return (
      <Routes>
        <Route path="/login" element={<Login setUsuarioLogado={setUsuarioLogado} />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    );
  }

  // Se o usuário está logado, renderiza o layout do ERP
  const handleLogout = () => {
    localStorage.clear(); // Limpa token e qualquer outro dado de sessão
    setUsuarioLogado(null);
    navigate("/login");
  };

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col">
      <header className="bg-purple-900 text-white p-4 shadow-md flex justify-between items-center">
        <h1 className="text-2xl font-bold">Radha ERP</h1>
        <nav className="flex space-x-4">
          {/* Exemplo de links de navegação condicional por permissão */}
          {possuiPermissao("marketing-ia") && (
            <Link to="/marketing-ia" className="hover:underline">Marketing Digital IA</Link>
          )}
          {possuiPermissao("producao") && (
            <Link to="/producao" className="hover:underline">Produção</Link>
          )}
        </nav>
        <button onClick={handleLogout} className="bg-red-500 hover:bg-red-600 text-white px-3 py-1 rounded">Sair</button>
      </header>

      <main className="flex-grow p-4">
        <Routes>
          {/* Removido a rota /login daqui, pois é tratada no if (!usuarioLogado) */}
          {/* <Route path="/login" element={<Login setUsuarioLogado={setUsuarioLogado} />} /> */}

          {/* Rotas protegidas para Marketing Digital IA */}
          <Route path="/marketing-ia/*" element={
            <ProtectedRoute usuarioLogado={usuarioLogado} permissoesObrigatorias={["marketing-ia"]}>
              <MarketingDigitalIA />
            </ProtectedRoute>
          } />

          {/* Rotas protegidas para Produção */}
          <Route path="/producao/*" element={
            <ProtectedRoute usuarioLogado={usuarioLogado} permissoesObrigatorias={["producao"]}>
              <Producao />
            </ProtectedRoute>
          } />

          <Route path="/" element={<p className="text-center text-lg mt-10">Bem-vindo ao ERP Radha. Selecione um módulo no menu.</p>} />
          {/* Ajustado para que o "*" não leve ao login se já estiver logado, mas sim para a home */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
}

// Componente de Rota Protegida
function ProtectedRoute({ children, usuarioLogado, permissoesObrigatorias }) {
  // Se não estiver logado, redireciona para o login (já tratado em AppWrapper)
  // Esta verificação aqui é uma segurança adicional
  if (!usuarioLogado) {
    return <Navigate to="/login" replace />;
  }

  // Verifica se o usuário possui todas as permissões necessárias para o módulo
  const temPermissao = permissoesObrigatorias.every(perm => usuarioLogado.permissoes.includes(perm));

  if (!temPermissao) {
    // Se não tiver permissão, redireciona para uma página de acesso negado ou para o dashboard
    return <div className="p-6 text-red-600 text-center text-xl">Acesso negado. Você não tem permissão para visualizar este módulo.</div>;
  }

  return children;
}

// O componente principal da aplicação. Envolve AppWrapper com BrowserRouter.
function MainApp() {
    return (
        <Router>
            <AppWrapper />
        </Router>
    );
}

export default MainApp;