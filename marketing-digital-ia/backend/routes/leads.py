from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
import json
import httpx
import os
from services.leads_info_service import obter_info, salvar_info

GATEWAY_URL = os.getenv("GATEWAY_URL", "http://127.0.0.1:8040")
from datetime import datetime
from services.rdstation_service import obter_leads
from security import verificar_autenticacao

router = APIRouter(prefix="/leads", tags=["Leads"])

# Permissão "marketing-ia/gestao-leads"
autorizacao = Depends(verificar_autenticacao(permissoes=["marketing-ia/gestao-leads"]))

@router.get("/", dependencies=[autorizacao])
async def listar_leads(
    inicio: str | None = Query(None),
    fim: str | None = Query(None),
    campanha: str | None = Query(None),
    estagio: str | None = Query(None),
    force_refresh: bool = Query(
        False,
        description="Força atualização dos leads ignorando o cache em memória",
    ),
):
    try:
        dados = await obter_leads(force_refresh=force_refresh)
    except HTTPException as exc:
        # Repassa problemas de autenticação da RD Station para o frontend
        raise exc

    def filtro(item: dict) -> bool:
        data_conv = item.get("created_at") or item.get("conversion_date")
        if inicio:
            try:
                if data_conv and datetime.fromisoformat(data_conv[:19]) < datetime.fromisoformat(inicio):
                    return False
            except Exception:
                pass
        if fim:
            try:
                if data_conv and datetime.fromisoformat(data_conv[:19]) > datetime.fromisoformat(fim):
                    return False
            except Exception:
                pass
        if campanha and campanha not in str(item):
            return False
        if estagio and str(item.get("funnel_step", "")).lower() != estagio.lower():
            return False
        return True

    leads_filtrados = [
        {
            "nome": item.get("name"),
            "email": item.get("email"),
            "origem": item.get("traffic_source", {}).get("source"),
            "data_conversao": item.get("created_at"),
            "estagio": item.get("funnel_step"),
            "id": item.get("uuid"),
        }
        for item in dados
        if filtro(item)
    ]

    return {"leads": leads_filtrados}


@router.get("/info/{rd_id}", dependencies=[autorizacao])
async def detalhes_lead(rd_id: str):
    info = obter_info(rd_id)
    return info or {}


@router.post("/info/{rd_id}", dependencies=[autorizacao])
async def atualizar_lead(
    rd_id: str,
    estagio: str = Form(...),
    descricao: str = Form(""),
    vendedor_id: int | None = Form(None),
    cliente: str | None = Form(None),
    files: list[UploadFile] = File([]),
):
    arquivos = []
    for f in files:
        arquivos.append((f.filename, await f.read()))
    dados = {"estagio": estagio, "descricao": descricao, "vendedor_id": vendedor_id}

    info = obter_info(rd_id) or {}

    if estagio.lower() == "convertido" and not info.get("cliente_id"):
        cliente_data = json.loads(cliente) if cliente else {}
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{GATEWAY_URL}/clientes", json=cliente_data)
            resp.raise_for_status()
            cid = resp.json().get("id")
            at_resp = await client.post(
                f"{GATEWAY_URL}/comercial/atendimentos",
                json={"cliente": cliente_data.get("nome"), "vendedor": vendedor_id},
            )
            at_resp.raise_for_status()
            aid = at_resp.json().get("id")
        dados["cliente_id"] = cid
        dados["atendimento_id"] = aid

    nova_info = salvar_info(rd_id, dados, arquivos)
    return nova_info
