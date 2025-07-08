from fastapi import FastAPI, Request, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from database import get_db_connection, init_db
from orcamento_promob import parse_promob_xml
from gabster_api import get_projeto
from datetime import datetime
import re
import json
import requests

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

app = FastAPI(redirect_slashes=False)

# Initialize commercial database tables on startup
init_db()


@app.get("/")
async def read_root():
    return {"message": "Backend Comercial em execução"}


@app.get("/atendimentos/proximo-codigo")
async def proximo_codigo():
    with get_db_connection() as conn:
        codigo = get_next_codigo(conn)
    return {"codigo": codigo}


@app.post("/leitor-orcamento-gabster")
async def leitor_orcamento_gabster(request: Request):
    """Retrieve Gabster project via API instead of PDF upload."""
    params = await request.json()
    cd_projeto = params.get("cd_projeto")
    usuario = params.get("usuario")
    chave = params.get("chave")
    if not cd_projeto:
        return JSONResponse({"detail": "cd_projeto ausente"}, status_code=400)
    try:
        projeto = get_projeto(cd_projeto, user=usuario, api_key=chave)
    except requests.exceptions.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail="Projeto não encontrado na Gabster. Verifique o código informado.",
            )
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:  # generic errors
        raise HTTPException(status_code=400, detail=str(exc))
    return projeto


