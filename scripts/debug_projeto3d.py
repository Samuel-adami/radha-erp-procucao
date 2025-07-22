import os
import json
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load .env if present
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable not set")

schema = os.getenv("DATABASE_SCHEMA")
connect_args = {"options": f"-c search_path={schema}"} if schema else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)


def listar_atendimentos():
    """Retorna lista de atendimentos disponíveis."""
    with engine.connect() as conn:
        rows = (
            conn.execute(
                text("SELECT id, cliente, codigo FROM atendimentos ORDER BY id DESC")
            )
            .mappings()
            .all()
        )
    return list(rows)


def debug_projeto(atendimento_id: int) -> None:
    print(f"\n=== Debug Projeto 3D para Atendimento {atendimento_id} ===")
    with engine.connect() as conn:
        tarefas = conn.execute(
            text(
                "SELECT id, nome, dados FROM atendimento_tarefas "
                "WHERE atendimento_id=:aid ORDER BY id"
            ),
            {"aid": atendimento_id},
        ).mappings().all()

        if not tarefas:
            print("Nenhuma tarefa encontrada para este atendimento.")
            return

        for t in tarefas:
            print(f"\n--- Tarefa '{t['nome']}' (ID {t['id']}) ---")
            dados_json = {}
            if t.get("dados"):
                try:
                    dados_json = json.loads(t["dados"])
                except Exception as exc:
                    print("Erro ao decodificar JSON dos dados:", exc)
            if dados_json.get("projetos"):
                print("Conteudo enviado em dados.projetos:")
                print(json.dumps(dados_json["projetos"], indent=2, ensure_ascii=False))
            else:
                print("dados.projetos vazio ou ausente")

            itens = conn.execute(
                text(
                    "SELECT ambiente, descricao, unitario, quantidade, total "
                    "FROM projeto_itens WHERE tarefa_id=:tid ORDER BY id"
                ),
                {"tid": t["id"]},
            ).mappings().all()

            if itens:
                print(f"{len(itens)} itens encontrados na tabela projeto_itens:")
                for it in itens:
                    print(
                        f" - {it['ambiente']}: {it['descricao']} | "
                        f"{it['quantidade']} x {it['unitario']} = {it['total']}"
                    )
            else:
                print("Nenhum registro em projeto_itens para esta tarefa")

        # Revisar reconstrução das tarefas como no endpoint /tarefas
        print("\n--- Resultado da busca em projeto_itens via logica do endpoint ---")
        recon = []
        for t in tarefas:
            dados = {}
            if t.get("dados"):
                try:
                    dados = json.loads(t["dados"])
                except Exception:
                    dados = {}
            itens = conn.execute(
                text(
                    "SELECT ambiente, descricao, unitario, quantidade, total "
                    "FROM projeto_itens WHERE tarefa_id=:tid ORDER BY id"
                ),
                {"tid": t["id"]},
            ).mappings().all()
            if itens:
                projetos = {}
                for it in itens:
                    amb = it["ambiente"]
                    projetos.setdefault(amb, {"itens": [], "total": 0})
                    projetos[amb]["itens"].append(
                        {
                            "descricao": it["descricao"],
                            "unitario": it["unitario"],
                            "quantidade": it["quantidade"],
                            "total": it["total"],
                        }
                    )
                    projetos[amb]["total"] += it["total"]
                dados["projetos"] = projetos
            recon.append({"id": t["id"], "nome": t["nome"], "dados": dados})

        print(json.dumps(recon, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Debug Projeto 3D")
    parser.add_argument(
        "atendimento_id",
        type=int,
        nargs="?",
        help="ID do atendimento (opcional; se omitido processa todos)",
    )
    args = parser.parse_args()

    if args.atendimento_id is not None:
        debug_projeto(args.atendimento_id)
    else:
        atendimentos = listar_atendimentos()
        if not atendimentos:
            print("Nenhum atendimento encontrado.")
        for a in atendimentos:
            debug_projeto(a["id"])

