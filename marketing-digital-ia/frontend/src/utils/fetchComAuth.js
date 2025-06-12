export async function fetchComAuth(url, options = {}) {
  const token = localStorage.getItem("token");

  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
    Authorization: `Bearer ${token}`,
  };

  const response = await fetch(url, {
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

    throw new Error(`Erro ${response.status}: ${errorMessage}`);
  }

  return await response.json();
}