@app.post("/leitor-orcamento-promob")
async def leitor_orcamento_promob(file: UploadFile = File(...)):
    """Parse Promob XML budget and return structured data."""
    data = parse_promob_xml(file.file)
    return data


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
            data.get("entrega_diferente"),
            data.get("historico"),
            json.dumps(data.get("arquivos", [])),
            data.get("procedencia"),
            data.get("vendedor"),
            data.get("telefone"),
            data.get("email"),
            data.get("rua"),
            data.get("numero"),
            data.get("complemento"),
            data.get("bairro"),
            data.get("cidade"),
            data.get("estado"),
            data.get("cep"),
            datetime.utcnow().isoformat(),
        )
        cur = conn.exec_driver_sql(
            """INSERT INTO atendimentos (
                cliente, codigo, projetos, previsao_fechamento,
                temperatura, tem_especificador, especificador_nome,
                rt_percent, entrega_diferente, historico, arquivos_json,
                procedencia, vendedor, telefone, email,
                rua, numero, complemento, bairro,
                cidade, estado, cep,
                data_cadastro
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            fields,
        )
        atendimento_id = cur.lastrowid
        for nome in TASKS:
            conn.exec_driver_sql(
                "INSERT INTO atendimento_tarefas (atendimento_id, nome) VALUES (%s, %s)",
                (atendimento_id, nome),
            )
        conn.commit()
    return {"id": atendimento_id, "codigo": codigo}


@app.get("/atendimentos")
async def listar_atendimentos():
    with get_db_connection() as conn:
        rows = (
            conn.exec_driver_sql(
                "SELECT id, cliente, codigo, previsao_fechamento, temperatura, data_cadastro FROM atendimentos ORDER BY id DESC"
            )
            .mappings()
            .all()
        )
        itens = [dict(row) for row in rows]
    return {"atendimentos": itens}


@app.get("/atendimentos/{atendimento_id}")
async def obter_atendimento(atendimento_id: int):
    with get_db_connection() as conn:
        row = (
            conn.exec_driver_sql(
                "SELECT * FROM atendimentos WHERE id=%s",
                (atendimento_id,),
            )
            .mappings()
            .fetchone()
        )
        if not row:
            return JSONResponse({"detail": "Atendimento não encontrado"}, status_code=404)
        item = dict(row)
        if item.get("arquivos_json"):
            try:
                item["arquivos"] = json.loads(item["arquivos_json"])
            except Exception:
                item["arquivos"] = []
        return {"atendimento": item}


@app.put("/atendimentos/{atendimento_id}")
async def atualizar_atendimento(atendimento_id: int, request: Request):
    data = await request.json()
    campos = []
    valores = []
    for campo in [
        "vendedor",
        "telefone",
        "email",
        "rua",
        "numero",
        "complemento",
        "bairro",
        "cidade",
        "estado",
        "cep",
        "entrega_diferente",
        "procedencia",
        "projetos",
    ]:
        if campo in data:
            campos.append(f"{campo}=%s")
            valores.append(data[campo])
    if not campos:
        return {"detail": "Nada para atualizar"}
    valores.append(atendimento_id)
    with get_db_connection() as conn:
        conn.exec_driver_sql(
            f"UPDATE atendimentos SET {', '.join(campos)} WHERE id=%s",
            valores,
        )
        conn.commit()
    return {"ok": True}


@app.get("/atendimentos/{atendimento_id}/tarefas")
async def listar_tarefas(atendimento_id: int):
    with get_db_connection() as conn:

        rows = (
            conn.exec_driver_sql(
                "SELECT id, nome, concluida, dados, data_execucao FROM atendimento_tarefas WHERE atendimento_id=%s ORDER BY id",
                (atendimento_id,),
            )
            .mappings()
            .all()
        )

        tarefas = []
        for row in rows:
            item = dict(row)
            dados = {}
            if item.get("dados"):
                try:
                    dados = json.loads(item["dados"])
                except Exception:
                    dados = {}

            # recuperar itens do projeto, se houver

            itens_rows = (
                conn.exec_driver_sql(
                    "SELECT ambiente, descricao, unitario, quantidade, total FROM projeto_itens WHERE tarefa_id=%s ORDER BY id",
                    (item["id"],),
                )
                .mappings()
                .all()
            )

            if itens_rows:
                projetos = {}
                for it in itens_rows:
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
                item["dados"] = json.dumps(dados)
            tarefas.append(item)
    return {"tarefas": tarefas}


@app.put("/atendimentos/{atendimento_id}/tarefas/{tarefa_id}")
async def atualizar_tarefa(atendimento_id: int, tarefa_id: int, request: Request):
    data = await request.json()
    campos = []
    valores = []
    dados_json = {}
    with get_db_connection() as conn:
        row = (
            conn.exec_driver_sql(
                "SELECT id, concluida FROM atendimento_tarefas WHERE atendimento_id=%s AND id=%s",
                (atendimento_id, tarefa_id),
            )
            .mappings()
            .fetchone()
        )
        if not row:
            return JSONResponse({"detail": "Tarefa não encontrada"}, status_code=404)
        if not row["concluida"]:
            prev = conn.exec_driver_sql(
                "SELECT COUNT(*) FROM atendimento_tarefas WHERE atendimento_id=%s AND id < %s AND concluida=0",
                (atendimento_id, tarefa_id),
            ).scalar()
            if prev > 0:
                return JSONResponse(
                    {"detail": "Não é possível executar esta tarefa antes de concluir as anteriores"},
                    status_code=400,
                )
    if "concluida" in data:
        concl = bool(data["concluida"])
        campos.append("concluida=%s")
        valores.append(int(concl))
        campos.append("data_execucao=%s")
        valores.append(datetime.utcnow().isoformat() if concl else None)
    if "dados" in data:
        campos.append("dados=%s")
        valores.append(data["dados"])
        try:
            dados_json = json.loads(data["dados"])
        except Exception:
            dados_json = {}
    if not campos:
        return {"detail": "Nada para atualizar"}
    valores.extend([atendimento_id, tarefa_id])
    with get_db_connection() as conn:
        conn.exec_driver_sql(
            f"UPDATE atendimento_tarefas SET {', '.join(campos)} WHERE atendimento_id=%s AND id=%s",
            valores,
        )
        if "dados" in data and dados_json.get("projetos"):

            conn.exec_driver_sql("DELETE FROM projeto_itens WHERE tarefa_id=%s", (tarefa_id,))
            for amb, info in dados_json["projetos"].items():
                for it in info.get("itens", []):
                    conn.exec_driver_sql(

                        """
                        INSERT INTO projeto_itens (
                            atendimento_id, tarefa_id, ambiente,
                            descricao, unitario, quantidade, total
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            atendimento_id,
                            tarefa_id,
                            amb,
                            it.get("descricao"),
                            float(it.get("unitario", 0)),
                            int(it.get("quantidade", 0)),
                            float(it.get("total", 0)),
                        ),
                    )
        conn.commit()
    return {"ok": True}


