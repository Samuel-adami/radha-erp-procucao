from fastapi import FastAPI, Request, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from database import get_db_connection, init_db, insert_with_id
from orcamento_promob import parse_promob_xml
from gabster_api import (
    list_orcamentos_cliente,
    list_orcamento_cliente_item,
    get_projeto,
    get_acabamento,
    get_componente,
    get_produto,
    BASE_URL,
    _auth_header
)
from orcamento_gabster import parse_gabster_projeto
from storage import (
    upload_file,
    delete_file,
    get_public_url,
    object_exists,
    download_stream,
)
from datetime import datetime
import logging
import re
import json
import requests
import base64
import tempfile
import os

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


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
    """Retrieve budget item information from Gabster API."""
    params = await request.json()
    usuario = params.get("usuario")
    chave = params.get("chave")
    offset = int(params.get("offset") or 0)
    limit = int(params.get("limit") or 20)

    try:
        itens = list_orcamento_cliente_item(
            offset=offset, limit=limit, user=usuario, api_key=chave
        )
    except requests.exceptions.HTTPError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:  # generic errors
        raise HTTPException(status_code=400, detail=str(exc))

    return itens


@app.post("/gabster-projeto")
async def gabster_projeto(request: Request):
    """Return header + enriched items from Gabster APIs for a Projeto."""
    params = await request.json()
    codigo = params.get("codigo")
    usuario = os.getenv("GABSTER_API_USER")
    chave = os.getenv("GABSTER_API_KEY")
    if not all([codigo, usuario, chave]):
        raise HTTPException(status_code=400, detail="Campos obrigatórios: codigo, e variáveis de ambiente GABSTER_API_USER e GABSTER_API_KEY.")

    try:
        # 1) Cabeçalho do projeto
        raw = get_projeto(int(codigo), user=usuario, api_key=chave)
        header = {
            "id": raw.get("id"),
            "nome": raw.get("nome"),
            "cd_cliente": raw.get("cd_cliente"),
            "nome_arquivo_skp": raw.get("nome_arquivo_skp"),
            "identificador_arquivo_skp": raw.get("identificador_arquivo_skp"),
            "descricao": raw.get("descricao"),
            "observacao": raw.get("observacao"),
            "ambiente": raw.get("ambiente"),
            "projeto_ref": raw.get("projeto_ref"),
        }

        # ✅ INSERE O PROJETO ANTES DE QUALQUER OUTRA IMPORTAÇÃO
        with get_db_connection() as conn:
            conn.exec_driver_sql(
                """
                INSERT INTO gabster_projeto_itens (
                    id, nome, cd_cliente, nome_arquivo_skp,
                    identificador_arquivo_skp, descricao, observacao,
                    ambiente, projeto_ref
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    nome = EXCLUDED.nome,
                    cd_cliente = EXCLUDED.cd_cliente,
                    nome_arquivo_skp = EXCLUDED.nome_arquivo_skp,
                    identificador_arquivo_skp = EXCLUDED.identificador_arquivo_skp,
                    descricao = EXCLUDED.descricao,
                    observacao = EXCLUDED.observacao,
                    ambiente = EXCLUDED.ambiente,
                    projeto_ref = EXCLUDED.projeto_ref
                """,
                (
                    header["id"],
                    header["nome"],
                    header["cd_cliente"],
                    header["nome_arquivo_skp"],
                    header["identificador_arquivo_skp"],
                    header["descricao"],
                    header["observacao"],
                    header["ambiente"],
                    header["projeto_ref"]
                )
            )
            conn.commit()

        # segue normalmente com a importação de orçamentos...

    
        # 2) Importa budgets via Gabster filtrando por cd_projeto (id do projeto)
        raw_orc = list_orcamentos_cliente(
            cd_projeto=header["id"], offset=0, limit=20, user=usuario, api_key=chave
        )
        # Extrai a lista de orçamentos do JSON retornado
        logging.info(
            "raw_orc keys for projeto %s: %s",
            header["id"], list(raw_orc.keys())
        )
        budgets = (
            raw_orc.get("objects")
            or raw_orc.get("results")
            or raw_orc.get("items")
            or raw_orc.get("data")
            or []
        )
        logging.info(
            "Orçamentos retornados para projeto %s: %d registros",
            header["id"], len(budgets)
        )
        # persiste budgets e itens na tabela gabster_orcamento_cliente e gabster_orcamento_itens
        try:
            with get_db_connection() as conn:
                # limpa orçamentos antigos e prepara para itens de cada budget
                conn.exec_driver_sql(
                    "DELETE FROM gabster_orcamento_cliente WHERE cd_projeto=%s",
                    (header["id"],),
                )
                for b in budgets:
                    # insere orçamento e limpa itens antigos deste orçamento
                    conn.exec_driver_sql(
                        "DELETE FROM gabster_orcamento_itens WHERE cd_orcamento_cliente=%s",
                        (b.get("id"),),
                    )
                    conn.exec_driver_sql(
                        """
                        INSERT INTO gabster_orcamento_cliente (
                            id, cd_projeto, valor_desconto, valor_frete,
                            valor_adicional, valor, nome_arquivo_skp,
                            identificador_arquivo_skp, descricao, observacao
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            b.get("id"), header["id"], b.get("valor_desconto"),
                            b.get("valor_frete"), b.get("valor_adicional"), b.get("valor"),
                            b.get("nome_arquivo_skp"), b.get("identificador_arquivo_skp"),
                            b.get("descricao"), b.get("observacao"),
                        ),
                    )
                    # busca itens do orçamento via API /orcamento_cliente_item
                    # busca itens do orçamento diretamente construindo URL para cd_orcamento_cliente
                    orc_url = (
                        f"{BASE_URL}orcamento_cliente_item/"
                        f"?cd_orcamento_cliente={b.get('id')}"
                        f"&offset=0&limit=100&format=json"
                    )
                    logging.info("GET ORCAMENTO_CLIENTE_ITEM direct: %s", orc_url)
                    raw_items = requests.get(
                        orc_url, headers=_auth_header(usuario, chave), timeout=15
                    ).json()
                    if isinstance(raw_items, dict):
                        logging.info(
                            "raw_items keys for orçamento %s: %s",
                            b.get("id"), list(raw_items.keys()),
                        )
                    items_list = (
                        raw_items.get("objects")
                        or raw_items.get("results")
                        or raw_items.get("data")
                        or raw_items.get("items")
                        or []
                    )
                    logging.info(
                        "Itens retornados para orçamento %s: %d registros",
                        b.get("id"), len(items_list)
                    )
                    if items_list:
                        logging.info(
                            "Chaves do primeiro item de orçamento %s: %s",
                            b.get("id"), list(items_list[0].keys())
                        )
                    # filtra e insere itens do orçamento
                    inserted = 0
                    for it in items_list:
                        # aceita string/int na comparação do projeto do orçamento
                        if str(it.get("cd_orcamento_cliente")) != str(b.get("id")):
                            logging.info(
                                "Ignorado item de orçamento %s: cd_orcamento_cliente %s != projeto %s",
                                it.get("id"), it.get("cd_orcamento_cliente"), b.get("id"),
                            )
                            continue
                        conn.exec_driver_sql(
                            """
                            INSERT INTO gabster_orcamento_itens (
                                id, cd_orcamento_cliente, cd_produto, quantidade,
                                cd_acabamento, comprimento, largura_profundidade,
                                espessura_altura, referencia, codigo_montagem,
                                cd_componente, valor, guid
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """,
                            (
                                safe_int(it.get("id")),
                                safe_int(b.get("id")),
                                safe_int(it.get("cd_produto")),
                                safe_int(it.get("quantidade")),
                                safe_int(it.get("cd_acabamento")),
                                safe_int(it.get("comprimento") or ""),
                                safe_int(it.get("largura_profundidade") or ""),
                                safe_int(it.get("espessura_altura") or ""),
                                str(it.get("referencia") or ""),
                                safe_int(it.get("codigo_montagem")),
                                safe_int(it.get("cd_componente")),
                                safe_float(it.get("valor")),
                                str(it.get("guid") or ""),
                            ),
                        )
                        inserted += 1
                    logging.info(
                        "Inseridos %d itens em gabster_orcamento_itens para orçamento %s",
                        inserted, b.get("id")
                    )
                conn.commit()
        except Exception:
            logging.exception(
                "Erro ao gravar orçamentos + itens para projeto %s",
                header["id"],
            )

        # 3) Sincroniza todos os itens de orçamentos na plataforma Gabster
        # Chama paginadamente o endpoint /orcamento_cliente_item/?offset=&limit=&format=json
        offset = 0
        limit = 100
        while True:
            page = list_orcamento_cliente_item(
                offset=offset, limit=limit, user=usuario, api_key=chave
            )
            items_page = (
                page.get("objects")
                or page.get("results")
                or page.get("data")
                or page.get("items")
                or []
            )
            if not items_page:
                break
            with get_db_connection() as conn:
                for item in items_page:
                    conn.exec_driver_sql(
                        """
                        INSERT INTO gabster_orcamento_itens (
                            id, cd_orcamento_cliente, cd_produto, quantidade,
                            cd_acabamento, comprimento, largura_profundidade,
                            espessura_altura, referencia, codigo_montagem,
                            cd_componente, valor, guid
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING
                        """,
                        (
                            safe_int(item.get("id")),
                            safe_int(item.get("cd_orcamento_cliente")),
                            safe_int(item.get("cd_produto")),
                            safe_int(item.get("quantidade")),
                            safe_int(item.get("cd_acabamento")),
                            safe_int(item.get("comprimento")),
                            safe_int(item.get("largura_profundidade")),
                            safe_int(item.get("espessura_altura")),                           
                            str(item.get("referencia") or ""),
                            safe_int(item.get("codigo_montagem")),
                            safe_int(item.get("cd_componente")),
                            safe_float(item.get("valor")),
                            str(item.get("guid") or ""),
                        ),
                    )
                conn.commit()
            offset += limit

        # 3) Itens do orçamento do projeto atual para compor o Projeto 3D
        with get_db_connection() as conn:
            res = conn.exec_driver_sql(
                "SELECT * FROM gabster_orcamento_itens WHERE cd_orcamento_cliente IN (SELECT id FROM gabster_orcamento_cliente WHERE cd_projeto = %s)",
                (header["id"],)
            )
            itens_brutos = [dict(r._mapping) for r in res.fetchall()]

        # Deduplica códigos para buscar metadados externos
        cds_acab = {it["cd_acabamento"] for it in itens_brutos if it.get("cd_acabamento")}
        cds_comp = {it["cd_componente"] for it in itens_brutos if it.get("cd_componente")}
        cds_prod = {it["cd_produto"] for it in itens_brutos if it.get("cd_produto")}

        acabamentos = {c: get_acabamento(c, user=usuario, api_key=chave) for c in cds_acab}
        componentes = {c: get_componente(c, user=usuario, api_key=chave) for c in cds_comp}
        produtos = {c: get_produto(c, user=usuario, api_key=chave) for c in cds_prod}

        # 4) Monta lista enriquecida
        enriched = []
        for it in itens_brutos:
            enriched.append({
                "id": it.get("id"),
                "quantidade": it.get("quantidade"),
                "referencia": it.get("referencia"),
                "valor": it.get("valor"),
                "comprimento": it.get("comprimento"),
                "largura_profundidade": it.get("largura_profundidade"),
                "espessura_altura": it.get("espessura_altura"),
                "acabamento": {
                    "cd": it.get("cd_acabamento"),
                    "nome": acabamentos.get(it.get("cd_acabamento"), {}).get("nome")
                },
                "componente": {
                    "cd": it.get("cd_componente"),
                    "nome": componentes.get(it.get("cd_componente"), {}).get("nome")
                },
                "produto": {
                    "cd": it.get("cd_produto"),
                    "nome": produtos.get(it.get("cd_produto"), {}).get("nome")
                }
            })

    except requests.exceptions.HTTPError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    # estrutura de saída compatível com front-end Projeto 3D
    ambiente = header.get("ambiente") or "Projeto"
    # soma o valor total dos itens para facilitar fluxo de negociação
    total = sum(item.get("valor", 0) for item in enriched)
    return {"projetos": {ambiente: {**header, "itens": enriched, "total": total}}}


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
        rt_percent = safe_float(data.get("rt_percent"))

        entrega = data.get("entrega_diferente")
        entrega = 1 if str(entrega).lower() in ("sim", "1", "true") else 0

        arquivos_input = data.get("arquivos", [])
        arquivos_keys: list[str] = []
        for arq in arquivos_input:
            if isinstance(arq, dict) and arq.get("nome") and arq.get("conteudo"):
                nome = arq["nome"]
                conteudo = arq["conteudo"]
                _, b64 = conteudo.split(",", 1) if "," in conteudo else ("", conteudo)
                tmp = tempfile.NamedTemporaryFile(delete=False)
                tmp.write(base64.b64decode(b64))
                tmp.close()
                key = f"atendimentos/{codigo}/{nome}"
                try:
                    upload_file(tmp.name, key)
                    arquivos_keys.append(key)
                finally:
                    os.remove(tmp.name)
            elif isinstance(arq, str):
                arquivos_keys.append(arq)

        fields = (
            data.get("cliente"),
            codigo,
            data.get("projetos"),
            data.get("previsao_fechamento"),
            data.get("temperatura"),
            int(data.get("tem_especificador") or 0),
            data.get("especificador_nome"),
            rt_percent,
            entrega,
            data.get("historico"),
            json.dumps(arquivos_keys),
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
        atendimento_id = insert_with_id(
            conn,
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
    """Return atendimento details including its tarefas."""
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
                keys = json.loads(item["arquivos_json"])
                arquivos = []
                for k in keys:
                    if object_exists(k) is not False:
                        arquivos.append({"obj_key": k, "url": get_public_url(k)})
                item["arquivos"] = arquivos
            except Exception:
                item["arquivos"] = []

        # carregar tarefas deste atendimento
        tarefas_rows = (
            conn.exec_driver_sql(
                "SELECT id, nome, concluida, dados, data_execucao FROM atendimento_tarefas WHERE atendimento_id=%s ORDER BY id",
                (atendimento_id,),
            )
            .mappings()
            .all()
        )

        tarefas = []
        for row in tarefas_rows:
            t = dict(row)
            dados_json = {}
            if t.get("dados"):
                try:
                    dados_json = json.loads(t["dados"])
                except Exception:
                    dados_json = {}

            itens_rows = (
                conn.exec_driver_sql(
                    "SELECT ambiente, descricao, unitario, quantidade, total FROM projeto_itens WHERE tarefa_id=%s ORDER BY id",
                    (t["id"],),
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
                dados_json["projetos"] = projetos
                t["dados"] = json.dumps(dados_json)
            tarefas.append(t)

        item["tarefas"] = tarefas

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
            val = data[campo]
            if campo == "entrega_diferente":
                val = 1 if str(val).lower() in ("sim", "1", "true") else 0
            campos.append(f"{campo}=%s")
            valores.append(val)
    if not campos:
        return {"detail": "Nada para atualizar"}
    valores.append(atendimento_id)
    with get_db_connection() as conn:
        conn.exec_driver_sql(
            f"UPDATE atendimentos SET {', '.join(campos)} WHERE id=%s",
            tuple(valores),
        )
        conn.commit()
        logging.info("Dados do projeto gravados com sucesso")
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
            tuple(valores),
        )
        if "dados" in data and dados_json.get("projetos"):

            conn.exec_driver_sql("DELETE FROM projeto_itens WHERE tarefa_id=%s", (tarefa_id,))
            for amb, info in dados_json["projetos"].items():
                for it in info.get("itens", []):
                    # insere itens de projeto (Promob ou Gabster), ajustando chaves para valores
                    desc = it.get("descricao") or it.get("referencia")
                    unit = safe_float(
                        it.get("unitario")
                        if it.get("unitario") is not None
                        else it.get("valor")
                    )
                    quant = safe_int(it.get("quantidade"))
                    tot = safe_float(
                        it.get("total") if it.get("total") is not None else it.get("valor")
                    )
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
                            desc,
                            unit,
                            quant,
                            tot,
                        ),
                    )
                # grava cabeçalho do projeto Gabster usando id da plataforma (upsert)
                if dados_json.get("programa") == "Gabster":
                    params = (
                        info.get("id"), info.get("nome"), info.get("cd_cliente"),
                        info.get("nome_arquivo_skp"), info.get("identificador_arquivo_skp"),
                        info.get("descricao"), info.get("observacao"), info.get("ambiente"),
                        info.get("projeto_ref"),
                    )
                    logging.info("Upsert gabster_projeto_itens header: %s", params)
                    conn.exec_driver_sql(
                        """
                        INSERT INTO gabster_projeto_itens (
                            id, nome, cd_cliente, nome_arquivo_skp,
                            identificador_arquivo_skp, descricao, observacao,
                            ambiente, projeto_ref
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO UPDATE SET
                          nome = EXCLUDED.nome,
                          cd_cliente = EXCLUDED.cd_cliente,
                          nome_arquivo_skp = EXCLUDED.nome_arquivo_skp,
                          identificador_arquivo_skp = EXCLUDED.identificador_arquivo_skp,
                          descricao = EXCLUDED.descricao,
                          observacao = EXCLUDED.observacao,
                          ambiente = EXCLUDED.ambiente,
                          projeto_ref = EXCLUDED.projeto_ref
                        """,
                        params,
                    )
        conn.commit()
        logging.info("Dados do projeto gravados com sucesso")
    return {"ok": True}


@app.delete("/atendimentos/{atendimento_id}")
async def excluir_atendimento(atendimento_id: int):
    with get_db_connection() as conn:
        row = (
            conn.exec_driver_sql(
                "SELECT arquivos_json FROM atendimentos WHERE id=%s",
                (atendimento_id,),
            )
            .mappings()
            .fetchone()
        )
        if row and row.get("arquivos_json"):
            try:
                for key in json.loads(row["arquivos_json"]):
                    delete_file(key)
            except Exception:
                pass

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
        new_id = insert_with_id(
            conn,
            """INSERT INTO condicoes_pagamento (
                nome, numero_parcelas, juros_parcela,
                dias_vencimento, ativa, parcelas_json
            ) VALUES (%s, %s, %s, %s, %s, %s)""",
            fields,
        )
        conn.commit()
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
        new_id = insert_with_id(
            conn,
            "INSERT INTO templates (tipo, titulo, campos_json, arquivo_key) VALUES (%s, %s, %s, %s)",
            (data.get("tipo"), data.get("titulo"), campos, data.get("arquivo_key")),
        )
        conn.commit()
    return {"id": new_id}


@app.post("/templates/upload")
async def upload_template(tipo: str, titulo: str, file: UploadFile = File(...)):
    """Importar arquivo DOCX ou PDF para um novo template."""
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in {".docx", ".pdf"}:
        raise HTTPException(status_code=400, detail="Apenas .docx ou .pdf")

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
    try:
        contents = await file.read()
        tmp.write(contents)
        tmp.close()
        key = f"templates/{tipo}/{titulo}_{int(datetime.utcnow().timestamp())}{ext}"
        upload_file(tmp.name, key)
    finally:
        os.remove(tmp.name)

    with get_db_connection() as conn:
        new_id = insert_with_id(
            conn,
            "INSERT INTO templates (tipo, titulo, campos_json, arquivo_key) VALUES (%s, %s, %s, %s)",
            (tipo, titulo, json.dumps([]), key),
        )
        conn.commit()


    return {"id": new_id, "arquivo_key": key, "arquivo_url": get_public_url(key)}


@app.post("/templates/{template_id}/upload")
async def upload_template_file(template_id: int, file: UploadFile = File(...)):
    """Anexar ou substituir o arquivo de um template existente."""
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in {".docx", ".pdf"}:
        raise HTTPException(status_code=400, detail="Apenas .docx ou .pdf")

    with get_db_connection() as conn:
        row = (
            conn.exec_driver_sql(
                "SELECT tipo, titulo FROM templates WHERE id=%s", (template_id,),
            )
            .mappings()
            .fetchone()
        )
    if not row:
        return JSONResponse({"detail": "Template não encontrado"}, status_code=404)

    key = f"templates/{row['tipo']}/{row['titulo']}_{int(datetime.utcnow().timestamp())}{ext}"

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
    try:
        tmp.write(await file.read())
        tmp.close()
        upload_file(tmp.name, key)
    finally:
        os.remove(tmp.name)

    with get_db_connection() as conn:
        conn.exec_driver_sql(
            "UPDATE templates SET arquivo_key=%s WHERE id=%s",
            (key, template_id),
        )
        conn.commit()

    return {"arquivo_key": key, "arquivo_url": get_public_url(key)}



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
        if item.get("arquivo_key"):
            item["arquivo_url"] = get_public_url(item["arquivo_key"])
        return {"template": item}


@app.post("/templates/{template_id}/gerar")
async def gerar_documento(template_id: int, request: Request):
    """Gerar documento substituindo tokens [campo]"""
    data = await request.json()
    valores: dict = data.get("valores", {})

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

    tpl = dict(row)
    key = tpl.get("arquivo_key")
    if not key:
        raise HTTPException(status_code=400, detail="Template sem arquivo")

    stream = download_stream(key, key)
    ext = os.path.splitext(key)[1].lower()
    from io import BytesIO

    if ext == ".docx":
        from docx import Document

        doc = Document(stream)
        for p in doc.paragraphs:
            for placeholder, value in valores.items():
                token = f"[{placeholder}]"
                if token in p.text:
                    for run in p.runs:
                        if token in run.text:
                            run.text = run.text.replace(token, str(value))

        output = BytesIO()
        doc.save(output)
        output.seek(0)
        media = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        return StreamingResponse(output, media_type=media)

    elif ext == ".pdf":
        content = stream.read()
        try:
            txt = content.decode("latin-1")
            for placeholder, value in valores.items():
                txt = txt.replace(f"[{placeholder}]", str(value))
            output = BytesIO(txt.encode("latin-1"))
            return StreamingResponse(output, media_type="application/pdf")
        except Exception:
            raise HTTPException(status_code=400, detail="Falha ao gerar PDF")

    else:
        raise HTTPException(status_code=400, detail="Formato não suportado")


@app.put("/templates/{template_id}")
async def atualizar_template(template_id: int, request: Request):
    data = await request.json()
    campos = json.dumps(data.get("campos", []))
    with get_db_connection() as conn:
        conn.exec_driver_sql(
            """UPDATE templates SET titulo=%s, tipo=%s, campos_json=%s, arquivo_key=%s WHERE id=%s""",
            (data.get("titulo"), data.get("tipo"), campos, data.get("arquivo_key"), template_id),
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
