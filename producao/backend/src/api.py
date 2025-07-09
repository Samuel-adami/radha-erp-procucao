from fastapi import FastAPI, File, UploadFile, Request, BackgroundTasks
from fastapi.responses import StreamingResponse
from storage import upload_file, download_stream, delete_file
import xml.etree.ElementTree as ET
import os
import re
from datetime import datetime
from leitor_dxf import aplicar_usinagem_retangular
from gerador_dxf import gerar_dxf_base
from pathlib import Path
import json
from database import (
    get_db_connection,
    init_db,
    exec_ignore,
    insert_with_id,
    PLACEHOLDER,
)
import tempfile
import shutil
from operacoes import (
    parse_xml_orcamento,
    parse_xml_producao,
    parse_dxt_producao,
)
from nesting import gerar_nesting, gerar_nesting_preview
import ezdxf
from typing import Union

init_db()

# Diretório base para arquivos de saída
BASE_DIR = Path(__file__).resolve().parent
SAIDA_DIR = BASE_DIR / "saida"


def resolve_saidadir_path(p: Union[str, Path]) -> Path:
    """Resolve ``p`` ensuring the resulting path is inside ``SAIDA_DIR``.

    This avoids ``Path.is_relative_to`` for compatibility with Python < 3.9.
    """
    resolved = Path(p).resolve()
    try:
        resolved.relative_to(SAIDA_DIR)
    except ValueError:
        raise ValueError("Caminho fora de SAIDA_DIR")
    return resolved


def proximo_oc_numero() -> int:
    """Retorna o próximo número sequencial de OC."""
    with get_db_connection() as conn:
        row = conn.execute(
            "SELECT MAX(oc_numero) as m FROM lotes_ocorrencias"
        ).fetchone()
        try:
            max_val = int(row["m"]) if row["m"] is not None else 0
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

app = FastAPI()


@app.post("/importar-xml")
async def importar_xml(files: list[UploadFile] = File(...)):
    print("🚀 Iniciando importação de arquivos...")
    with tempfile.TemporaryDirectory() as tmpdirname:
        for f in files:
            (Path(tmpdirname) / f.filename).write_bytes(await f.read())

        arquivo_dxt = next((f for f in files if f.filename.lower().endswith((".dxt", ".txt"))), None)
        arquivo_xml = next((f for f in files if f.filename.lower().endswith(".xml")), None)

        if arquivo_dxt:
            print(f"📄 Fluxo DXT de Produção iniciado com '{arquivo_dxt.filename}'.")
            caminho_dxt = Path(tmpdirname) / arquivo_dxt.filename
            try:
                root = ET.fromstring(caminho_dxt.read_text(encoding='utf-8', errors='ignore'))
                return {"pacotes": parse_dxt_producao(root, caminho_dxt)}
            except Exception as e:
                return {"erro": f"Erro crítico no arquivo DXT: {e}"}

        if arquivo_xml:
            print(f"📄 Fluxo XML iniciado com '{arquivo_xml.filename}'.")
            caminho_xml = Path(tmpdirname) / arquivo_xml.filename
            root = ET.fromstring(caminho_xml.read_bytes())
            tipo_xml = "orcamento" if root.find(".//DATA[@ID='nomecliente']") is not None else "producao"
            print(f"    - Tipo de XML detectado: {tipo_xml}")
            return {"pacotes": parse_xml_orcamento(root) if tipo_xml == "orcamento" else parse_xml_producao(root, caminho_xml)}

        return {"erro": "Nenhum arquivo principal (.dxt, .txt, .xml) foi enviado."}


