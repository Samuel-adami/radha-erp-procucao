import os
from typing import Any, Optional, List

from pydantic import BaseModel

from dotenv import load_dotenv

load_dotenv()

import requests

BASE_URL = "https://api.gabster.com.br/integracao/api/v2/"


class Projeto(BaseModel):
    """Representation of the Projeto object returned by the Gabster API."""

    id: int
    nome: Optional[str] = None
    cd_cliente: Optional[int] = None
    nome_arquivo_skp: Optional[str] = None
    identificador_arquivo_skp: Optional[str] = None
    descricao: Optional[str] = None
    observacao: Optional[str] = None
    ambiente: Optional[str] = None
    projeto_ref: Optional[int] = None


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


def list_orcamento_cliente_item(
    offset: int = 0,
    limit: int = 20,
    *,
    user: Optional[str] = None,
    api_key: Optional[str] = None,
) -> dict[str, Any]:
    """Return items from the 'Orçamento de Cliente' endpoint."""
    url = (
        f"{BASE_URL}orcamento_cliente_item/?offset={offset}&limit={limit}&format=json"
    )
    headers = _auth_header(user, api_key)
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()
    return response.json()


def list_projetos(
    offset: int = 0,
    limit: int = 20,
    *,
    user: Optional[str] = None,
    api_key: Optional[str] = None,
) -> List[Projeto]:
    """Return a list of ``Projeto`` objects from the Gabster API."""
    url = f"{BASE_URL}projeto/?offset={offset}&limit={limit}&format=json"
    headers = _auth_header(user, api_key)
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()
    data = response.json()
    projetos = []
    if isinstance(data, dict):
        items = data.get("results") or data.get("items") or data.get("data") or []
    else:
        items = data
    for item in items:
        try:
            projetos.append(Projeto(**item))
        except Exception:
            # ignore invalid items
            continue
    return projetos