@app.delete("/atendimentos/{atendimento_id}")
async def excluir_atendimento(atendimento_id: int):
    with get_db_connection() as conn:

        conn.exec_driver_sql(
            "DELETE FROM projeto_itens WHERE atendimento_id=%s",
            (atendimento_id,),
        )
        conn.exec_driver_sql(

            "DELETE FROM atendimento_tarefas WHERE atendimento_id=%s",
            (atendimento_id,),
        )
        conn.exec_driver_sql(
            "DELETE FROM atendimentos WHERE id=%s",
            (atendimento_id,),
        )
        conn.commit()
    return {"ok": True}


@app.get("/condicoes-pagamento")
async def listar_condicoes():
    with get_db_connection() as conn:
        rows = (
            conn.exec_driver_sql(
                "SELECT * FROM condicoes_pagamento ORDER BY id"
            )
            .mappings()
            .all()
        )
        itens = []
        for row in rows:
            item = dict(row)
            if item.get("parcelas_json"):
                try:
                    item["parcelas"] = json.loads(item["parcelas_json"])
                except Exception:
                    item["parcelas"] = []
            itens.append(item)
    return {"condicoes": itens}


@app.post("/condicoes-pagamento")
async def criar_condicao(request: Request):
    data = await request.json()
    dias = ",".join(str(d) for d in data.get("dias_vencimento", []))
    parcelas = json.dumps(data.get("parcelas", []))
    fields = (
        data.get("nome"),
        data.get("numero_parcelas"),
        data.get("juros_parcela", 0),
        dias,
        int(data.get("ativa", 1)),
        parcelas,
    )
    with get_db_connection() as conn:
        cur = conn.exec_driver_sql(
            """INSERT INTO condicoes_pagamento (
                nome, numero_parcelas, juros_parcela,
                dias_vencimento, ativa, parcelas_json
            ) VALUES (%s, %s, %s, %s, %s, %s)""",
            fields,
        )
        conn.commit()
        new_id = cur.lastrowid
    return {"id": new_id}


@app.get("/condicoes-pagamento/{condicao_id}")
async def obter_condicao(condicao_id: int):
    with get_db_connection() as conn:
        row = (
            conn.exec_driver_sql(
                "SELECT * FROM condicoes_pagamento WHERE id=%s",
                (condicao_id,),
            )
            .mappings()
            .fetchone()
        )
        if not row:
            return JSONResponse({"detail": "Condição não encontrada"}, status_code=404)
        item = dict(row)
        if item.get("parcelas_json"):
            try:
                item["parcelas"] = json.loads(item["parcelas_json"])
            except Exception:
                item["parcelas"] = []
        return {"condicao": item}


@app.put("/condicoes-pagamento/{condicao_id}")
async def atualizar_condicao(condicao_id: int, request: Request):
    data = await request.json()
    dias = ",".join(str(d) for d in data.get("dias_vencimento", []))
    parcelas = json.dumps(data.get("parcelas", []))
    fields = (
        data.get("nome"),
        data.get("numero_parcelas"),
        data.get("juros_parcela", 0),
        dias,
        int(data.get("ativa", 1)),
        parcelas,
        condicao_id,
    )
    with get_db_connection() as conn:
        conn.exec_driver_sql(
            """UPDATE condicoes_pagamento SET
                nome=%s, numero_parcelas=%s, juros_parcela=%s,
                dias_vencimento=%s, ativa=%s, parcelas_json=%s
            WHERE id=%s""",
            fields,
        )
        conn.commit()
    return {"ok": True}


