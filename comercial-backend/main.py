from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from database import get_db_connection

app = FastAPI(redirect_slashes=False)


@app.get("/")
async def read_root():
    return {"message": "Backend Comercial em execução"}


@app.post("/atendimentos")
async def criar_atendimento(request: Request):
    data = await request.json()
    fields = (
        data.get("cliente"),
        data.get("codigo"),
        data.get("projetos"),
        data.get("previsao_fechamento"),
        data.get("temperatura"),
        int(data.get("tem_especificador") or 0),
        data.get("especificador_nome"),
        data.get("rt_percent"),
        data.get("historico"),
    )
    with get_db_connection() as conn:
        cur = conn.execute(
            """INSERT INTO atendimentos (
                cliente, codigo, projetos, previsao_fechamento,
                temperatura, tem_especificador, especificador_nome,
                rt_percent, historico
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            fields,
        )
        conn.commit()
        new_id = cur.lastrowid
    return {"id": new_id}


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
