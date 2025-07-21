import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR))

import finance_backend.services.finance_service as finance_service


def test_suggest_account_group():
    assert finance_service.suggest_account_group("Conta de luz") == "despesas/energia"
    assert finance_service.suggest_account_group("Venda para cliente") == "receitas/vendas"
    assert finance_service.suggest_account_group("Outro") is None
