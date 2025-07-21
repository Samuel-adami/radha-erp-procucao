from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import JSONResponse
from typing import List
import xml.etree.ElementTree as ET
from datetime import datetime

from database import get_session, get_db_connection, insert_with_id, init_db
from models import (
    Bank,
    BankAccount,
    AccountGroup,
    Payable,
    Receivable,
    FiscalConfig,
)

app = FastAPI(redirect_slashes=False)

# initialize tables
init_db()


# ------------------- Configuracoes -------------------
@app.post("/finance/banks/")
async def create_bank(request: Request):
    data = await request.json()
    session = get_session()
    try:
        bank = Bank(**data)
        session.add(bank)
        session.commit()
        session.refresh(bank)
        return {"id": bank.id}
    finally:
        session.close()


@app.get("/finance/banks/")
async def list_banks():
    session = get_session()
    try:
        itens = [b.__dict__ for b in session.query(Bank).order_by(Bank.id).all()]
        for it in itens:
            it.pop("_sa_instance_state", None)
        return {"banks": itens}
    finally:
        session.close()


@app.put("/finance/banks/{bank_id}")
async def update_bank(bank_id: int, request: Request):
    data = await request.json()
    session = get_session()
    try:
        bank = session.query(Bank).filter(Bank.id == bank_id).first()
        if not bank:
            return JSONResponse({"detail": "Banco não encontrado"}, status_code=404)
        for k, v in data.items():
            setattr(bank, k, v)
        session.commit()
        return {"ok": True}
    finally:
        session.close()


@app.post("/finance/accounts/")
async def create_account(request: Request):
    data = await request.json()
    session = get_session()
    try:
        acc = BankAccount(**data)
        session.add(acc)
        session.commit()
        session.refresh(acc)
        return {"id": acc.id}
    finally:
        session.close()


@app.get("/finance/accounts/")
async def list_accounts():
    session = get_session()
    try:
        itens = [a.__dict__ for a in session.query(BankAccount).order_by(BankAccount.id).all()]
        for it in itens:
            it.pop("_sa_instance_state", None)
        return {"accounts": itens}
    finally:
        session.close()


@app.put("/finance/accounts/{account_id}")
async def update_account(account_id: int, request: Request):
    data = await request.json()
    session = get_session()
    try:
        acc = session.query(BankAccount).filter(BankAccount.id == account_id).first()
        if not acc:
            return JSONResponse({"detail": "Conta não encontrada"}, status_code=404)
        for k, v in data.items():
            setattr(acc, k, v)
        session.commit()
        return {"ok": True}
    finally:
        session.close()


# ------------------- Payables -------------------
@app.post("/finance/payables/")
async def create_payable(request: Request):
    data = await request.json()
    session = get_session()
    try:
        data.setdefault("status", "ABERTO")
        pay = Payable(**data)
        session.add(pay)
        session.commit()
        session.refresh(pay)
        return {"id": pay.id}
    finally:
        session.close()


@app.get("/finance/payables/")
async def list_payables():
    session = get_session()
    try:
        itens = [p.__dict__ for p in session.query(Payable).order_by(Payable.id).all()]
        for it in itens:
            it.pop("_sa_instance_state", None)
        return {"payables": itens}
    finally:
        session.close()


@app.put("/finance/payables/{payable_id}/settle")
async def settle_payable(payable_id: int, request: Request):
    data = await request.json()
    session = get_session()
    try:
        pay = session.query(Payable).filter(Payable.id == payable_id).first()
        if not pay:
            return JSONResponse({"detail": "Conta não encontrada"}, status_code=404)
        pay.status = "PAGO"
        pay.payment_date = data.get("payment_date", datetime.utcnow().isoformat())
        pay.bank_account_id = data.get("bank_account_id")
        session.commit()
        return {"ok": True}
    finally:
        session.close()


@app.post("/finance/payables/import-xml")
async def import_payables_xml(file: UploadFile = File(...)):
    content = await file.read()
    root = ET.fromstring(content)
    created = 0
    session = get_session()
    try:
        for elem in root.findall("payable"):
            pay = Payable(
                description=elem.get("description"),
                amount=float(elem.get("amount", "0")),
                due_date=elem.get("due_date"),
                status="ABERTO",
                supplier_id=int(elem.get("supplier_id") or 0),
                account_group_id=int(elem.get("account_group_id") or 0),
            )
            session.add(pay)
            created += 1
        session.commit()
        return {"created": created}
    finally:
        session.close()


@app.post("/finance/payables/reconciliation")
async def reconcile_payables(request: Request):
    # placeholder for reconciliation logic
    return {"ok": True}


# ------------------- Receivables -------------------
@app.post("/finance/receivables/")
async def create_receivable(request: Request):
    data = await request.json()
    session = get_session()
    try:
        data.setdefault("status", "ABERTO")
        rec = Receivable(**data)
        session.add(rec)
        session.commit()
        session.refresh(rec)
        return {"id": rec.id}
    finally:
        session.close()


@app.get("/finance/receivables/")
async def list_receivables():
    session = get_session()
    try:
        itens = [r.__dict__ for r in session.query(Receivable).order_by(Receivable.id).all()]
        for it in itens:
            it.pop("_sa_instance_state", None)
        return {"receivables": itens}
    finally:
        session.close()


@app.put("/finance/receivables/{rec_id}/settle")
async def settle_receivable(rec_id: int, request: Request):
    data = await request.json()
    session = get_session()
    try:
        rec = session.query(Receivable).filter(Receivable.id == rec_id).first()
        if not rec:
            return JSONResponse({"detail": "Conta não encontrada"}, status_code=404)
        rec.status = "RECEBIDO"
        rec.payment_date = data.get("payment_date", datetime.utcnow().isoformat())
        rec.bank_account_id = data.get("bank_account_id")
        session.commit()
        return {"ok": True}
    finally:
        session.close()


@app.post("/finance/receivables/from-sale")
async def receivables_from_sale(request: Request):
    # placeholder for generation logic
    return {"ok": True}


# ------------------- Fiscal Config -------------------
@app.post("/finance/fiscal-config/")
async def create_fiscal_config(request: Request):
    data = await request.json()
    session = get_session()
    try:
        cfg = FiscalConfig(**data)
        session.add(cfg)
        session.commit()
        session.refresh(cfg)
        return {"id": cfg.id}
    finally:
        session.close()


@app.get("/finance/fiscal-config/")
async def list_fiscal_config():
    session = get_session()
    try:
        itens = [c.__dict__ for c in session.query(FiscalConfig).order_by(FiscalConfig.id).all()]
        for it in itens:
            it.pop("_sa_instance_state", None)
        return {"configs": itens}
    finally:
        session.close()


@app.put("/finance/fiscal-config/{cfg_id}")
async def update_fiscal_config(cfg_id: int, request: Request):
    data = await request.json()
    session = get_session()
    try:
        cfg = session.query(FiscalConfig).filter(FiscalConfig.id == cfg_id).first()
        if not cfg:
            return JSONResponse({"detail": "Configuração não encontrada"}, status_code=404)
        for k, v in data.items():
            setattr(cfg, k, v)
        session.commit()
        return {"ok": True}
    finally:
        session.close()
