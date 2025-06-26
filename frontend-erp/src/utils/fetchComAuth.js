const GATEWAY_URL = import.meta.env.VITE_GATEWAY_URL || "http://localhost:8010";

export async function fetchComAuth(url, options = {}) {
  const token = localStorage.getItem("token");

  const headers = {
    ...(options.headers || {}),
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  // Define o Content-Type como JSON, a menos que seja um FormData.
  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  // --- LÓGICA DE PREFIXO DE URL RESTAURADA E AJUSTADA ---
  let finalUrl = url;
  if (url.startsWith('/')) { // Se for uma rota relativa
      if (url.startsWith('/publicos') || url.startsWith('/nova-campanha') || url.startsWith('/nova-publicacao') || url.startsWith('/chat') || url.startsWith('/conhecimento')) {
          finalUrl = `${GATEWAY_URL}/marketing-ia${url}`; // Rotas do Marketing Digital IA via Gateway
        } else if (url.startsWith('/importar-xml') || url.startsWith('/gerar-lote-final') || url.startsWith('/carregar-lote-final') || url.startsWith('/executar-nesting') || url.startsWith('/listar-lotes') || url.startsWith('/excluir-lote') || url.startsWith('/config-maquina') || url.startsWith('/config-ferramentas') || url.startsWith('/config-cortes') || url.startsWith('/config-layers') || url.startsWith('/chapas') || url.startsWith('/coletar-layers') || url.startsWith('/lotes-ocorrencias') || url.startsWith('/motivos-ocorrencias') || url.startsWith('/relatorio-ocorrencias') || url.startsWith('/nestings') || url.startsWith('/remover-nesting')) {
            finalUrl = `${GATEWAY_URL}/producao${url}`; // Rotas de Produção via Gateway
        } else if (url.startsWith('/auth') || url.startsWith('/usuarios') || url.startsWith('/empresa')) {
          finalUrl = `${GATEWAY_URL}${url}`; // Endpoints atendidos diretamente pelo Gateway
      }
  } else {
    // Se a URL já for absoluta e não começar com a porta do gateway, precisamos ajustá-la
    // Isso é uma proteção caso alguma chamada no futuro não use a lógica relativa
    if (url.includes("localhost:8000") || url.includes("localhost:8005") || url.includes("localhost:8009")) {
        const gatewayHost = GATEWAY_URL.replace(/^https?:\/\//, '');
        finalUrl = url.replace(/localhost:(8000|8005|8009)/, gatewayHost);
    }
  }
  // --- FIM DA LÓGICA DE PREFIXO DE URL ---

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

    if (response.status === 401 || response.status === 403) {
      localStorage.removeItem("token");
      window.location.reload();
    }

    throw new Error(`Erro ${response.status}: ${errorMessage}`);
  }

  const responseText = await response.text();
  return responseText ? JSON.parse(responseText) : null;
}