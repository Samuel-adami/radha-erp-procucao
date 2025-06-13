export async function fetchComAuth(url, options = {}) {
  const token = localStorage.getItem("token");

  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  // Modifique a URL para apontar para o Gateway API
  // Se a URL já for completa (ex: http://localhost:8010/auth/validate), não prefixe
  // Se for relativa (ex: /chat), adicione o prefixo do gateway e do módulo
  let finalUrl = url;
  if (url.startsWith('/')) { // É uma rota relativa
      // Lógica para determinar qual módulo a rota pertence
      // Isso pode ser feito de forma mais sofisticada se houver rotas sobrepostas
      if (url.startsWith('/publicos') || url.startsWith('/nova-campanha') || url.startsWith('/nova-publicacao') || url.startsWith('/chat') || url.startsWith('/conhecimento') || url.startsWith('/auth')) { // Adicionado /auth aqui
          finalUrl = `http://localhost:8010/marketing-ia${url}`; // Rotas do Marketing Digital IA
      } else if (url.startsWith('/importar-xml') || url.startsWith('/gerar-lote-final')) {
          finalUrl = `http://localhost:8010/producao${url}`; // Rotas de Produção
      }
      // Adicione mais `else if` para outros módulos conforme necessário
  } else {
    // Se a URL já for absoluta e não começar com a porta do gateway, precisamos ajustá-la
    // Isso é uma proteção caso alguma chamada no futuro não use a lógica relativa
    if (url.includes("localhost:8000") || url.includes("localhost:8005") || url.includes("localhost:8009")) {
        finalUrl = url.replace(/localhost:(8000|8005|8009)/, "localhost:8010");
    }
  }


  const response = await fetch(finalUrl, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const contentType = response.headers.get("content-type");
    let errorMessage;

    if (contentType && contentType.includes("application/json")) {
      const errorData = await response.json();
      errorMessage = JSON.stringify(errorData, null, 2);
    } else {
      errorMessage = await response.text();
    }

    // Se for erro de autenticação, redireciona para o login
    if (response.status === 401 || response.status === 403) {
        localStorage.removeItem("token");
        window.location.href = "/login"; // Redireciona para a página de login do ERP
    }

    throw new Error(`Erro ${response.status}: ${errorMessage}`);
  }

  return await response.json();
}