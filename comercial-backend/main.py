from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from database import get_db_connection
import re

TASKS = [
    "Contato Inicial",
    "Visita Técnica/Briefing",
    "Projeto 3D",
    "Orçamento",
    "Apresentação",
    "Venda Concluída",
    "Pasta Final",
]


def get_next_codigo(conn):
    row = conn.execute(
        "SELECT codigo FROM atendimentos ORDER BY id DESC LIMIT 1"
    ).fetchone()
    if row and row[0]:
        m = re.search(r"(\d{4})$", row[0])
        seq = int(m.group(1)) + 1 if m else 1
    else:
        seq = 1
    return f"AT-{seq:04d}"

app = FastAPI(redirect_slashes=False)


@app.get("/")
async def read_root():
    return {"message": "Backend Comercial em execução"}


@app.get("/atendimentos/proximo-codigo")
async def proximo_codigo():
    with get_db_connection() as conn:
        codigo = get_next_codigo(conn)
    return {"codigo": codigo}


@app.post("/atendimentos")
async def criar_atendimento(request: Request):
    data = await request.json()
    with get_db_connection() as conn:
        codigo = data.get("codigo") or get_next_codigo(conn)
        fields = (
            data.get("cliente"),
            codigo,
            data.get("projetos"),
            data.get("previsao_fechamento"),
            data.get("temperatura"),
            int(data.get("tem_especificador") or 0),
            data.get("especificador_nome"),
            data.get("rt_percent"),
            data.get("historico"),
        )
        cur = conn.execute(
            """INSERT INTO atendimentos (
                cliente, codigo, projetos, previsao_fechamento,
                temperatura, tem_especificador, especificador_nome,
                rt_percent, historico
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            fields,
        )
        atendimento_id = cur.lastrowid
        for nome in TASKS:
            conn.execute(
                "INSERT INTO atendimento_tarefas (atendimento_id, nome) VALUES (?, ?)",
                (atendimento_id, nome),
            )
        conn.commit()
    return {"id": atendimento_id, "codigo": codigo}


@app.get("/atendimentos")
async def listar_atendimentos():
    with get_db_connection() as conn:
        rows = conn.execute(
            "SELECT id, cliente, codigo, previsao_fechamento, temperatura FROM atendimentos ORDER BY id DESC"
        ).fetchall()
        itens = [dict(row) for row in rows]
    return {"atendimentos": itens}


@app.get("/atendimentos/{atendimento_id}")
async def obter_atendimento(atendimento_id: int):
    with get_db_connection() as conn:
        row = conn.execute(
            "SELECT * FROM atendimentos WHERE id=?",
            (atendimento_id,),
        ).fetchone()
        if not row:
            return JSONResponse({"detail": "Atendimento não encontrado"}, status_code=404)
        return {"atendimento": dict(row)}


@app.get("/atendimentos/{atendimento_id}/tarefas")
async def listar_tarefas(atendimento_id: int):
    with get_db_connection() as conn:
        rows = conn.execute(
            "SELECT id, nome, concluida, dados FROM atendimento_tarefas WHERE atendimento_id=?",
            (atendimento_id,),
        ).fetchall()
        tarefas = [dict(row) for row in rows]
    return {"tarefas": tarefas}


@app.put("/atendimentos/{atendimento_id}/tarefas/{tarefa_id}")
async def atualizar_tarefa(atendimento_id: int, tarefa_id: int, request: Request):
    data = await request.json()
    campos = []
    valores = []
    if "concluida" in data:
        campos.append("concluida=?")
        valores.append(int(bool(data["concluida"])))
    if "dados" in data:
        campos.append("dados=?")
        valores.append(data["dados"])
    if not campos:
        return {"detail": "Nada para atualizar"}
    valores.extend([atendimento_id, tarefa_id])
    with get_db_connection() as conn:
        conn.execute(
            f"UPDATE atendimento_tarefas SET {', '.join(campos)} WHERE atendimento_id=? AND id=?",
            valores,
        )
        conn.commit()
    return {"ok": True}


@app.get("/condicoes-pagamento")
async def listar_condicoes():
    with get_db_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM condicoes_pagamento ORDER BY id"
        ).fetchall()
        itens = [dict(row) for row in rows]
    return {"condicoes": itens}


@app.post("/condicoes-pagamento")
async def criar_condicao(request: Request):
    data = await request.json()
    dias = ",".join(str(d) for d in data.get("dias_vencimento", []))
    fields = (
        data.get("nome"),
        data.get("numero_parcelas"),
        data.get("juros_parcela", 0),
        dias,
        int(data.get("ativa", 1)),
    )
    with get_db_connection() as conn:
        cur = conn.execute(
            """INSERT INTO condicoes_pagamento (
                nome, numero_parcelas, juros_parcela,
                dias_vencimento, ativa
            ) VALUES (?, ?, ?, ?, ?)""",
            fields,
        )
        conn.commit()
        new_id = cur.lastrowid
    return {"id": new_id}


@app.get("/condicoes-pagamento/{condicao_id}")
async def obter_condicao(condicao_id: int):
    with get_db_connection() as conn:
        row = conn.execute(
            "SELECT * FROM condicoes_pagamento WHERE id=?",
            (condicao_id,),
        ).fetchone()
        if not row:
            return JSONResponse({"detail": "Condição não encontrada"}, status_code=404)
        return {"condicao": dict(row)}


@app.put("/condicoes-pagamento/{condicao_id}")
async def atualizar_condicao(condicao_id: int, request: Request):
    data = await request.json()
    dias = ",".join(str(d) for d in data.get("dias_vencimento", []))
    fields = (
        data.get("nome"),
        data.get("numero_parcelas"),
        data.get("juros_parcela", 0),
        dias,
        int(data.get("ativa", 1)),
        condicao_id,
    )
    with get_db_connection() as conn:
        conn.execute(
            """UPDATE condicoes_pagamento SET
                nome=?, numero_parcelas=?, juros_parcela=?,
                dias_vencimento=?, ativa=?
            WHERE id=?""",
            fields,
        )
        conn.commit()
    return {"ok": True}


@app.delete("/condicoes-pagamento/{condicao_id}")
async def excluir_condicao(condicao_id: int):
    with get_db_connection() as conn:
        conn.execute(
            "DELETE FROM condicoes_pagamento WHERE id=?",
            (condicao_id,),
        )
        conn.commit()
    return {"ok": True}