@app.post("/gerar-lote-final")
async def gerar_lote_final(request: Request):
    dados = await request.json()
    numero_lote = dados.get('lote', 'sem_nome')
    pasta_saida = SAIDA_DIR / f"Lote_{numero_lote}"
    os.makedirs(pasta_saida, exist_ok=True)
    try:
        with get_db_connection() as conn:
            sql = f"INSERT INTO lotes (pasta, criado_em) VALUES ({PLACEHOLDER}, {PLACEHOLDER})"
            exec_ignore(conn, sql, (str(pasta_saida), datetime.now().isoformat()))
            conn.commit()
    except Exception:
        pass
    todas = []
    for p in dados.get("pecas", []):
        nome = f"{p['id']}.DXF"
        comprimento = float(p['comprimento'])
        largura = float(p['largura'])
        obs = p.get("observacoes", "")
        cliente = p.get("cliente", "")
        ambiente = p.get("ambiente", "")
        material = p.get("material", "")

        codigo_original = p.get('codigo_peca', '')
        codigo_numerico = re.sub(r'\D', '', codigo_original)

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

        todas.append({
            "Filename": nome,
            "PartName": p['nome'],
            "Length": comprimento,
            "Width": largura,
            "Thickness": 18,
            "Material": material,
            "Client": cliente,
            "Project": ambiente,
            "Program1": codigo_numerico,
            "Comment": obs,
        })

    caminho_dxt_final = pasta_saida / f"Lote_{numero_lote}.dxt"
    with open(caminho_dxt_final, 'w', encoding='utf-8') as f:
        f.write('<?xml version="1.0"?>\n<ListInformation>\n   <ApplicationData>\n')
        f.write('     <Name />\n     <Version>1.0</Version>\n')
        f.write(f'     <Date>{datetime.now().strftime("%d/%m/%Y %H:%M:%S")}</Date>\n')
        f.write('   </ApplicationData>\n   <PartData>\n')
        for p in todas:
            f.write('     <Part>\n')
            for k, v in p.items():
                tipo = 'Text' if isinstance(v, str) else 'Real'
                f.write(f"       <Field><Name>{k}</Name><Type>{tipo}</Type><Value>{v}</Value></Field>\n")
            f.write('     </Part>\n')
        f.write('   </PartData>\n</ListInformation>\n')
    return {"status": "ok", "mensagem": "Arquivos gerados com sucesso."}


