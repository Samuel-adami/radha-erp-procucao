from fastapi import FastAPI, File, UploadFile, Request
import xml.etree.ElementTree as ET
import os
import re
from datetime import datetime
from leitor_dxf import aplicar_usinagem_retangular
from gerador_dxf import gerar_dxf_base
from pathlib import Path
import json
from database import get_db_connection, init_db
import tempfile
import shutil
from operacoes import (
    parse_xml_orcamento,
    parse_xml_producao,
    parse_dxt_producao,
)
from nesting import gerar_nesting
import ezdxf

init_db()

def coletar_layers(pasta_lote: str) -> list[str]:
    """Percorre os arquivos DXF do lote e coleta os nomes de layers."""
    pasta = Path(pasta_lote)
    layers: set[str] = set()
    for arquivo in pasta.glob('*.dxf'):
        try:
            doc = ezdxf.readfile(arquivo)
        except Exception:
            continue
        msp = doc.modelspace()
        for ent in msp:
            nome = ent.dxf.layer
            if nome and nome.upper() != 'CONTORNO':
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
    pasta_saida = os.path.join('saida', f"Lote_{numero_lote}")
    os.makedirs(pasta_saida, exist_ok=True)
    try:
        with get_db_connection() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO lotes (pasta, criado_em) VALUES (?, ?)",
                (pasta_saida, datetime.now().isoformat()),
            )
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

        caminho_saida = os.path.join(pasta_saida, nome)
        gerar_dxf_base(comprimento, largura, caminho_saida)

        for op in p.get("operacoes", []):
            if op.get("face") in ["Topo (L1)", "Topo (L3)"]:
                continue
            aplicar_usinagem_retangular(caminho_saida, caminho_saida, op, p)

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

    caminho_dxt_final = os.path.join(pasta_saida, f"Lote_{numero_lote}.dxt")
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
        pasta_resultado = gerar_nesting(
            pasta_lote,
            largura_chapa,
            altura_chapa,
            ferramentas,
            config_layers,
            config_maquina,
        )
        layers = coletar_layers(pasta_lote)
    except Exception as e:
        return {"erro": str(e)}
    return {"status": "ok", "pasta_resultado": pasta_resultado, "layers": layers}


@app.get("/listar-lotes")
async def listar_lotes():
    """Retorna uma lista das pastas de lote registradas."""
    try:
        with get_db_connection() as conn:
            rows = conn.execute(
                "SELECT pasta FROM lotes ORDER BY id"
            ).fetchall()
            lotes = [row["pasta"] for row in rows]
    except Exception:
        lotes = []
    return {"lotes": lotes}


@app.post("/excluir-lote")
async def excluir_lote(request: Request):
    """Remove a pasta do lote em 'saida'."""
    dados = await request.json()
    numero_lote = dados.get("lote")
    if not numero_lote:
        return {"erro": "Parâmetro 'lote' não informado."}
    pasta = Path("saida") / f"Lote_{numero_lote}"
    if pasta.is_dir():
        shutil.rmtree(pasta, ignore_errors=True)
    try:
        with get_db_connection() as conn:
            conn.execute("DELETE FROM lotes WHERE pasta = ?", (str(pasta),))
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
            row = conn.execute(
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
            conn.execute(
                "INSERT INTO config_maquina (id, dados) VALUES (1, ?) "
                "ON CONFLICT(id) DO UPDATE SET dados=excluded.dados",
                (json.dumps(dados, ensure_ascii=False),),
            )
            conn.commit()
    except Exception as e:
        return {"erro": str(e)}
    return {"status": "ok"}
