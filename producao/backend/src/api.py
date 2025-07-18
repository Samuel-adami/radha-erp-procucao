from fastapi import FastAPI, File, UploadFile, Request, BackgroundTasks
from fastapi.responses import StreamingResponse
from storage import (
    upload_file,
    download_stream,
    delete_file,
    download_file,
    object_exists,
    get_public_url,
)
import logging
import xml.etree.ElementTree as ET
import os
import re
import time
from datetime import datetime
from leitor_dxf import aplicar_usinagem_retangular
from gerador_dxf import gerar_dxf_base
from pathlib import Path
import json
from sqlalchemy import text
from database import (
    get_db_connection,
    init_db,
    exec_ignore,
    insert_with_id,
    PLACEHOLDER,
    schema,
)

SCHEMA_PREFIX = f"{schema}." if schema else ""
import tempfile
import shutil
from operacoes import (
    parse_xml_orcamento,
    parse_xml_producao,
    parse_dxt_producao,
    parse_gabster,
)
from nesting import (
    gerar_nesting,
    gerar_nesting_preview,
    _ler_dxt,
    _encontrar_dxt,
    _sanitize_material_name,
)
import ezdxf
from typing import Union, Dict, List


def _age_seconds(value) -> float | None:
    """Return the age in seconds since ``value`` or ``None`` on failure."""
    if value is None:
        return None
    try:
        dt = (
            datetime.fromisoformat(value)
            if isinstance(value, str)
            else datetime.fromisoformat(str(value))
        )
        now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
        return (now - dt).total_seconds()
    except Exception:
        return None


app = FastAPI()