@app.get("/carregar-lote-final")
async def carregar_lote_final(pasta: str):
    """Lê o lote final em 'pasta' e retorna os pacotes com suas peças."""
    try:
        pasta_path = resolve_saidadir_path(pasta)
    except ValueError:
        return {"erro": "Caminho inválido"}
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
    pasta_lote = dados.get('pasta_lote')
    largura_chapa = float(dados.get('largura_chapa', 2750))
    altura_chapa = float(dados.get('altura_chapa', 1850))
    ferramentas = dados.get('ferramentas', [])
    config_maquina = dados.get('config_maquina')
    config_layers = dados.get('config_layers')
    if not pasta_lote:
        return {"erro": "Parâmetro 'pasta_lote' não informado."}
    try:
        pasta_lote_resolved = resolve_saidadir_path(pasta_lote)
    except ValueError:
        return {"erro": "Caminho inválido"}
    try:
        chapas = gerar_nesting_preview(
            str(pasta_lote_resolved),
            largura_chapa,
            altura_chapa,
            ferramentas,
            config_layers,
            config_maquina,
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
    config_layers = dados.get("config_layers")
    if not pasta_lote:
        return {"erro": "Parâmetro 'pasta_lote' não informado."}
    try:
        pasta_lote_resolved = resolve_saidadir_path(pasta_lote)
    except ValueError:
        return {"erro": "Caminho inválido"}
    try:
        chapas = gerar_nesting_preview(
            str(pasta_lote_resolved),
            largura_chapa,
            altura_chapa,
            ferramentas,
            config_layers,
            config_maquina,
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
    if not pasta_lote:
        return {"erro": "Parâmetro 'pasta_lote' não informado."}
    try:
        pasta_lote_resolved = resolve_saidadir_path(pasta_lote)
    except ValueError:
        return {"erro": "Caminho inválido"}
    try:
        pasta_resultado = gerar_nesting(
            str(pasta_lote_resolved),
            largura_chapa,
            altura_chapa,
            ferramentas,
            config_layers,
            config_maquina,
        )
    except Exception as e:
        return {"erro": str(e)}
    return {"status": "ok", "pasta_resultado": pasta_resultado}


@app.post("/coletar-layers")
async def api_coletar_layers(request: Request):
    """Retorna os layers encontrados nos DXFs do lote."""
    dados = await request.json()
    pasta_lote = dados.get("pasta_lote")
    if not pasta_lote:
        return {"erro": "Parâmetro 'pasta_lote' não informado."}
    try:
        pasta_lote_resolved = resolve_saidadir_path(pasta_lote)
    except ValueError:
        return {"erro": "Caminho inválido"}
    try:
        layers = coletar_layers(str(pasta_lote_resolved))
    except Exception as e:
        return {"erro": str(e)}
    return {"layers": layers}


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
            rows = conn.exec_driver_sql(
                "SELECT id, pasta FROM lotes ORDER BY id"
            ).fetchall()
            dados = [dict(r) for r in rows]

            registrados = {d["pasta"] for d in dados}

            # Adiciona entradas ausentes para pastas existentes no filesystem
            for pasta_dir in SAIDA_DIR.glob("Lote_*/"):
                if pasta_dir.is_dir() and str(pasta_dir) not in registrados:
                    cur = conn.exec_driver_sql(
                        f"INSERT INTO lotes (pasta, criado_em) VALUES ({PLACEHOLDER}, {PLACEHOLDER})",
                        (str(pasta_dir), datetime.now().isoformat()),
                    )
                    conn.commit()
                    dados.append({"id": cur.lastrowid, "pasta": str(pasta_dir)})

            for d in dados:
                pasta = Path(d["pasta"])
                if pasta.is_dir():
                    lotes_validos.append(str(pasta))
                else:
                    conn.exec_driver_sql(
                        f"DELETE FROM lotes WHERE id={PLACEHOLDER}",
                        (d["id"],),
                    )
            conn.commit()
    except Exception:
        lotes_validos = []

    lotes_validos.sort()
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
            rows = conn.exec_driver_sql(
                "SELECT id, lote, pasta_resultado, criado_em FROM nestings ORDER BY id DESC"
            ).fetchall()
            dados = [dict(r) for r in rows]

            existentes = {d["pasta_resultado"] for d in dados}
            for lote_dir in SAIDA_DIR.glob("Lote_*/"):
                pasta_nest = lote_dir / "nesting"
                if pasta_nest.is_dir() and str(pasta_nest) not in existentes:
                    cur = conn.exec_driver_sql(
                        f"INSERT INTO nestings (lote, pasta_resultado, criado_em) VALUES ({PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER})",
                        (str(lote_dir), str(pasta_nest), datetime.now().isoformat()),
                    )
                    conn.commit()
                    dados.append(
                        {
                            "id": cur.lastrowid,
                            "lote": str(lote_dir),
                            "pasta_resultado": str(pasta_nest),
                            "criado_em": datetime.now().isoformat(),
                        }
                    )
    except Exception:
        pass
    dados.sort(key=lambda d: d.get("id") or 0, reverse=True)
    return {"nestings": dados}


@app.get("/download-lote/{lote}")
async def download_lote(lote: str, background_tasks: BackgroundTasks):
    """Compacta e faz o download do lote especificado."""
    pasta = SAIDA_DIR / f"Lote_{lote}"
    if not pasta.is_dir():
        return {"erro": "Lote não encontrado"}

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    tmp.close()
    base_name = tmp.name[:-4]
    shutil.make_archive(base_name, "zip", pasta)
    zip_path = base_name + ".zip"
    object_name = f"lotes/Lote_{lote}.zip"
    upload_file(zip_path, object_name)
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
            row = conn.exec_driver_sql(
                f"SELECT pasta_resultado FROM nestings WHERE id={PLACEHOLDER}",
                (nid,),
            ).fetchone()
            pasta_str = row["pasta_resultado"] if row else None
    except Exception:
        pasta_str = None

    if not pasta_str:
        return {"erro": "Nesting não encontrado"}

    pasta = Path(pasta_str)
    if not pasta.is_dir():
        return {"erro": "Pasta não encontrada"}

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    tmp.close()
    base_name = tmp.name[:-4]
    shutil.make_archive(base_name, "zip", pasta)
    zip_path = base_name + ".zip"
    filename = f"{pasta.name}.zip"
    object_name = f"nestings/{filename}"
    upload_file(zip_path, object_name)
    background_tasks.add_task(os.remove, zip_path)
    return StreamingResponse(
        download_stream(object_name, zip_path),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.post("/remover-nesting")
async def remover_nesting(request: Request):
    """Exclui uma otimização de nesting e remove seus arquivos."""
    dados = await request.json()
    nid = dados.get("id")
    pasta_resultado = dados.get("pasta_resultado")
    try:
        with get_db_connection() as conn:
            if nid:
                row = conn.exec_driver_sql(
                    f"SELECT pasta_resultado FROM nestings WHERE id={PLACEHOLDER}",
                    (nid,),
                ).fetchone()
                if row:
                    pasta_resultado = pasta_resultado or row["pasta_resultado"]
                conn.exec_driver_sql(
                    f"DELETE FROM nestings WHERE id={PLACEHOLDER}",
                    (nid,),
                )
            elif pasta_resultado:
                conn.exec_driver_sql(
                    f"DELETE FROM nestings WHERE pasta_resultado={PLACEHOLDER}",
                    (pasta_resultado,),
                )
            conn.commit()
    except Exception as e:
        return {"erro": str(e)}
    if pasta_resultado:
        try:
            pasta_resultado_resolved = resolve_saidadir_path(pasta_resultado)
        except ValueError:
            return {"erro": "Caminho inválido"}
        shutil.rmtree(pasta_resultado_resolved, ignore_errors=True)
        delete_file(f"nestings/{pasta_resultado_resolved.name}.zip")
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
    delete_file(f"lotes/Lote_{numero_lote}.zip")
    try:
        with get_db_connection() as conn:
            conn.exec_driver_sql(
                f"DELETE FROM lotes WHERE pasta = {PLACEHOLDER}",
                (str(pasta),),
            )
            conn.commit()
    except Exception:
        pass
    if pasta.is_dir():
        return {"status": "ok", "mensagem": f"Lote {numero_lote} removido"}
    return {"status": "ok", "mensagem": "Lote não encontrado"}


@app.get("/config-maquina")
async def obter_config_maquina():
    """Retorna a configuracao de maquina persistida."""
    try:
        with get_db_connection() as conn:
            row = conn.exec_driver_sql(
                "SELECT dados FROM config_maquina WHERE id=1"
            ).fetchone()
            if row:
                return json.loads(row["dados"])
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


# Novos endpoints para persistir ferramentas, configuracoes de corte e layers


@app.get("/config-ferramentas")
async def obter_ferramentas():
    """Retorna a lista de ferramentas salva."""
    try:
        with get_db_connection() as conn:
            row = conn.exec_driver_sql(
                "SELECT dados FROM config_ferramentas WHERE id=1"
            ).fetchone()
            if row:
                return json.loads(row["dados"])
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
            row = conn.exec_driver_sql(
                "SELECT dados FROM config_cortes WHERE id=1"
            ).fetchone()
            if row:
                return json.loads(row["dados"])
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
            row = conn.exec_driver_sql(
                "SELECT dados FROM config_layers WHERE id=1"
            ).fetchone()
            if row:
                return json.loads(row["dados"])
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
            rows = conn.exec_driver_sql(
                "SELECT id, possui_veio, propriedade, espessura, comprimento, largura FROM chapas"
            ).fetchall()
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
                sql_up = (
                    f"UPDATE chapas SET possui_veio={PLACEHOLDER}, propriedade={PLACEHOLDER}, espessura={PLACEHOLDER}, comprimento={PLACEHOLDER}, largura={PLACEHOLDER} WHERE id={PLACEHOLDER}"
                )
                conn.exec_driver_sql(
                    sql_up,
                    (
                        1 if dados.get("possui_veio") else 0,
                        dados.get("propriedade"),
                        dados.get("espessura"),
                        dados.get("comprimento"),
                        dados.get("largura"),
                        dados["id"],
                    ),
                )
            else:
                sql_ins = (
                    f"INSERT INTO chapas (possui_veio, propriedade, espessura, comprimento, largura)"
                    f" VALUES ({PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER})"
                )
                conn.exec_driver_sql(
                    sql_ins,
                    (
                        1 if dados.get("possui_veio") else 0,
                        dados.get("propriedade"),
                        dados.get("espessura"),
                        dados.get("comprimento"),
                        dados.get("largura"),
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
                f"DELETE FROM chapas WHERE id={PLACEHOLDER}",
                (chapa_id,),
            )
            conn.commit()
    except Exception as e:
        return {"erro": str(e)}
    return {"status": "ok"}


# --------------------- Lotes de Ocorrências ---------------------


@app.get("/lotes-ocorrencias")
async def listar_lotes_ocorrencias():
    """Retorna os lotes de ocorrências cadastrados."""
    try:
        with get_db_connection() as conn:
            rows = conn.execute(
                "SELECT id, lote, pacote, oc_numero, pasta, criado_em FROM lotes_ocorrencias ORDER BY id"
            ).fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        return {"erro": str(e)}


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
        comprimento = float(p['comprimento'])
        largura = float(p['largura'])
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
        todas.append({
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
        })

    caminho_dxt_final = pasta_saida / f"{lote_nome}_OC{numero_oc}.dxt"
    with open(caminho_dxt_final, "w", encoding="utf-8") as f:
        f.write("<?xml version=\"1.0\"?>\n<ListInformation>\n   <ApplicationData>\n")
        f.write("     <Name />\n     <Version>1.0</Version>\n")
        f.write(
            f"     <Date>{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</Date>\n"
        )
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

    try:
        with get_db_connection() as conn:
            sql_lote = f"INSERT INTO lotes (pasta, criado_em) VALUES ({PLACEHOLDER}, {PLACEHOLDER})"
            exec_ignore(conn, sql_lote, (str(pasta_saida), datetime.now().isoformat()))

            sql_oc = (
                f"INSERT INTO lotes_ocorrencias (lote, pacote, oc_numero, pasta, criado_em) "
                f"VALUES ({PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER})"
            )
            oc_id = insert_with_id(
                conn,
                sql_oc,
                (
                    lote,
                    pacote,
                    numero_oc,
                    str(pasta_saida),
                    datetime.now().isoformat(),
                ),
            )
            for p in pecas:
                sql_op = (
                    f"INSERT INTO ocorrencias_pecas (oc_id, peca_id, descricao_peca, motivo_id) "
                    f"VALUES ({PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER})"
                )
                conn.exec_driver_sql(
                    sql_op,
                    (
                        oc_id,
                        p.get('id'),
                        p.get('nome', ''),
                        p.get('motivo_codigo'),
                    ),
                )
            conn.commit()
    except Exception as e:
        return {"erro": str(e)}

    return {"status": "ok", "oc_numero": numero_oc}


@app.delete("/lotes-ocorrencias/{oc_id}")
async def excluir_lote_ocorrencia(oc_id: int):
    """Remove um lote de ocorrência."""
    try:
        with get_db_connection() as conn:
            row = conn.exec_driver_sql(
                f"SELECT pasta FROM lotes_ocorrencias WHERE id={PLACEHOLDER}",
                (oc_id,),
            ).fetchone()
            if row:
                try:
                    pasta = resolve_saidadir_path(row["pasta"])
                except ValueError:
                    return {"erro": "Caminho inválido"}
                if pasta.is_dir():
                    shutil.rmtree(pasta, ignore_errors=True)
                delete_file(f"ocorrencias/{pasta.name}.zip")
                conn.exec_driver_sql(
                    f"DELETE FROM lotes_ocorrencias WHERE id={PLACEHOLDER}",
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
            rows = conn.exec_driver_sql(
                "SELECT codigo, descricao, tipo, setor FROM motivos_ocorrencia ORDER BY codigo"
            ).fetchall()
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
                "INSERT INTO motivos_ocorrencia (codigo, descricao, tipo, setor) "
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
                f"DELETE FROM motivos_ocorrencia WHERE codigo={PLACEHOLDER}",
                (codigo,),
            )
            conn.commit()
    except Exception as e:
        return {"erro": str(e)}
    return {"status": "ok"}


@app.get("/relatorio-ocorrencias")
async def relatorio_ocorrencias(request: Request):
    params = request.query_params
    query = """
        SELECT o.oc_numero, o.lote, o.pacote, o.criado_em,
               p.peca_id, p.descricao_peca,
               m.codigo as motivo_codigo, m.descricao as motivo_descricao, m.tipo, m.setor
        FROM ocorrencias_pecas p
        JOIN lotes_ocorrencias o ON o.id = p.oc_id
        LEFT JOIN motivos_ocorrencia m ON m.codigo = p.motivo_id
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
            rows = conn.exec_driver_sql(query, tuple(params_list)).fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        return {"erro": str(e)}
