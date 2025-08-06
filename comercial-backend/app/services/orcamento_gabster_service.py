from typing import Any, Dict


def safe_float(value: Any) -> float:
    try:
        val = str(value).replace(".", "").replace(",", ".")
        return float(val)
    except (TypeError, ValueError):
        return 0.0


def safe_int(value: Any) -> int:
    try:
        val = str(value).replace(".", "").replace(",", ".")
        return int(float(val))
    except (TypeError, ValueError):
        return 0


def parse_gabster_projeto(data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Convert raw Gabster API project data to the structure used by the frontend.

    The Gabster API structure is not officially documented here, so this parser
    tries to extract useful information using a few common field names. The
    result matches the format produced by ``parse_promob_xml`` so that the
    frontend can display a table with the items and total of each ambiente.
    """

    projetos: Dict[str, Dict[str, Any]] = {}

    if not isinstance(data, dict):
        return {"projetos": projetos}

    # Helper to add an item to an ambiente
    def add_item(amb: str, desc: str, qtd: Any, unit: Any, tot: Any):
        amb = amb or "Projeto"
        projetos.setdefault(amb, {"itens": [], "total": 0.0})
        q = safe_int(qtd) or 1
        t = safe_float(tot)
        u = safe_float(unit)
        if not u and q:
            u = t / q if q else t
        projetos[amb]["itens"].append(
            {"descricao": str(desc), "unitario": u, "quantidade": q, "total": t}
        )
        projetos[amb]["total"] += t

    def walk(obj: Any, ambiente: str | None = None):
        if isinstance(obj, dict):
            # permite chaves com maiúsculas/minúsculas diferentes
            lower = {k.lower(): v for k, v in obj.items()}

            amb = (
                lower.get("ambiente")
                or lower.get("ambiente_nome")
                or lower.get("nm_ambiente")
                or lower.get("nome_ambiente")
                or lower.get("ds_ambiente")
                or ambiente
            )

            desc_keys = {
                "descricao",
                "ds_produto",
                "produto",
                "nome",
                "desc_item",
                "descricao_item",
                "ds_item",
            }

            total_keys = {
                "vl_total",
                "valor_total",
                "total",
                "valor",
                "vl_tot_item",
                "preco_total",
                "vl_preco_total",
            }

            if desc_keys.intersection(lower.keys()) and total_keys.intersection(lower.keys()):
                desc = (
                    lower.get("descricao")
                    or lower.get("ds_produto")
                    or lower.get("produto")
                    or lower.get("nome")
                    or lower.get("desc_item")
                    or lower.get("descricao_item")
                    or lower.get("ds_item")
                )
                qtd = (
                    lower.get("quantidade")
                    or lower.get("qtde")
                    or lower.get("qtd")
                    or lower.get("quantidade_item")
                    or lower.get("qt_item")
                )
                unit = (
                    lower.get("unitario")
                    or lower.get("vl_unitario")
                    or lower.get("valor_unitario")
                    or lower.get("valor_unit")
                    or lower.get("vl_unit")
                    or lower.get("vl_preco_unitario")
                    or lower.get("preco_unitario")
                )
                tot = (
                    lower.get("vl_total")
                    or lower.get("valor_total")
                    or lower.get("total")
                    or lower.get("valor")
                    or lower.get("vl_tot_item")
                    or lower.get("preco_total")
                    or lower.get("vl_preco_total")
                )
                add_item(amb or "Projeto", desc, qtd, unit, tot)
                return

            for v in obj.values():
                walk(v, amb)
        elif isinstance(obj, list):
            for v in obj:
                walk(v, ambiente)

    walk(data)
    return {"projetos": projetos}
