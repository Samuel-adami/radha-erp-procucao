from datetime import datetime, timedelta
from typing import List
from sqlalchemy import text

from ..database import get_db_connection
from ..models import Payable


def predict_cash_flow(days: int = 30) -> List[dict]:
    """Simple cash flow forecast summing expected receivables and payables."""
    cutoff = (datetime.utcnow() + timedelta(days=days)).isoformat()
    with get_db_connection() as conn:
        pay_total = conn.exec_driver_sql(
            "SELECT SUM(amount) FROM payables WHERE status!='PAGO' AND due_date <= %s",
            (cutoff,),
        ).scalar() or 0
        rec_total = conn.exec_driver_sql(
            "SELECT SUM(amount) FROM receivables WHERE status!='RECEBIDO' AND due_date <= %s",
            (cutoff,),
        ).scalar() or 0
    return [
        {"date": cutoff, "payables": float(pay_total), "receivables": float(rec_total)}
    ]


def suggest_account_group(description: str) -> str | None:
    """Naive NLP logic to suggest an account group based on keywords."""
    desc = description.lower()
    if "energia" in desc or "luz" in desc:
        return "despesas/energia"
    if "venda" in desc or "cliente" in desc:
        return "receitas/vendas"
    return None


def detect_anomalous_payment(payable: Payable) -> bool:
    """Return True if the payable amount is unusually high."""
    with get_db_connection() as conn:
        avg = conn.exec_driver_sql(
            "SELECT AVG(amount) FROM payables WHERE supplier_id=%s", (payable.supplier_id,)
        ).scalar() or 0
    return payable.amount > avg * 3 if avg else False
