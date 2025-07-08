from typing import Any, Dict


def safe_float(value: Any) -> float:
    try:
        return float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        return 0.0


def safe_int(value: Any) -> int:
    try:
        return int(float(value))
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
                or ambiente
            )
            if {
                "descricao",
                "ds_produto",
                "produto",
                "nome",
            }.intersection(obj.keys()) and {
                "vl_total",
                "valor_total",
                "total",
                "valor",
            }.intersection(obj.keys()):
                desc = (
                    obj.get("descricao")
                    or obj.get("ds_produto")
                    or obj.get("produto")
                    or obj.get("nome")
                )
                qtd = obj.get("quantidade") or obj.get("qtde") or obj.get("qtd")
                unit = (
                    obj.get("unitario")
                    or obj.get("vl_unitario")
                    or obj.get("valor_unitario")
                )
                tot = (
                    obj.get("vl_total")
                    or obj.get("valor_total")
                    or obj.get("total")
                    or obj.get("valor")
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
