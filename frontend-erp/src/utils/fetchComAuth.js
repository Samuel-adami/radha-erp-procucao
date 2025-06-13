export async function fetchComAuth(url, options = {}) {
  const token = localStorage.getItem("token");

  // Inicia os cabeçalhos com o que foi passado nas opções.
  const headers = { ...(options.headers || {}) };

  // Adiciona o token de autorização, se existir.
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  // Define o Content-Type como JSON, a menos que seja um FormData.
  // O navegador definirá o Content-Type correto para FormData automaticamente.
  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  // Removemos a lógica de prefixo de URL, pois os componentes
  // já estão chamando a URL completa do gateway.
  // Isso simplifica a função e evita erros.
  const finalUrl = url; 

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
      window.location.href = "/login";
    }

    throw new Error(`Erro ${response.status}: ${errorMessage}`);
  }

  // Se a resposta tiver um corpo, retorna o JSON, senão, retorna null
  const responseText = await response.text();
  return responseText ? JSON.parse(responseText) : null;
}