import re


def safe_float(value):
    """Convert value to float returning 0.0 when invalid."""
    try:
        val = str(value).replace(".", "")
        return float(val)
    except (TypeError, ValueError):
        return 0.0


def safe_int(value):
    """Convert value to int returning 0 when invalid."""
    try:
        val = str(value).replace(".", "")
        return int(float(val))
    except (TypeError, ValueError):
        return 0


TASKS = [
    "Contato Inicial",
    "Visita Técnica/Briefing",
    "Projeto 3D",
    "Negociação",
    "Apresentação",
    "Fechamento da Venda",
    "Pasta Final",
]


def get_next_codigo(conn):
    row = conn.exec_driver_sql(
        "SELECT codigo FROM atendimentos ORDER BY id DESC LIMIT 1"
    ).fetchone()
    if row and row[0]:
        m = re.search(r"(\d{4})$", row[0])
        seq = int(m.group(1)) + 1 if m else 1
    else:
        seq = 1
    return f"AT-{seq:04d}"
