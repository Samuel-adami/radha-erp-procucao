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
            amb = (
                obj.get("ambiente")
                or obj.get("ambiente_nome")
                or obj.get("nm_ambiente")
                or obj.get("nome_ambiente")
                or obj.get("ds_ambiente")
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



            if desc_keys.intersection(obj.keys()) and total_keys.intersection(obj.keys()):
                desc = (
                    obj.get("descricao")
                    or obj.get("ds_produto")
                    or obj.get("produto")
                    or obj.get("nome")
                    or obj.get("desc_item")
                    or obj.get("descricao_item")
                    or obj.get("ds_item")
                )
                qtd = (
                    obj.get("quantidade")
                    or obj.get("qtde")
                    or obj.get("qtd")
                    or obj.get("quantidade_item")
                    or obj.get("qt_item")
                )
                unit = (
                    obj.get("unitario")
                    or obj.get("vl_unitario")
                    or obj.get("valor_unitario")
                    or obj.get("valor_unit")
                    or obj.get("vl_unit")
                    or obj.get("vl_preco_unitario")
                    or obj.get("preco_unitario")
                )
                tot = (
                    obj.get("vl_total")
                    or obj.get("valor_total")
                    or obj.get("total")
                    or obj.get("valor")
                    or obj.get("vl_tot_item")
                    or obj.get("preco_total")
                    or obj.get("vl_preco_total")
                )
                add_item(amb or "Projeto", desc, qtd, unit, tot)
                return

            for k, v in obj.items():
                walk(v, amb)
        elif isinstance(obj, list):
            for v in obj:
                walk(v, ambiente)

    walk(data)
    return {"projetos": projetos}
