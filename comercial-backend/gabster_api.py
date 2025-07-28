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


def list_orcamentos_cliente(
    cd_projeto: Optional[int] = None,
    offset: int = 0,
    limit: int = 20,
    *,
    user: Optional[str] = None,
    api_key: Optional[str] = None
) -> dict[str, Any]:
    """Return list of budgets for a given project from the Gabster API."""
    params = []
    if cd_projeto is not None:
        params.append(f"cd_projeto={cd_projeto}")
    params.append(f"offset={offset}")
    params.append(f"limit={limit}")
    params.append("format=json")
    url = f"{BASE_URL}orcamento_cliente/?" + "&".join(params)
    headers = _auth_header(user, api_key)
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()
    return response.json()


def list_orcamento_cliente_item(
    offset: int = 0,
    limit: int = 20,
    cd_orcamento_cliente: Optional[int] = None,
    *,
    user: Optional[str] = None,
    api_key: Optional[str] = None,
) -> dict[str, Any]:
    """Return items from the 'Orçamento de Cliente' endpoint, optionally filtered by cd_orcamento_cliente."""
    params = [f"offset={offset}", f"limit={limit}", "format=json"]
    if cd_orcamento_cliente is not None:
        params.insert(0, f"cd_orcamento_cliente={cd_orcamento_cliente}")
    url = f"{BASE_URL}orcamento_cliente_item/?" + "&".join(params)
    headers = _auth_header(user, api_key)
    # debug: mostra URL chamada para itens de orçamento de cliente
    import logging
    logging.info("GET ORCAMENTO_CLIENTE_ITEM: %s", url)
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


def get_acabamento(
    cd_acabamento: int,
    *, user: Optional[str] = None,
    api_key: Optional[str] = None
) -> dict[str, Any]:
    """Fetch acabamento details from Gabster API."""
    url = f"{BASE_URL}acabamento/{cd_acabamento}/?format=json"
    headers = _auth_header(user, api_key)
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()
    return response.json()


def get_componente(
    cd_componente: int,
    *, user: Optional[str] = None,
    api_key: Optional[str] = None
) -> dict[str, Any]:
    """Fetch componente details from Gabster API."""
    url = f"{BASE_URL}componente/{cd_componente}/?format=json"
    headers = _auth_header(user, api_key)
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()
    return response.json()


def get_produto(
    cd_produto: int,
    *, user: Optional[str] = None,
    api_key: Optional[str] = None
) -> dict[str, Any]:
    """Fetch produto details from Gabster API."""
    url = f"{BASE_URL}produto/{cd_produto}/?format=json"
    headers = _auth_header(user, api_key)
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()
    return response.json()
