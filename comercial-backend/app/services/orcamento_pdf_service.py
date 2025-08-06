import re
from typing import IO
import pdfplumber


def parse_gabster_pdf(file: IO) -> dict:
    """Read a Gabster budget PDF and return items and total."""
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            text += "\n" + page_text

    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    try:
        start_idx = next(i for i, l in enumerate(lines) if "ITENS DO PROJETO" in l)
    except StopIteration:
        return {"itens": [], "total": 0}

    idx = start_idx + 1
    while idx < len(lines) and not re.search(r"\d", lines[idx]):
        idx += 1

    items_raw = []
    for line in lines[idx:]:
        if line.startswith("MATERIAIS") or line.startswith("SUBTOTAL") or line.startswith("TOTAL"):
            break
        parts = re.split(r"\s{2,}|\t", line)
        if len(parts) >= 2:
            desc = parts[0].strip()
            valor_str = parts[-1].replace("R$", "").replace(".", "").replace(",", ".")
            try:
                valor = float(valor_str)
            except ValueError:
                continue
            items_raw.append((desc, valor))

    grouped = {}
    for desc, val in items_raw:
        if desc not in grouped:
            grouped[desc] = {"descricao": desc, "unitario": val, "quantidade": 1, "total": val}
        else:
            item = grouped[desc]
            item["quantidade"] += 1
            item["total"] = item["unitario"] * item["quantidade"]

    itens = list(grouped.values())

    total_val = 0
    m_total = re.search(r"TOTAL DO ORÇAMENTO:\s*R\$\s*([\d\.,]+)", text)
    if m_total:
        total_val = float(m_total.group(1).replace(".", "").replace(",", "."))
    else:
        total_val = sum(it["total"] for it in itens)

    return {"itens": itens, "total": total_val}