@app.on_event("startup")
async def _startup() -> None:
    """Initialize database tables on application startup."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    try:
        init_db()
    except Exception as e:  # pragma: no cover - init failures only logged
        logging.error(f"Falha ao inicializar o banco: {e}")
    from storage import storage_config_summary, client

    if client:
        logging.info("Storage configurado: %s", storage_config_summary())
    else:
        logging.warning(
            "Storage NÃO configurado corretamente: %s", storage_config_summary()
        )


# Diretório base para arquivos de saída
BASE_DIR = Path(__file__).resolve().parent
SAIDA_DIR = BASE_DIR / "saida"
# Prefixo utilizado para armazenar arquivos no bucket S3. O valor era obtido
# de variáveis de ambiente, mas agora é definido diretamente para evitar
# problemas quando o .env não é carregado.
OBJECT_PREFIX = "producao/"

# Intervalo em segundos antes de considerar que um lote ausente no bucket
# pode ser removido do banco de dados. Isso evita que lotes recém-criados
# sejam apagados caso a propagação para o armazenamento ainda não tenha
# ocorrido completamente.
LOT_CHECK_GRACE = int(os.getenv("LOT_CHECK_GRACE", "60"))


def ensure_pasta_local(key: str) -> Path:
    """Garantir que ``key`` esteja extraído localmente em ``SAIDA_DIR``.

    Retorna o caminho da pasta extraída.
    """
    key_no_prefix = key[len(OBJECT_PREFIX) :] if key.startswith(OBJECT_PREFIX) else key

    if key_no_prefix.startswith("lotes/"):
        pasta = SAIDA_DIR / Path(key_no_prefix).stem
        extract_to = SAIDA_DIR
    elif key_no_prefix.startswith("nestings/"):
        pasta = SAIDA_DIR / Path(key_no_prefix).stem / "nesting"
        extract_to = pasta.parent
    elif key_no_prefix.startswith("ocorrencias/"):
        pasta = SAIDA_DIR / Path(key_no_prefix).stem
        extract_to = SAIDA_DIR
    else:
        raise ValueError("Chave de objeto invalida")

    if pasta.is_dir():
        return pasta

    status = object_exists(key)
    if status is False:
        logging.error("Objeto %s não encontrado no bucket", key)
        raise FileNotFoundError(f"Objeto {key} nao encontrado")
    if status is None:
        logging.error("Falha ao verificar existência do objeto %s", key)
        raise FileNotFoundError(f"Objeto {key} nao encontrado")
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    tmp.close()
    try:
        download_file(key, tmp.name)
        shutil.unpack_archive(tmp.name, extract_to)
    finally:
        os.remove(tmp.name)
    logging.info("Pasta %s extraída para %s", key, extract_to)

    return pasta


# Helper to check column existence
def _has_column(conn, table: str, column: str) -> bool:
    """Check if a column exists in the specified table for the configured schema."""
    try:
        row = conn.exec_driver_sql(
            "SELECT 1 FROM information_schema.columns WHERE table_schema=%s AND table_name=%s AND column_name=%s",
            (schema, table, column),
        ).fetchone()
        return row is not None
    except Exception:
        return False


def proximo_oc_numero() -> int:
    """Retorna o próximo número sequencial de OC."""
    with get_db_connection() as conn:
        row = (
            conn.execute(
                text(
                    f"SELECT MAX(oc_numero) as m FROM {SCHEMA_PREFIX}lotes_ocorrencias"
                )
            )
            .mappings()
            .fetchone()
        )
        if row is None:
            max_val = 0
        else:
            m_val = row.get("m")
            try:
                max_val = int(m_val) if m_val is not None else 0
            except (ValueError, TypeError):
                max_val = 0
        return max_val + 1


def coletar_layers(pasta_lote: str) -> list[str]:
    """Percorre os arquivos DXF do lote e coleta todos os nomes de layers."""
    pasta = Path(pasta_lote)
    layers: set[str] = set()
    # Busca recursivamente por arquivos DXF na pasta do lote (case-insensitive)
    for arquivo in pasta.rglob("*"):
        if arquivo.is_file() and arquivo.suffix.lower() == ".dxf":
            try:
                doc = ezdxf.readfile(arquivo)
            except Exception:
                continue

            # Inclui também os layers definidos no arquivo, não apenas os utilizados
            for layer in doc.layers:
                nome = layer.dxf.name
                if nome and nome.upper() not in {"CONTORNO", "0", "DEFPOINTS"}:
                    layers.add(nome)

            msp = doc.modelspace()
            for ent in msp:
                nome = ent.dxf.layer
                if nome and nome.upper() not in {"CONTORNO", "0", "DEFPOINTS"}:
                    layers.add(nome)

    return sorted(layers)


def coletar_chapas(pasta_lote: str) -> list[str]:
    """Retorna os materiais das pecas descritos no DXT do lote."""
    pasta = Path(pasta_lote)
    dxt = _encontrar_dxt(pasta)
    if not dxt:
        raise FileNotFoundError("Arquivo DXT não encontrado na pasta do lote")

    pecas = _ler_dxt(dxt)
    materiais: set[str] = set()
    for p in pecas:
        nome = p.get("Material")
        if nome:
            materiais.add(_sanitize_material_name(nome))

    return sorted(materiais)


@app.post("/importar-xml")
async def importar_xml(files: list[UploadFile] = File(...)):
    logging.info("🚀 Iniciando importação de arquivos...")
    with tempfile.TemporaryDirectory() as tmpdirname:
        for f in files:
            (Path(tmpdirname) / f.filename).write_bytes(await f.read())

        arquivo_dxt = next(
            (f for f in files if f.filename.lower().endswith((".dxt", ".txt"))), None
        )
        arquivo_csv = next(
            (f for f in files if f.filename.lower().endswith(".csv")), None
        )
        arquivo_xml = next(
            (f for f in files if f.filename.lower().endswith(".xml")), None
        )

        if arquivo_dxt:
            logging.info(
                f"📄 Fluxo DXT de Produção iniciado com '{arquivo_dxt.filename}'."
            )
            caminho_dxt = Path(tmpdirname) / arquivo_dxt.filename
            try:
                root = ET.fromstring(
                    caminho_dxt.read_text(encoding="utf-8", errors="ignore")
                )
                return {"pacotes": parse_dxt_producao(root, caminho_dxt)}
            except Exception as e:
                return {"erro": f"Erro crítico no arquivo DXT: {e}"}

        if arquivo_csv:
            logging.info(
                f"📄 Fluxo Gabster iniciado com '{arquivo_csv.filename}'."
            )
            caminho_csv = Path(tmpdirname) / arquivo_csv.filename
            try:
                return {"pacotes": parse_gabster(caminho_csv)}
            except Exception as e:
                return {"erro": f"Erro crítico no arquivo CSV: {e}"}

        if arquivo_xml:
            logging.info(f"📄 Fluxo XML iniciado com '{arquivo_xml.filename}'.")
            caminho_xml = Path(tmpdirname) / arquivo_xml.filename
            root = ET.fromstring(caminho_xml.read_bytes())
            tipo_xml = (
                "orcamento"
                if root.find(".//DATA[@ID='nomecliente']") is not None
                else "producao"
            )
            logging.info(f"    - Tipo de XML detectado: {tipo_xml}")
            return {
                "pacotes": (
                    parse_xml_orcamento(root)
                    if tipo_xml == "orcamento"
                    else parse_xml_producao(root, caminho_xml)
                )
            }

        return {"erro": "Nenhum arquivo principal (.dxt, .txt, .xml, .csv) foi enviado."}


@app.post("/gerar-lote-final")
async def gerar_lote_final(request: Request):
    dados = await request.json()
    numero_lote = dados.get("lote", "sem_nome")
    pasta_saida = SAIDA_DIR / f"Lote_{numero_lote}"
    obj_key = f"lotes/{pasta_saida.name}.zip"

    if not schema:
        msg = "DATABASE_SCHEMA nao configurado"
        logging.error(msg)
        return {"erro": msg}

    os.makedirs(pasta_saida, exist_ok=True)
    todas = []
    for p in dados.get("pecas", []):
        nome = f"{p['id']}.DXF"
        comprimento = float(p["comprimento"])
        largura = float(p["largura"])
        obs = p.get("observacoes", "")
        cliente = p.get("cliente", "")
        ambiente = p.get("ambiente", "")
        material = p.get("material", "")

        codigo_original = p.get("codigo_peca", "")
        codigo_numerico = re.sub(r"\D", "", codigo_original)

        caminho_saida = pasta_saida / nome

        raios = {}
        ops_sem_raio = []
        for op in p.get("operacoes", []):
            if op.get("tipo") == "Raio":
                pos = op.get("pos")
                sub = op.get("subPos")
                valor = float(op.get("raio", 0))
                if pos == "L1":
                    if sub == "inferior":
                        raios["bottomLeft"] = valor
                    else:
                        raios["topLeft"] = valor
                elif pos in ("C2", "L3"):
                    if sub == "inferior":
                        raios["bottomRight"] = valor
                    else:
                        raios["topRight"] = valor
                elif pos == "C1":
                    if sub == "T1":
                        raios["bottomLeft"] = valor
                    elif sub == "T2":
                        raios["topLeft"] = valor
                    elif sub == "T3":
                        raios["topRight"] = valor
                    else:
                        raios["bottomRight"] = valor
            else:
                ops_sem_raio.append(op)

        gerar_dxf_base(comprimento, largura, str(caminho_saida), raios)

        for op in ops_sem_raio:
            if op.get("face") in ["Topo (L1)", "Topo (L3)"]:
                continue
            aplicar_usinagem_retangular(str(caminho_saida), str(caminho_saida), op, p)

        todas.append(
            {
                "Filename": nome,
                "PartName": p["nome"],
                "Length": comprimento,
                "Width": largura,
                "Thickness": 18,
                "Material": material,
                "Client": cliente,
                "Project": ambiente,
                "Program1": codigo_numerico,
                "Comment": obs,
            }
        )

    caminho_dxt_final = pasta_saida / f"Lote_{numero_lote}.dxt"
    with open(caminho_dxt_final, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0"?>\n<ListInformation>\n   <ApplicationData>\n')
        f.write("     <Name />\n     <Version>1.0</Version>\n")
        f.write(f'     <Date>{datetime.now().strftime("%d/%m/%Y %H:%M:%S")}</Date>\n')
        f.write("   </ApplicationData>\n   <PartData>\n")
        for p in todas:
            f.write("     <Part>\n")
            for k, v in p.items():
                tipo = "Text" if isinstance(v, str) else "Real"
                f.write(
                    f"       <Field><Name>{k}</Name><Type>{tipo}</Type><Value>{v}</Value></Field>\n"
                )
            f.write("     </Part>\n")
        f.write("   </PartData>\n</ListInformation>\n")

    zip_path = shutil.make_archive(
        str(pasta_saida), "zip", root_dir=pasta_saida.parent, base_dir=pasta_saida.name
    )

    try:
        upload_file(zip_path, obj_key)
        with get_db_connection() as conn:
            sql = (
                f"INSERT INTO {SCHEMA_PREFIX}lotes (obj_key, criado_em) "
                f"VALUES ({PLACEHOLDER}, {PLACEHOLDER}) "
                f"ON CONFLICT (obj_key) DO UPDATE SET criado_em = EXCLUDED.criado_em"
            )
            conn.exec_driver_sql(sql, (obj_key, datetime.now().isoformat()))
            conn.commit()
    except Exception as e:
        logging.error(f"Erro ao salvar lote: {e}")
        return {"erro": f"Erro ao salvar lote: {e}"}
    finally:
        os.remove(zip_path)
        shutil.rmtree(pasta_saida, ignore_errors=True)

        time.sleep(2)

    return {"status": "ok", "mensagem": "Arquivos gerados com sucesso."}


@app.get("/carregar-lote-final")
async def carregar_lote_final(pasta: str):
    """Lê o lote final identificado pela chave de objeto ``pasta``."""

    try:
        pasta_path = ensure_pasta_local(pasta)
    except FileNotFoundError as e:
        return {"erro": str(e)}

    dxt_path = pasta_path / f"{pasta_path.name}.dxt"
    if not dxt_path.exists():
        return {"erro": "DXT nao encontrado"}
    try:
        root = ET.fromstring(dxt_path.read_text(encoding="utf-8", errors="ignore"))
        pacotes = parse_dxt_producao(root, dxt_path)
    except Exception as e:
        return {"erro": str(e)}
    return {"pacotes": pacotes}


@app.post("/executar-nesting")
async def executar_nesting(request: Request):
    dados = await request.json()
    pasta_lote = dados.get("pasta_lote")
    largura_chapa = float(dados.get("largura_chapa", 2750))
    altura_chapa = float(dados.get("altura_chapa", 1850))
    ferramentas = dados.get("ferramentas", [])
    config_maquina = dados.get("config_maquina")
    config_layers = dados.get("config_layers")
    sobras_ids_raw = dados.get("sobras_ids", [])
    try:
        sobras_ids = [int(s) for s in sobras_ids_raw if str(s).strip()]
    except Exception:
        sobras_ids = []
    if not pasta_lote:
        return {"erro": "Parâmetro 'pasta_lote' não informado."}

    try:
        pasta_lote_resolved = ensure_pasta_local(pasta_lote)
    except FileNotFoundError as e:
        return {"erro": str(e)}

    try:
        estoque_sel: Dict[str, List[Dict]] = {}
        if sobras_ids:
            with get_db_connection() as conn:
                rows = (
                    conn.exec_driver_sql(
                        f"SELECT id, chapa_id, descricao, comprimento, largura FROM {SCHEMA_PREFIX}chapas_estoque WHERE id = ANY({PLACEHOLDER})",
                        (sobras_ids,),
                    )
                    .mappings()
                    .all()
                )
                for r in rows:
                    desc = (r.get("descricao") or "").split("(")[0].strip()
                    estoque_sel.setdefault(desc, []).append(dict(r))

        chapas = gerar_nesting_preview(
            str(pasta_lote_resolved),
            largura_chapa,
            altura_chapa,
            ferramentas,
            config_layers,
            config_maquina,
            estoque_sel or None,
        )
        layers = coletar_layers(str(pasta_lote_resolved))
    except Exception as e:
        return {"erro": str(e)}
    return {"status": "ok", "preview": chapas, "layers": layers}


@app.post("/nesting-preview")
async def nesting_preview(request: Request):
    """Retorna a disposição das chapas para visualização."""
    try:
        dados = await request.json()
    except Exception:
        dados = {}
    pasta_lote = dados.get("pasta_lote")
    largura_chapa = float(dados.get("largura_chapa", 2750))
    altura_chapa = float(dados.get("altura_chapa", 1850))
    ferramentas = dados.get("ferramentas", [])
    config_maquina = dados.get("config_maquina")
    sobras_ids_raw = dados.get("sobras_ids", [])
    try:
        sobras_ids = [int(s) for s in sobras_ids_raw if str(s).strip()]
    except Exception:
        sobras_ids = []

    config_layers = dados.get("config_layers")
    if not pasta_lote:
        return {"erro": "Parâmetro 'pasta_lote' não informado."}

    try:
        pasta_lote_resolved = ensure_pasta_local(pasta_lote)
    except FileNotFoundError as e:
        return {"erro": str(e)}

    try:
        estoque_sel: Dict[str, List[Dict]] = {}
        if sobras_ids:
            with get_db_connection() as conn:
                rows = (
                    conn.exec_driver_sql(
                        f"SELECT id, chapa_id, descricao, comprimento, largura FROM {SCHEMA_PREFIX}chapas_estoque WHERE id = ANY({PLACEHOLDER})",
                        (sobras_ids,),
                    )
                    .mappings()
                    .all()
                )
                for r in rows:
                    desc = (r.get("descricao") or "").split("(")[0].strip()
                    estoque_sel.setdefault(desc, []).append(dict(r))

        chapas = gerar_nesting_preview(
            str(pasta_lote_resolved),
            largura_chapa,
            altura_chapa,
            ferramentas,
            config_layers,
            config_maquina,
            estoque_sel or None,
        )
    except Exception as e:
        return {"erro": str(e)}
    return {"chapas": chapas}


@app.post("/executar-nesting-final")
async def executar_nesting_final(request: Request):
    """Executa o nesting definitivo usando os parâmetros informados."""
    try:
        dados = await request.json()
    except Exception:
        dados = {}
    pasta_lote = dados.get("pasta_lote")
    largura_chapa = float(dados.get("largura_chapa", 2750))
    altura_chapa = float(dados.get("altura_chapa", 1850))
    ferramentas = dados.get("ferramentas", [])
    config_maquina = dados.get("config_maquina")
    config_layers = dados.get("config_layers")
    sobras_ids_raw = dados.get("sobras_ids", [])
    try:
        sobras_ids = [int(s) for s in sobras_ids_raw if str(s).strip()]
    except Exception:
        sobras_ids = []
    if not pasta_lote:
        return {"erro": "Parâmetro 'pasta_lote' não informado."}

    try:
        pasta_lote_resolved = ensure_pasta_local(pasta_lote)
    except FileNotFoundError as e:
        return {"erro": str(e)}

    try:
        estoque_sel: Dict[str, List[Dict]] = {}
        if sobras_ids:
            with get_db_connection() as conn:
                rows = (
                    conn.exec_driver_sql(
                        f"SELECT id, chapa_id, descricao, comprimento, largura FROM {SCHEMA_PREFIX}chapas_estoque WHERE id = ANY({PLACEHOLDER})",
                        (sobras_ids,),
                    )
                    .mappings()
                    .all()
                )
                for r in rows:
                    desc = (r.get("descricao") or "").split("(")[0].strip()
                    estoque_sel.setdefault(desc, []).append(dict(r))

        pasta_resultado, sobras = gerar_nesting(
            str(pasta_lote_resolved),
            largura_chapa,
            altura_chapa,
            ferramentas,
            config_layers,
            config_maquina,
            estoque_sel,
        )
    except Exception as e:
        return {"erro": str(e)}
    pasta_resultado_path = Path(pasta_resultado)

    zip_path = shutil.make_archive(
        str(pasta_resultado_path),
        "zip",
        root_dir=pasta_resultado_path.parent,
        base_dir=pasta_resultado_path.name,
    )

    obj_key = f"nestings/Nesting_{pasta_resultado_path.parent.name}.zip"
    upload_file(zip_path, obj_key)
    os.remove(zip_path)
    shutil.rmtree(pasta_resultado_path, ignore_errors=True)
    shutil.rmtree(pasta_lote_resolved, ignore_errors=True)
    try:
        with get_db_connection() as conn:
            origem_lote = Path(pasta_lote).stem

            has_origem = _has_column(conn, "chapas_estoque", "origem")
            has_reservada = _has_column(conn, "chapas_estoque", "reservada")
            has_mov_origem = _has_column(conn, "chapas_estoque_mov", "origem")

            for placa in sobras:
                for s in placa:
                    mat = s.get("Material")
                    comp = float(s.get("Length", 0))
                    larg = float(s.get("Width", 0))
                    row = conn.exec_driver_sql(
                        f"SELECT id, custo_m2 FROM {SCHEMA_PREFIX}chapas WHERE propriedade={PLACEHOLDER} LIMIT 1",
                        (mat,),
                    ).fetchone()
                    chapa_id = row[0] if row else None
                    custo_m2 = float(row[1]) if row and row[1] is not None else 0.0
                    m2 = comp * larg / 1000000.0
                    desc = f"{mat} ({int(comp)} x {int(larg)})"

                    cols = [
                        "chapa_id",
                        "descricao",
                        "comprimento",
                        "largura",
                        "m2",
                        "custo_m2",
                        "custo_total",
                    ]
                    params = [
                        chapa_id,
                        desc,
                        comp,
                        larg,
                        m2,
                        custo_m2,
                        m2 * custo_m2,
                    ]
                    if has_origem:
                        cols.append("origem")
                        params.append(origem_lote)
                    if has_reservada:
                        cols.append("reservada")
                        params.append(0)

                    placeholders = ",".join([PLACEHOLDER] * len(params))
                    sql = f"INSERT INTO {SCHEMA_PREFIX}chapas_estoque ({', '.join(cols)}) VALUES ({placeholders})"
                    conn.exec_driver_sql(sql, tuple(params))

            if sobras_ids:
                sel_cols = [
                    "chapa_id",
                    "descricao",
                    "comprimento",
                    "largura",
                    "m2",
                    "custo_m2",
                    "custo_total",
                ]
                if has_origem:
                    sel_cols.append("origem")

                sel_sql = f"SELECT {', '.join(sel_cols)} FROM {SCHEMA_PREFIX}chapas_estoque WHERE id = ANY({PLACEHOLDER})"
                rows_sel = [
                    dict(r)
                    for r in conn.exec_driver_sql(sel_sql, (sobras_ids,))
                    .mappings()
                    .all()
                ]
                conn.exec_driver_sql(
                    f"DELETE FROM {SCHEMA_PREFIX}chapas_estoque WHERE id = ANY({PLACEHOLDER})",
                    (sobras_ids,),
                )
                for r in rows_sel:
                    mov_cols = [
                        "chapa_id",
                        "descricao",
                        "comprimento",
                        "largura",
                        "m2",
                        "custo_m2",
                        "custo_total",
                    ]
                    mov_params = [
                        r.get("chapa_id"),
                        r.get("descricao"),
                        r.get("comprimento"),
                        r.get("largura"),
                        r.get("m2"),
                        r.get("custo_m2"),
                        r.get("custo_total"),
                    ]
                    if has_mov_origem:
                        mov_cols.append("origem")
                        mov_params.append(r.get("origem"))

                    mov_cols.extend(["destino", "criado_em"])
                    mov_params.extend([origem_lote, datetime.now().isoformat()])

                    mov_placeholders = ",".join([PLACEHOLDER] * len(mov_params))
                    sql = f"INSERT INTO {SCHEMA_PREFIX}chapas_estoque_mov ({', '.join(mov_cols)}) VALUES ({mov_placeholders})"
                    conn.exec_driver_sql(sql, tuple(mov_params))

            conn.commit()
    except Exception as e:
        logging.error("Falha ao registrar sobras: %s", e)
    try:
        with get_db_connection() as conn:
            conn.exec_driver_sql(
                f"INSERT INTO {SCHEMA_PREFIX}nestings (lote, obj_key, criado_em) VALUES ({PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER})",
                (
                    pasta_lote,
                    obj_key,
                    datetime.now().isoformat(),
                ),
            )
            conn.commit()
    except Exception:
        pass
    return {"status": "ok", "pasta_resultado": obj_key}


@app.post("/coletar-layers")
async def api_coletar_layers(request: Request):
    """Retorna os layers encontrados nos DXFs do lote."""
    dados = await request.json()
    pasta_lote = dados.get("pasta_lote")
    if not pasta_lote:
        return {"erro": "Parâmetro 'pasta_lote' não informado."}

    try:
        pasta_lote_resolved = ensure_pasta_local(pasta_lote)
    except FileNotFoundError as e:
        return {"erro": str(e)}

    try:
        layers = coletar_layers(str(pasta_lote_resolved))
    except Exception as e:
        return {"erro": str(e)}
    return {"layers": layers}


@app.post("/coletar-chapas")
async def api_coletar_chapas(request: Request):
    """Retorna a lista de materiais usados no lote informado."""
    dados = await request.json()
    pasta_lote = dados.get("pasta_lote")
    if not pasta_lote:
        return {"erro": "Parâmetro 'pasta_lote' não informado."}

    try:
        pasta_lote_resolved = ensure_pasta_local(pasta_lote)
    except FileNotFoundError as e:
        return {"erro": str(e)}

    try:
        materiais = coletar_chapas(str(pasta_lote_resolved))
    except Exception as e:
        return {"erro": str(e)}
    return {"materiais": materiais}


@app.get("/listar-lotes")
async def listar_lotes():
    """Retorna uma lista das pastas de lote registradas.

    Caso existam pastas ``Lote_*`` em ``SAIDA_DIR`` que ainda não estejam
    cadastradas no banco de dados, elas são inseridas automaticamente. Esse
    comportamento evita que um lote fique invisível nas telas de Nesting e
    Ocorrência quando a gravação inicial falha por algum motivo.
    """

    lotes_validos: list[str] = []
    try:
        with get_db_connection() as conn:
            rows = (
                conn.exec_driver_sql(
                    f"SELECT id, obj_key, criado_em FROM {SCHEMA_PREFIX}lotes ORDER BY id"
                )
                .mappings()
                .all()
            )
            dados = [dict(r) for r in rows]
            logging.info("%d lotes encontrados no banco", len(dados))

            novos: list[str] = []
            logging.info("LISTANDO LOTES:")
            for d in dados:
                key = d["obj_key"]
                logging.info(" - Verificando: %s", key)
                status = object_exists(key)
                if status is True:
                    logging.info("   ✓ Existe no bucket")
                elif status is False:
                    age = _age_seconds(d.get("criado_em"))
                    if age is not None and age < LOT_CHECK_GRACE:
                        logging.info(
                            "   ⚠ Lote recente (%ds), aguardando upload", int(age)
                        )
                    else:
                        logging.info("   ✗ NÃO encontrado no bucket")
                else:
                    logging.info("   ⚠ Erro ao verificar no bucket")
                novos.append(key)

            conn.commit()
            lotes_validos = novos
    except Exception as e:
        logging.error("Erro ao listar lotes: %s", e)
        lotes_validos = []

    lotes_validos.sort()
    logging.info("LOCAIS VÁLIDOS ENCONTRADOS: %s", lotes_validos)
    return {"lotes": lotes_validos}


@app.get("/nestings")
async def listar_nestings():
    """Retorna as otimizações de nesting registradas.

    Se existirem pastas de nesting na estrutura de ``SAIDA_DIR`` que ainda não
    estejam registradas no banco de dados, elas são adicionadas automaticamente.
    """
    dados: list[dict] = []
    try:
        with get_db_connection() as conn:
            rows = (
                conn.exec_driver_sql(
                    f"SELECT id, lote, obj_key, criado_em FROM {SCHEMA_PREFIX}nestings ORDER BY id DESC"
                )
                .mappings()
                .all()
            )
            dados = [dict(r) for r in rows]
            logging.info("%d nestings encontrados no banco", len(dados))

            novos: list[dict] = []
            for d in dados:
                key = d["obj_key"]
                status = object_exists(key)
                if status is True:
                    d["arquivo_url"] = get_public_url(key)
                    novos.append(d)
                elif status is False:
                    age = _age_seconds(d.get("criado_em"))
                    if age is not None and age < LOT_CHECK_GRACE:
                        d["arquivo_url"] = get_public_url(key)
                        novos.append(d)
                    else:
                        conn.exec_driver_sql(
                            f"DELETE FROM {SCHEMA_PREFIX}nestings WHERE id={PLACEHOLDER}",
                            (d["id"],),
                        )
                else:
                    d["arquivo_url"] = get_public_url(key)
                    novos.append(d)
            conn.commit()
            dados = novos
    except Exception as e:
        logging.error("Erro ao listar nestings: %s", e)
        dados = []
    dados.sort(key=lambda d: d.get("id") or 0, reverse=True)
    return {"nestings": dados}


@app.get("/download-lote/{lote}")
async def download_lote(lote: str, background_tasks: BackgroundTasks):
    """Compacta e faz o download do lote especificado."""
    try:
        with get_db_connection() as conn:
            row = (
                conn.exec_driver_sql(
                    f"SELECT obj_key FROM {SCHEMA_PREFIX}lotes WHERE obj_key IN (%s, %s)",
                    (
                        f"{OBJECT_PREFIX}lotes/Lote_{lote}.zip",
                        f"lotes/Lote_{lote}.zip",
                    ),
                )
                .mappings()
                .fetchone()
            )
            object_name = row.get("obj_key") if row else None
    except Exception:
        object_name = None

    pasta = SAIDA_DIR / f"Lote_{lote}"
    if not object_name:
        object_name = f"lotes/Lote_{lote}.zip"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    tmp.close()
    base_name = tmp.name[:-4]
    zip_path = base_name + ".zip"
    if pasta.is_dir():

        shutil.make_archive(
            base_name, "zip", root_dir=pasta.parent, base_dir=pasta.name
        )

        upload_file(zip_path, object_name)
    elif object_exists(object_name) is False:
        os.remove(zip_path)
        return {"erro": "Lote não encontrado"}
    background_tasks.add_task(os.remove, zip_path)
    return StreamingResponse(
        download_stream(object_name, zip_path),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=Lote_{lote}.zip"},
    )


@app.get("/download-nesting/{nid}")
async def download_nesting(nid: int, background_tasks: BackgroundTasks):
    """Compacta e faz o download dos arquivos de uma otimização."""
    try:
        with get_db_connection() as conn:
            row = (
                conn.exec_driver_sql(
                    f"SELECT obj_key FROM {SCHEMA_PREFIX}nestings WHERE id={PLACEHOLDER}",
                    (nid,),
                )
                .mappings()
                .fetchone()
            )
            object_name = row.get("obj_key") if row else None
    except Exception:
        object_name = None

    if not object_name:
        return {"erro": "Nesting não encontrado"}

    status = object_exists(object_name)
    if status is False:
        return {"erro": "Pasta não encontrada"}

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    tmp.close()
    filename = Path(object_name).name
    background_tasks.add_task(os.remove, tmp.name)
    return StreamingResponse(
        download_stream(object_name, tmp.name),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.get("/nesting-layout/{nid}")
async def nesting_layout(nid: int):
    """Retorna o layout gerado para uma otimização existente."""
    try:
        with get_db_connection() as conn:
            row = (
                conn.exec_driver_sql(
                    f"SELECT obj_key FROM {SCHEMA_PREFIX}nestings WHERE id={PLACEHOLDER}",
                    (nid,),
                )
                .mappings()
                .fetchone()
            )
            obj_key = row.get("obj_key") if row else None
    except Exception:
        obj_key = None
    if not obj_key:
        return {"erro": "Nesting não encontrado"}
    try:
        pasta = ensure_pasta_local(obj_key)
    except FileNotFoundError:
        return {"erro": "Pasta não encontrada"}
    layout = pasta / "layout.json"
    if not layout.is_file():
        return {"erro": "Layout não encontrado"}
    try:
        dados = json.loads(layout.read_text(encoding="utf-8"))
    except Exception as e:
        return {"erro": str(e)}
    return {"chapas": dados}


@app.post("/remover-nesting")
async def remover_nesting(request: Request):
    """Exclui uma otimização de nesting e remove seus arquivos."""
    dados = await request.json()
    nid = dados.get("id")
    obj_key = dados.get("obj_key")
    lote_nome = None
    try:
        with get_db_connection() as conn:
            if nid:
                row = (
                    conn.exec_driver_sql(
                        f"SELECT lote, obj_key FROM {SCHEMA_PREFIX}nestings WHERE id={PLACEHOLDER}",
                        (nid,),
                    )
                    .mappings()
                    .fetchone()
                )
                if row:
                    lote_nome = row.get("lote")
                    obj_key = obj_key or row.get("obj_key")
                conn.exec_driver_sql(
                    f"DELETE FROM {SCHEMA_PREFIX}nestings WHERE id={PLACEHOLDER}",
                    (nid,),
                )
            elif obj_key:
                row = (
                    conn.exec_driver_sql(
                        f"SELECT lote FROM {SCHEMA_PREFIX}nestings WHERE obj_key={PLACEHOLDER}",
                        (obj_key,),
                    )
                    .mappings()
                    .fetchone()
                )
                if row:
                    lote_nome = row.get("lote")
                conn.exec_driver_sql(
                    f"DELETE FROM {SCHEMA_PREFIX}nestings WHERE obj_key={PLACEHOLDER}",
                    (obj_key,),
                )
            conn.commit()
    except Exception as e:
        return {"erro": str(e)}
    if obj_key:

        try:
            pasta_local = ensure_pasta_local(obj_key)
        except FileNotFoundError:
            pasta_local = None
        if pasta_local:
            shutil.rmtree(pasta_local, ignore_errors=True)

        delete_file(obj_key)

    if lote_nome:
        try:
            with get_db_connection() as conn:
                conn.exec_driver_sql(
                    f"DELETE FROM {SCHEMA_PREFIX}chapas_estoque WHERE origem={PLACEHOLDER} AND COALESCE(reservada,0)=0",
                    (Path(lote_nome).stem,),
                )
                conn.commit()
        except Exception:
            pass
    return {"status": "ok"}


@app.post("/excluir-lote")
async def excluir_lote(request: Request):
    """Remove a pasta do lote em 'saida'."""
    dados = await request.json()
    numero_lote = dados.get("lote")
    if not numero_lote:
        return {"erro": "Parâmetro 'lote' não informado."}
    pasta = SAIDA_DIR / f"Lote_{numero_lote}"
    if pasta.is_dir():
        shutil.rmtree(pasta, ignore_errors=True)

    key = f"lotes/Lote_{numero_lote}.zip"
    delete_file(key)
    try:
        with get_db_connection() as conn:
            key_pref = f"{OBJECT_PREFIX}{key}"
            conn.exec_driver_sql(
                f"DELETE FROM {SCHEMA_PREFIX}lotes WHERE obj_key IN ({PLACEHOLDER}, {PLACEHOLDER})",
                (key, key_pref),
            )

            conn.commit()
    except Exception:
        pass
    status = object_exists(key)
    if pasta.is_dir() or status is True:
        return {"status": "ok", "mensagem": f"Lote {numero_lote} removido"}
    return {"status": "ok", "mensagem": "Lote não encontrado"}


@app.get("/config-maquina")
async def obter_config_maquina():
    """Retorna a configuracao de maquina persistida."""
    try:
        with get_db_connection() as conn:
            row = (
                conn.exec_driver_sql("SELECT dados FROM config_maquina WHERE id=1")
                .mappings()
                .fetchone()
            )
            if row:
                dados_str = row.get("dados")
                if dados_str is not None:
                    return json.loads(dados_str)
    except Exception as e:
        return {"erro": str(e)}
    return {}


@app.post("/config-maquina")
async def salvar_config_maquina(request: Request):
    """Salva configuracao de maquina no banco de dados."""
    dados = await request.json()
    try:
        with get_db_connection() as conn:
            conn.exec_driver_sql(
                f"INSERT INTO config_maquina (id, dados) VALUES (1, {PLACEHOLDER}) ON CONFLICT(id) DO UPDATE SET dados=excluded.dados",
                (json.dumps(dados, ensure_ascii=False),),
            )
            conn.commit()
    except Exception as e:
        return {"erro": str(e)}
    return {"status": "ok"}


@app.get("/chapas-estoque-mov")
async def listar_chapas_estoque_mov():
    """Lista as movimentacoes de estoque registradas."""
    try:
        with get_db_connection() as conn:
            rows = (
                conn.exec_driver_sql(
                    f"SELECT id, chapa_id, descricao, comprimento, largura, m2, custo_m2, custo_total, origem, destino, criado_em FROM {SCHEMA_PREFIX}chapas_estoque_mov ORDER BY id DESC"
                )
                .mappings()
                .all()
            )
            return [dict(r) for r in rows]
    except Exception as e:
        return {"erro": str(e)}


# Novos endpoints para persistir ferramentas, configuracoes de corte e layers


@app.get("/config-ferramentas")
async def obter_ferramentas():
    """Retorna a lista de ferramentas salva."""
    try:
        with get_db_connection() as conn:
            row = (
                conn.exec_driver_sql("SELECT dados FROM config_ferramentas WHERE id=1")
                .mappings()
                .fetchone()
            )
            if row:
                dados_str = row.get("dados")
                if dados_str is not None:
                    return json.loads(dados_str)
    except Exception as e:
        return {"erro": str(e)}
    return []


@app.post("/config-ferramentas")
async def salvar_ferramentas(request: Request):
    """Salva lista de ferramentas no banco de dados."""
    dados = await request.json()
    try:
        with get_db_connection() as conn:
            conn.exec_driver_sql(
                f"INSERT INTO config_ferramentas (id, dados) VALUES (1, {PLACEHOLDER}) ON CONFLICT(id) DO UPDATE SET dados=excluded.dados",
                (json.dumps(dados, ensure_ascii=False),),
            )
            conn.commit()
    except Exception as e:
        return {"erro": str(e)}
    return {"status": "ok"}


@app.get("/config-cortes")
async def obter_cortes():
    """Retorna as configuracoes de corte salvas."""
    try:
        with get_db_connection() as conn:
            row = (
                conn.exec_driver_sql("SELECT dados FROM config_cortes WHERE id=1")
                .mappings()
                .fetchone()
            )
            if row:
                dados_str = row.get("dados")
                if dados_str is not None:
                    return json.loads(dados_str)
    except Exception as e:
        return {"erro": str(e)}
    return []


@app.post("/config-cortes")
async def salvar_cortes(request: Request):
    """Salva configuracoes de corte no banco de dados."""
    dados = await request.json()
    try:
        with get_db_connection() as conn:
            conn.exec_driver_sql(
                f"INSERT INTO config_cortes (id, dados) VALUES (1, {PLACEHOLDER}) ON CONFLICT(id) DO UPDATE SET dados=excluded.dados",
                (json.dumps(dados, ensure_ascii=False),),
            )
            conn.commit()
    except Exception as e:
        return {"erro": str(e)}
    return {"status": "ok"}


@app.get("/config-layers")
async def obter_layers():
    """Retorna configuracoes de layers salvas."""
    try:
        with get_db_connection() as conn:
            row = (
                conn.exec_driver_sql("SELECT dados FROM config_layers WHERE id=1")
                .mappings()
                .fetchone()
            )
            if row:
                dados_str = row.get("dados")
                if dados_str is not None:
                    return json.loads(dados_str)
    except Exception as e:
        return {"erro": str(e)}
    return []


@app.post("/config-layers")
async def salvar_layers(request: Request):
    """Salva configuracoes de layers no banco de dados."""
    dados = await request.json()
    try:
        with get_db_connection() as conn:
            conn.exec_driver_sql(
                f"INSERT INTO config_layers (id, dados) VALUES (1, {PLACEHOLDER}) ON CONFLICT(id) DO UPDATE SET dados=excluded.dados",
                (json.dumps(dados, ensure_ascii=False),),
            )
            conn.commit()
    except Exception as e:
        return {"erro": str(e)}
    return {"status": "ok"}


@app.get("/chapas")
async def listar_chapas():
    """Retorna todas as chapas cadastradas."""
    try:
        with get_db_connection() as conn:
            rows = (
                conn.exec_driver_sql(
                    f"SELECT id, possui_veio, propriedade, espessura, comprimento, largura, custo_m2 FROM {SCHEMA_PREFIX}chapas"
                )
                .mappings()
                .all()
            )
            return [dict(row) for row in rows]
    except Exception as e:
        return {"erro": str(e)}


@app.post("/chapas")
async def salvar_chapa(request: Request):
    """Cria ou atualiza uma chapa."""
    dados = await request.json()
    try:
        with get_db_connection() as conn:
            if dados.get("id"):
                sql_up = f"UPDATE {SCHEMA_PREFIX}chapas SET possui_veio={PLACEHOLDER}, propriedade={PLACEHOLDER}, espessura={PLACEHOLDER}, comprimento={PLACEHOLDER}, largura={PLACEHOLDER}, custo_m2={PLACEHOLDER} WHERE id={PLACEHOLDER}"
                conn.exec_driver_sql(
                    sql_up,
                    (
                        1 if dados.get("possui_veio") else 0,
                        dados.get("propriedade"),
                        dados.get("espessura"),
                        dados.get("comprimento"),
                        dados.get("largura"),
                        dados.get("custo_m2"),
                        dados["id"],
                    ),
                )
            else:
                sql_ins = (
                    f"INSERT INTO {SCHEMA_PREFIX}chapas (possui_veio, propriedade, espessura, comprimento, largura, custo_m2)"
                    f" VALUES ({PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER})"
                )
                conn.exec_driver_sql(
                    sql_ins,
                    (
                        1 if dados.get("possui_veio") else 0,
                        dados.get("propriedade"),
                        dados.get("espessura"),
                        dados.get("comprimento"),
                        dados.get("largura"),
                        dados.get("custo_m2"),
                    ),
                )
            conn.commit()
    except Exception as e:
        return {"erro": str(e)}
    return {"status": "ok"}


@app.delete("/chapas/{chapa_id}")
async def remover_chapa(chapa_id: int):
    try:
        with get_db_connection() as conn:
            conn.exec_driver_sql(
                f"DELETE FROM {SCHEMA_PREFIX}chapas WHERE id={PLACEHOLDER}",
                (chapa_id,),
            )
            conn.commit()
    except Exception as e:
        return {"erro": str(e)}
    return {"status": "ok"}


@app.get("/chapas-estoque")
async def listar_chapas_estoque(descricao: str | None = None):
    """Lista o estoque de chapas e sobras."""
    try:
        with get_db_connection() as conn:
            sql = (
                "SELECT ce.id, ce.chapa_id, ce.descricao, ce.comprimento, ce.largura, ce.m2, "
                "COALESCE(c.custo_m2, ce.custo_m2) AS custo_m2, "
                "ce.m2 * COALESCE(c.custo_m2, ce.custo_m2) AS custo_total, "
                "ce.origem, ce.reservada "
                f"FROM {SCHEMA_PREFIX}chapas_estoque ce "
                f"LEFT JOIN {SCHEMA_PREFIX}chapas c ON c.id = ce.chapa_id"
            )
            params: tuple = ()
            if descricao:
                sql += " WHERE descricao ILIKE " + PLACEHOLDER
                params = (f"%{descricao}%",)
            try:

                rows = conn.exec_driver_sql(sql, params).mappings().all()
            except Exception as e:
                if "origem" in str(e):
                    conn.rollback()
                    sql = sql.replace(", origem, reservada", "")
                    rows = conn.exec_driver_sql(sql, params).mappings().all()
                    return [dict(r) for r in rows]
                raise
            return [dict(r) for r in rows]

    except Exception as e:
        return {"erro": str(e)}


@app.post("/chapas-estoque")
async def salvar_chapa_estoque(request: Request):
    """Cria ou atualiza um item de estoque."""
    dados = await request.json()
    comp = float(dados.get("comprimento", 0))
    larg = float(dados.get("largura", 0))
    m2 = comp * larg / 1000000.0
    custo_m2 = 0.0
    try:
        with get_db_connection() as conn:
            row = conn.exec_driver_sql(
                f"SELECT custo_m2 FROM {SCHEMA_PREFIX}chapas WHERE id={PLACEHOLDER}",
                (dados.get("chapa_id"),),
            ).fetchone()
            if row and row[0] is not None:
                custo_m2 = float(row[0])
    except Exception:
        custo_m2 = 0.0
    total = m2 * custo_m2
    try:
        with get_db_connection() as conn:
            if dados.get("id"):
                conn.exec_driver_sql(
                    f"UPDATE {SCHEMA_PREFIX}chapas_estoque SET chapa_id={PLACEHOLDER}, descricao={PLACEHOLDER}, comprimento={PLACEHOLDER}, largura={PLACEHOLDER}, m2={PLACEHOLDER}, custo_m2={PLACEHOLDER}, custo_total={PLACEHOLDER}, origem={PLACEHOLDER}, reservada={PLACEHOLDER} WHERE id={PLACEHOLDER}",
                    (
                        dados.get("chapa_id"),
                        dados.get("descricao"),
                        comp,
                        larg,
                        m2,
                        custo_m2,
                        total,
                        dados.get("origem"),
                        int(dados.get("reservada", 0)),
                        dados["id"],
                    ),
                )
            else:
                conn.exec_driver_sql(
                    f"INSERT INTO {SCHEMA_PREFIX}chapas_estoque (chapa_id, descricao, comprimento, largura, m2, custo_m2, custo_total, origem, reservada) VALUES ({PLACEHOLDER},{PLACEHOLDER},{PLACEHOLDER},{PLACEHOLDER},{PLACEHOLDER},{PLACEHOLDER},{PLACEHOLDER},{PLACEHOLDER},{PLACEHOLDER})",
                    (
                        dados.get("chapa_id"),
                        dados.get("descricao"),
                        comp,
                        larg,
                        m2,
                        custo_m2,
                        total,
                        dados.get("origem"),
                        int(dados.get("reservada", 0)),
                    ),
                )
            conn.commit()
    except Exception as e:
        return {"erro": str(e)}
    return {"status": "ok"}


@app.delete("/chapas-estoque/{item_id}")
async def remover_chapa_estoque(item_id: int, request: Request):
    dados = {}
    try:
        dados = await request.json()
    except Exception:
        pass
    destino = dados.get("destino")
    try:
        with get_db_connection() as conn:
            item = (
                conn.exec_driver_sql(
                    f"SELECT chapa_id, descricao, comprimento, largura, m2, custo_m2, custo_total, origem FROM {SCHEMA_PREFIX}chapas_estoque WHERE id={PLACEHOLDER}",
                    (item_id,),
                )
                .mappings()
                .fetchone()
            )
            if item:
                conn.exec_driver_sql(
                    f"INSERT INTO {SCHEMA_PREFIX}chapas_estoque_mov (chapa_id, descricao, comprimento, largura, m2, custo_m2, custo_total, origem, destino, criado_em) VALUES ({PLACEHOLDER},{PLACEHOLDER},{PLACEHOLDER},{PLACEHOLDER},{PLACEHOLDER},{PLACEHOLDER},{PLACEHOLDER},{PLACEHOLDER},{PLACEHOLDER},{PLACEHOLDER})",
                    (
                        item.get("chapa_id"),
                        item.get("descricao"),
                        item.get("comprimento"),
                        item.get("largura"),
                        item.get("m2"),
                        item.get("custo_m2"),
                        item.get("custo_total"),
                        item.get("origem"),
                        destino,
                        datetime.now().isoformat(),
                    ),
                )
            conn.exec_driver_sql(
                f"DELETE FROM {SCHEMA_PREFIX}chapas_estoque WHERE id={PLACEHOLDER}",
                (item_id,),
            )
            conn.commit()
    except Exception as e:
        return {"erro": str(e)}
    return {"status": "ok"}


# --------------------- Lotes de Ocorrências ---------------------


@app.get("/lotes-ocorrencias")
async def listar_lotes_ocorrencias():
    """Retorna os lotes de ocorrências cadastrados."""
    dados: list[dict] = []
    try:
        with get_db_connection() as conn:
            rows = (
                conn.execute(
                    text(
                        f"SELECT id, lote, pacote, oc_numero, obj_key, criado_em FROM {SCHEMA_PREFIX}lotes_ocorrencias ORDER BY id"
                    )
                )
                .mappings()
                .all()
            )
            dados = [dict(row) for row in rows]
            logging.info("%d lotes de ocorrências encontrados", len(dados))

            novos: list[dict] = []
            for d in dados:
                key = d["obj_key"]
                pasta_oc = Path(SAIDA_DIR / Path(key).stem)
                status = object_exists(key) if not pasta_oc.is_dir() else True
                if status is True:
                    d["arquivo_url"] = get_public_url(key)
                    novos.append(d)
                elif status is False:
                    conn.exec_driver_sql(
                        f"DELETE FROM {SCHEMA_PREFIX}lotes_ocorrencias WHERE id={PLACEHOLDER}",
                        (d["id"],),
                    )
                else:
                    d["arquivo_url"] = get_public_url(key)
                    novos.append(d)
            conn.commit()
            dados = novos
    except Exception as e:
        logging.error("Erro ao listar lotes de ocorrências: %s", e)
        return {"erro": str(e)}
    dados.sort(key=lambda d: d.get("id") or 0, reverse=True)
    return {"lotes": dados}


@app.post("/lotes-ocorrencias")
async def gerar_lote_ocorrencia(request: Request):
    """Gera um novo lote de ocorrência a partir das peças selecionadas."""
    dados = await request.json()
    lote = dados.get("lote")
    pacote = dados.get("pacote")
    pecas = dados.get("pecas", [])

    for p in pecas:
        if not p.get("motivo_codigo"):
            return {
                "erro": f"Insira o motivo na peça {p.get('id')} - {p.get('nome', '')}"
            }

    numero_oc = proximo_oc_numero()
    lote_nome = str(lote)
    if not lote_nome.startswith("Lote_"):
        lote_nome = f"Lote_{lote_nome}"
    pasta_saida = SAIDA_DIR / f"{lote_nome}_OC{numero_oc}"
    os.makedirs(pasta_saida, exist_ok=True)

    todas = []
    for p in pecas:
        nome = f"{p['id']}.DXF"
        comprimento = float(p["comprimento"])
        largura = float(p["largura"])
        obs = p.get("observacoes", "")
        cliente = p.get("cliente", "")
        ambiente = p.get("ambiente", "")
        material = p.get("material", "")

        codigo_original = p.get("codigo_peca", "")
        codigo_numerico = re.sub(r"\D", "", codigo_original)

        caminho_saida = pasta_saida / nome
        raios = {}
        ops_sem_raio = []
        for op in p.get("operacoes", []):
            if op.get("tipo") == "Raio":
                pos = op.get("pos")
                sub = op.get("subPos")
                valor = float(op.get("raio", 0))
                if pos == "L1":
                    if sub == "inferior":
                        raios["bottomLeft"] = valor
                    else:
                        raios["topLeft"] = valor
                elif pos in ("C2", "L3"):
                    if sub == "inferior":
                        raios["bottomRight"] = valor
                    else:
                        raios["topRight"] = valor
                elif pos == "C1":
                    if sub == "T1":
                        raios["bottomLeft"] = valor
                    elif sub == "T2":
                        raios["topLeft"] = valor
                    elif sub == "T3":
                        raios["topRight"] = valor
                    else:
                        raios["bottomRight"] = valor
            else:
                ops_sem_raio.append(op)

        gerar_dxf_base(comprimento, largura, str(caminho_saida), raios)
        for op in ops_sem_raio:
            if op.get("face") in ["Topo (L1)", "Topo (L3)"]:
                continue
            aplicar_usinagem_retangular(str(caminho_saida), str(caminho_saida), op, p)
        todas.append(
            {
                "Filename": nome,
                "PartName": p.get("nome", ""),
                "Length": comprimento,
                "Width": largura,
                "Thickness": 18,
                "Material": material,
                "Client": cliente,
                "Project": ambiente,
                "Program1": codigo_numerico,
                "Comment": obs,
            }
        )

    caminho_dxt_final = pasta_saida / f"{lote_nome}_OC{numero_oc}.dxt"
    with open(caminho_dxt_final, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0"?>\n<ListInformation>\n   <ApplicationData>\n')
        f.write("     <Name />\n     <Version>1.0</Version>\n")
        f.write(f"     <Date>{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</Date>\n")
        f.write("   </ApplicationData>\n   <PartData>\n")
        for p in todas:
            f.write("     <Part>\n")
            for k, v in p.items():
                tipo = "Text" if isinstance(v, str) else "Real"
                f.write(
                    f"       <Field><Name>{k}</Name><Type>{tipo}</Type><Value>{v}</Value></Field>\n"
                )
            f.write("     </Part>\n")
        f.write("   </PartData>\n</ListInformation>\n")

    key_lote = f"lotes/{pasta_saida.name}.zip"
    key_oc = f"ocorrencias/{pasta_saida.name}.zip"
    try:
        with get_db_connection() as conn:
            sql_lote = f"INSERT INTO {SCHEMA_PREFIX}lotes (obj_key, criado_em) VALUES ({PLACEHOLDER}, {PLACEHOLDER})"
            exec_ignore(conn, sql_lote, (key_lote, datetime.now().isoformat()))

            sql_oc = (
                f"INSERT INTO {SCHEMA_PREFIX}lotes_ocorrencias (lote, pacote, oc_numero, obj_key, criado_em) "
                f"VALUES ({PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER})"
            )
            oc_id = insert_with_id(
                conn,
                sql_oc,
                (
                    lote,
                    pacote,
                    numero_oc,
                    key_oc,
                    datetime.now().isoformat(),
                ),
            )
            for p in pecas:
                sql_op = (
                    f"INSERT INTO {SCHEMA_PREFIX}ocorrencias_pecas (oc_id, peca_id, descricao_peca, motivo_id) "
                    f"VALUES ({PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER})"
                )
                conn.exec_driver_sql(
                    sql_op,
                    (
                        oc_id,
                        p.get("id"),
                        p.get("nome", ""),
                        p.get("motivo_codigo"),
                    ),
                )
            conn.commit()
    except Exception as e:
        return {"erro": str(e)}

    zip_path = shutil.make_archive(
        str(pasta_saida), "zip", root_dir=pasta_saida.parent, base_dir=pasta_saida.name
    )

    upload_file(zip_path, key_oc)
    os.remove(zip_path)
    shutil.rmtree(pasta_saida, ignore_errors=True)
    return {"status": "ok", "oc_numero": numero_oc}


@app.delete("/lotes-ocorrencias/{oc_id}")
async def excluir_lote_ocorrencia(oc_id: int):
    """Remove um lote de ocorrência."""
    try:
        with get_db_connection() as conn:
            row = (
                conn.exec_driver_sql(
                    f"SELECT obj_key FROM {SCHEMA_PREFIX}lotes_ocorrencias WHERE id={PLACEHOLDER}",
                    (oc_id,),
                )
                .mappings()
                .fetchone()
            )
            if row:
                key = row.get("obj_key")

                try:
                    pasta = ensure_pasta_local(key)
                except FileNotFoundError:
                    pasta = None
                if pasta and pasta.is_dir():

                    shutil.rmtree(pasta, ignore_errors=True)
                delete_file(key)
                conn.exec_driver_sql(
                    f"DELETE FROM {SCHEMA_PREFIX}lotes_ocorrencias WHERE id={PLACEHOLDER}",
                    (oc_id,),
                )
                conn.commit()
                return {"status": "ok"}
    except Exception as e:
        return {"erro": str(e)}
    return {"status": "ok", "mensagem": "Lote não encontrado"}


@app.get("/motivos-ocorrencias")
async def listar_motivos():
    try:
        with get_db_connection() as conn:
            rows = (
                conn.exec_driver_sql(
                    f"SELECT codigo, descricao, tipo, setor FROM {SCHEMA_PREFIX}motivos_ocorrencia ORDER BY codigo"
                )
                .mappings()
                .all()
            )
            return [dict(row) for row in rows]
    except Exception as e:
        return {"erro": str(e)}


@app.post("/motivos-ocorrencias")
async def salvar_motivo(request: Request):
    dados = await request.json()
    codigo = dados.get("codigo")
    if not codigo:
        return {"erro": "codigo obrigatorio"}
    descricao = dados.get("descricao", "")
    tipo = dados.get("tipo", "")
    setor = dados.get("setor", "")
    try:
        with get_db_connection() as conn:
            sql = (
                f"INSERT INTO {SCHEMA_PREFIX}motivos_ocorrencia (codigo, descricao, tipo, setor) "
                f"VALUES ({PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}) ON CONFLICT(codigo) DO UPDATE SET descricao=excluded.descricao, tipo=excluded.tipo, setor=excluded.setor"
            )
            conn.exec_driver_sql(
                sql,
                (codigo, descricao, tipo, setor),
            )
            conn.commit()
    except Exception as e:
        return {"erro": str(e)}
    return {"status": "ok"}


@app.delete("/motivos-ocorrencias/{codigo}")
async def deletar_motivo(codigo: str):
    try:
        with get_db_connection() as conn:
            conn.exec_driver_sql(
                f"DELETE FROM {SCHEMA_PREFIX}motivos_ocorrencia WHERE codigo={PLACEHOLDER}",
                (codigo,),
            )
            conn.commit()
    except Exception as e:
        return {"erro": str(e)}
    return {"status": "ok"}


@app.get("/relatorio-ocorrencias")
async def relatorio_ocorrencias(request: Request):
    params = request.query_params
    query = f"""
        SELECT o.oc_numero, o.lote, o.pacote, o.criado_em,
               p.peca_id, p.descricao_peca,
               m.codigo as motivo_codigo, m.descricao as motivo_descricao, m.tipo, m.setor
        FROM {SCHEMA_PREFIX}ocorrencias_pecas p
        JOIN {SCHEMA_PREFIX}lotes_ocorrencias o ON o.id = p.oc_id
        LEFT JOIN {SCHEMA_PREFIX}motivos_ocorrencia m ON m.codigo = p.motivo_id
        WHERE 1=1
    """
    params_list = []
    if params.get("data_inicio"):
        query += f" AND o.criado_em >= {PLACEHOLDER}"
        params_list.append(params.get("data_inicio"))
    if params.get("data_fim"):
        query += f" AND o.criado_em <= {PLACEHOLDER}"
        params_list.append(params.get("data_fim"))
    if params.get("motivo"):
        query += f" AND m.codigo = {PLACEHOLDER}"
        params_list.append(params.get("motivo"))
    if params.get("tipo"):
        query += f" AND m.tipo = {PLACEHOLDER}"
        params_list.append(params.get("tipo"))
    if params.get("setor"):
        query += f" AND m.setor = {PLACEHOLDER}"
        params_list.append(params.get("setor"))
    query += " ORDER BY o.oc_numero, p.peca_id"
    try:
        with get_db_connection() as conn:
            rows = conn.exec_driver_sql(query, tuple(params_list)).mappings().all()
            return [dict(row) for row in rows]
    except Exception as e:
        return {"erro": str(e)}
