from fastapi import APIRouter, Depends, Query
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
):
    dados = await obter_leads()

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
