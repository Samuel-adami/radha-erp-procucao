import httpx

# Shared HTTP client for RD Station API to preserve cookies across requests
client: httpx.AsyncClient = httpx.AsyncClient(timeout=30.0)
