const GATEWAY_URL = import.meta.env.VITE_GATEWAY_URL || "http://localhost:8010";

export async function fetchComAuth(url, options = {}) {
  // "cache" defaulta para "no-store" para evitar reutilizar respostas em cache,
  // o que pode causar telas desatualizadas. O chamador pode sobrescrever se desejar.
  const { raw, cache = "no-store", ...fetchOpts } = options;
  const token = localStorage.getItem("token");

  const headers = {
    ...(fetchOpts.headers || {}),

    'Cache-Control': 'no-store',

    Pragma: 'no-cache',
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  // Define o Content-Type como JSON, a menos que seja um FormData.
  if (fetchOpts.body && !(fetchOpts.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  // --- LÓGICA DE PREFIXO DE URL RESTAURADA E AJUSTADA ---
  let finalUrl = url;
  if (url.startsWith('/')) { // Se for uma rota relativa
      if (url.startsWith('/publicos') || url.startsWith('/nova-campanha') || url.startsWith('/nova-publicacao') || url.startsWith('/chat') || url.startsWith('/conhecimento') || url.startsWith('/leads')) {
          finalUrl = `${GATEWAY_URL}/marketing-ia${url}`; // Rotas do Marketing Digital IA via Gateway
        } else if (url.startsWith('/importar-xml') || url.startsWith('/gerar-lote-final') || url.startsWith('/carregar-lote-final') || url.startsWith('/executar-nesting') || url.startsWith('/executar-nesting-final') || url.startsWith('/nesting-preview') || url.startsWith('/limpar-nesting-preview') || url.startsWith('/listar-lotes') || url.startsWith('/excluir-lote') || url.startsWith('/config-maquina') || url.startsWith('/config-ferramentas') || url.startsWith('/config-cortes') || url.startsWith('/config-layers') || url.startsWith('/chapas') || url.startsWith('/coletar-layers') || url.startsWith('/coletar-chapas') || url.startsWith('/lotes-producao') || url.startsWith('/lotes-ocorrencias') || url.startsWith('/motivos-ocorrencias') || url.startsWith('/relatorio-ocorrencias') || url.startsWith('/nestings') || url.startsWith('/remover-nesting') || url.startsWith('/download-lote') || url.startsWith('/download-nesting') || url.startsWith('/apontamentos')) {
            finalUrl = `${GATEWAY_URL}/producao${url}`; // Rotas de Produção via Gateway
        } else if (url.startsWith('/comercial')) {
            finalUrl = `${GATEWAY_URL}${url}`; // Rotas do módulo Comercial via Gateway
        } else if (url.startsWith('/finance')) {
            finalUrl = `${GATEWAY_URL}${url}`; // Rotas do módulo Financeiro via Gateway
        } else if (url.startsWith('/universidade-radha')) {
            finalUrl = `${GATEWAY_URL}${url}`; // Rotas da Universidade Radha via Gateway
        } else if (url.startsWith('/clientes') || url.startsWith('/fornecedores')) {
            finalUrl = `${GATEWAY_URL}${url}`; // Cadastros básicos via Gateway
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

  let response;
  try {
    response = await fetch(finalUrl, {
      cache, // garante que as requisições não usem dados antigos do cache do navegador
      ...fetchOpts,
      headers,
    });
  } catch (networkError) {
    console.error('Erro de rede ao chamar', finalUrl, networkError);
    window.dispatchEvent(new CustomEvent('log', { detail: `Erro de rede: ${networkError.message}` }));
    throw new Error(`Erro de rede: ${networkError.message}`);
  }

  if (!response.ok) {
    const contentType = response.headers.get("content-type");
    let errorMessage;

    if (contentType && contentType.includes("application/json")) {
      const errorData = await response.json();
      errorMessage = errorData.detail || JSON.stringify(errorData, null, 2);
    } else {
      errorMessage = await response.text();
    }

    if (response.status === 401 || response.status === 403) {
      // Apenas remove o token; quem chamar decide se recarrega a página
      localStorage.removeItem("token");
    }
    window.dispatchEvent(new CustomEvent('log', { detail: errorMessage }));
    throw new Error(`Erro ${response.status}: ${errorMessage}`);
  }

  if (raw) {
    return response;
  }

  const responseText = await response.text();
  const contentType = response.headers.get("content-type") || "";
  if (!responseText) return null;
  if (contentType.includes("application/json")) {
    try {
      const data = JSON.parse(responseText);
      if (data && data.erro) {
        window.dispatchEvent(new CustomEvent('log', { detail: data.erro }));
      }
      return data;
    } catch (e) {
      console.error("Erro ao parsear JSON", e);
      return null;
    }
  }
  return responseText;
}

export async function downloadComAuth(url, filename) {
  const response = await fetchComAuth(url, { raw: true, method: 'GET', cache: 'no-store' });
  const blob = await response.blob();
  const dlUrl = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = dlUrl;
  let suggested = filename;
  if (!suggested) {
    const cd = response.headers.get('Content-Disposition');
    const m = cd && cd.match(/filename\*?=(?:UTF-8'')?"?([^";]+)"?/i);
    if (m) suggested = decodeURIComponent(m[1]);
  }
  a.download = suggested || '';
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => window.URL.revokeObjectURL(dlUrl), 1000);
}