@app.delete("/condicoes-pagamento/{condicao_id}")
async def excluir_condicao(condicao_id: int):
    with get_db_connection() as conn:
        conn.exec_driver_sql(
            "DELETE FROM condicoes_pagamento WHERE id=%s",
            (condicao_id,),
        )
        conn.commit()
    return {"ok": True}


@app.get("/templates")
async def listar_templates(tipo: str | None = None):
    with get_db_connection() as conn:
        if tipo:
            rows = (
                conn.exec_driver_sql(
                    "SELECT * FROM templates WHERE tipo=%s ORDER BY id", (tipo,)
                )
                .mappings()
                .all()
            )
        else:
            rows = (
                conn.exec_driver_sql(
                    "SELECT * FROM templates ORDER BY id"
                )
                .mappings()
                .all()
            )
        itens = [dict(row) for row in rows]
        for it in itens:
            if it.get("campos_json"):
                try:
                    it["campos"] = json.loads(it["campos_json"])
                except Exception:
                    it["campos"] = []
    return {"templates": itens}


@app.post("/templates")
async def criar_template(request: Request):
    data = await request.json()
    campos = json.dumps(data.get("campos", []))
    with get_db_connection() as conn:
        cur = conn.exec_driver_sql(
            "INSERT INTO templates (tipo, titulo, campos_json) VALUES (%s, %s, %s)",
            (data.get("tipo"), data.get("titulo"), campos),
        )
        conn.commit()
        new_id = cur.lastrowid
    return {"id": new_id}


@app.get("/templates/{template_id}")
async def obter_template(template_id: int):
    with get_db_connection() as conn:
        row = (
            conn.exec_driver_sql(
                "SELECT * FROM templates WHERE id=%s", (template_id,)
            )
            .mappings()
            .fetchone()
        )
        if not row:
            return JSONResponse({"detail": "Template não encontrado"}, status_code=404)
        item = dict(row)
        if item.get("campos_json"):
            try:
                item["campos"] = json.loads(item["campos_json"])
            except Exception:
                item["campos"] = []
        return {"template": item}


@app.put("/templates/{template_id}")
async def atualizar_template(template_id: int, request: Request):
    data = await request.json()
    campos = json.dumps(data.get("campos", []))
    with get_db_connection() as conn:
        conn.exec_driver_sql(
            """UPDATE templates SET titulo=%s, tipo=%s, campos_json=%s WHERE id=%s""",
            (data.get("titulo"), data.get("tipo"), campos, template_id),
        )
        conn.commit()
    return {"ok": True}


@app.delete("/templates/{template_id}")
async def excluir_template(template_id: int):
    with get_db_connection() as conn:
        conn.exec_driver_sql("DELETE FROM templates WHERE id=%s", (template_id,))
        conn.commit()
    return {"ok": True}


@app.post("/contratos/assinar")
async def assinar_contrato(request: Request):
    """Gerar PDF simples com a assinatura enviada."""
    data = await request.json()
    assinatura = data.get("assinatura")
    usuario = data.get("usuario")
    agora = datetime.utcnow().isoformat()
    ip = request.client.host if request.client else ""

    from base64 import b64decode
    from io import BytesIO
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    c.drawString(50, 800, f"Assinado por: {usuario}")
    c.drawString(50, 785, f"Data: {agora} IP: {ip}")

    if assinatura:
        try:
            _, b64 = assinatura.split(",", 1) if "," in assinatura else ("", assinatura)
            img_data = b64decode(b64)
            img = ImageReader(BytesIO(img_data))
            c.drawImage(img, 50, 650, width=200, height=100)
        except Exception:
            pass

    c.showPage()
    c.save()
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/pdf")

