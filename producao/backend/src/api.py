from fastapi import FastAPI, File, UploadFile, Request
# Removido: from fastapi.middleware.cors import CORSMiddleware
import xml.etree.ElementTree as ET
import os
import re
from datetime import datetime
from leitor_dxf import aplicar_usinagem_retangular
from gerador_dxf import gerar_dxf_base, gerar_dxt_final # gerar_dxt_final também é usada
import json
from pathlib import Path
import tempfile 
# Importações ajustadas de operacoes.py:
from operacoes import processar_dxf_producao, parse_bpp_furos_topo, parse_xml_orcamento, parse_xml_producao, parse_dxt_producao # parse_dxt_producao também é importada

app = FastAPI()

# Removido: Configuração de CORS, pois será gerenciada pelo Gateway API
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# Removido: materiais (agora em operacoes.py, se necessário)
# Removido: classificar_item (agora em operacoes.py, se necessário)
# Removido: inferir_operacoes_por_nome (agora em operacoes.py)

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
                # parse_dxt_producao está sendo importada de operacoes, então não precisamos assumir que está aqui
                return {"pacotes": parse_dxt_producao(root, caminho_dxt)}
            except Exception as e: return {"erro": f"Erro crítico no arquivo DXT: {e}"}

        if arquivo_xml:
            print(f"📄 Fluxo XML iniciado com '{arquivo_xml.filename}'.")
            caminho_xml = Path(tmpdirname) / arquivo_xml.filename
            root = ET.fromstring(caminho_xml.read_bytes())
            # Usando as funções importadas de operacoes.py
            tipo_xml = "orcamento" if root.find(".//DATA[@ID='nomecliente']") is not None else "producao"
            print(f"    - Tipo de XML detectado: {tipo_xml}")
            return {"pacotes": parse_xml_orcamento(root) if tipo_xml == "orcamento" else parse_xml_producao(root, caminho_xml)}

        return {"erro": "Nenhum arquivo principal (.dxt, .txt, .xml) foi enviado."}
        
@app.post("/gerar-lote-final")
async def gerar_lote_final(request: Request):
    dados = await request.json()
    numero_lote, pasta_saida = dados.get('lote', 'sem_nome'), os.path.join('saida', f"Lote_{dados.get('lote', 'sem_nome')}")
    os.makedirs(pasta_saida, exist_ok=True)
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
            # FILTRO COM NOMES DE FACES ATUALIZADOS
            if op.get("face") in ["Topo (L1)", "Topo (L3)"]:
                continue
            aplicar_usinagem_retangular(caminho_saida, caminho_saida, op, p)
        
        todas.append({
            "Filename": nome, "PartName": p['nome'], "Length": comprimento, "Width": largura, 
            "Thickness": 18, "Material": material, "Client": cliente, "Project": ambiente, 
            "Program1": codigo_numerico,  
            "Comment": obs
        })

    caminho_dxt_final = os.path.join(pasta_saida, f"Lote_{numero_lote}.dxt")
    with open(caminho_dxt_final, 'w', encoding='utf-8') as f:
        f.write(f'<?xml version="1.0"?>\n<ListInformation>\n   <ApplicationData>\n     <Name />\n     <Version>1.0</Version>\n     <Date>{datetime.now().strftime("%d/%m/%Y %H:%M:%S")}</Date>\n   </ApplicationData>\n   <PartData>\n')
        for p in todas:
            f.write('     <Part>\n')
            for k, v in p.items(): f.write(f"       <Field><Name>{k}</Name><Type>{'Text' if isinstance(v, str) else 'Real'}</Type><Value>{v}</Value></Field>\n")
            f.write('     </Part>\n')
        f.write('   </PartData>\n</ListInformation>\n')
    return {"status": "ok", "mensagem": "Arquivos gerados com sucesso."}