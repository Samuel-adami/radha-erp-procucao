import os
from typing import Any, Optional

import requests

BASE_URL = "https://api.gabster.com.br/integracao/api/v2/"


def _auth_header(user: Optional[str] = None, api_key: Optional[str] = None) -> dict:
    """Return authorization header using user and api key from env if not given."""
    user = user or os.environ.get("GABSTER_API_USER", "")
    api_key = api_key or os.environ.get("GABSTER_API_KEY", "")
    token = f"ApiKey {user}:{api_key}"
    return {"Authorization": token}


def get_projeto(cd_projeto: int, *, user: Optional[str] = None, api_key: Optional[str] = None) -> dict[str, Any]:
    """Fetch project details from Gabster API."""
    url = f"{BASE_URL}projeto/{cd_projeto}/?format=json"
    headers = _auth_header(user, api_key)
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()
    return response.json()


def list_orcamentos_cliente(*, user: Optional[str] = None, api_key: Optional[str] = None) -> dict[str, Any]:
    """Return list of budgets available for the authenticated user."""
    url = f"{BASE_URL}orcamento_cliente/?format=json"
    headers = _auth_header(user, api_key)
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()
    return response.json()

