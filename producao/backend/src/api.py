from fastapi import FastAPI, File, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
import xml.etree.ElementTree as ET
import os
import re
from datetime import datetime
from leitor_dxf import aplicar_usinagem_retangular
from gerador_dxf import gerar_dxf_base
import json
from pathlib import Path
import tempfile 
from operacoes import processar_dxf_producao

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

materiais = {
    ("18", "700"): "Branco TX 18mm",
    ("18", "999"): "Nogal Terracota 18mm",
}

def classificar_item(item):
    desc = item.get("DESCRIPTION", "").lower()
    ref = item.get("REFERENCE", "")
    supplier = item.get("SUPPLIER", "")
    family = item.get("FAMILY", "").lower()
    tipo = item.get("TYPE", "").lower()
    largura = float(item.get("WIDTH", 0))
    comprimento = float(item.get("DEPTH", 0))
    espessura = float(item.get("HEIGHT", 0))
    if item.get("COMPONENT") != "Y" or item.get("STRUCTURE") != "N": return "outro"
    if family in ["acessórios", "roteiro produtivo", "ferragem", "ferragens"]: return "outro"
    if ref and not supplier and largura > 0 and comprimento > 0 and espessura > 0: return "mdf"
    if "fita" in desc or item.get("PRODUCTTYPE") == "EdgeBanding": return "fita"
    if tipo == "accessory" or "parafuso" in desc or "dobradiça" in desc or supplier: return "ferragem"
    return "outro"       

def inferir_operacoes_por_nome(nome, largura, comprimento):
    operacoes, nome_lower, espessura = [], nome.lower(), comprimento
    if "lateral direita" in nome_lower:
        operacoes = [
            {"tipo": "Furo", "x": 10, "y": 27, "diametro": 8, "profundidade": 12.5},
            {"tipo": "Furo", "x": 9.5, "y": largura - 80, "diametro": 8, "profundidade": 12.5},
            {"tipo": "Furo", "x": comprimento - 9, "y": 95, "diametro": 8, "profundidade": 12.5},
            {"tipo": "Furo", "x": comprimento - 9, "y": largura - 69, "diametro": 8, "profundidade": 12.5},
            {"tipo": "Retângulo", "x": 0, "y": 0, "comprimento": comprimento, "largura": 6.5, "profundidade": 6.5, "estrategia": "Por Dentro"}
        ]
    elif "lateral esquerda" in nome_lower:
        operacoes = [
            {"tipo": "Furo", "x": 9, "y": 95, "diametro": 8, "profundidade": 12.5},
            {"tipo": "Furo", "x": 9, "y": largura - 69, "diametro": 8, "profundidade": 12.5},
            {"tipo": "Furo", "x": comprimento - 10, "y": 27, "diametro": 8, "profundidade": 12.5},
            {"tipo": "Furo", "x": comprimento - 9.5, "y": largura - 80, "diametro": 8, "profundidade": 12.5},
            {"tipo": "Retângulo", "x": 0, "y": 0, "comprimento": comprimento, "largura": 6.5, "profundidade": 6.5, "estrategia": "Por Dentro"}
        ]
    elif "porta" in nome_lower:
        operacoes = [
            {"tipo": "Furo", "x": 90, "y": 22, "diametro": 35, "profundidade": 11.5},
            {"tipo": "Furo", "x": comprimento - 90, "y": 22, "diametro": 35, "profundidade": 11.5},
            {"tipo": "Furo", "x": 64, "y": 27.5, "diametro": 3, "profundidade": 1},
            {"tipo": "Furo", "x": comprimento - 64, "y": 27.5, "diametro": 3, "profundidade": 1},
            {"tipo": "Furo", "x": 116, "y": 27.5, "diametro": 3, "profundidade": 1},
            {"tipo": "Furo", "x": comprimento - 116, "y": 27.5, "diametro": 3, "profundidade": 1}
        ]
    elif any(tag in nome_lower for tag in ["base inferior", "base superior", "divisória"]):
        y_positions = [37, largura / 2, largura - 37]
        operacoes = [
            {"tipo": "Retângulo", "x": 0, "y": 0, "comprimento": comprimento, "largura": 6.5, "profundidade": 6.5, "estrategia": "Por Dentro"},
            # NOMES DAS FACES ATUALIZADOS AQUI
            *[{"tipo": "Furo", "x": 9, "y": y, "diametro": 8, "profundidade": 24, "face": "Topo (L1)"} for y in y_positions],
            *[{"tipo": "Furo", "x": espessura - 9.5, "y": y, "diametro": 8, "profundidade": 24, "face": "Topo (L3)"} for y in y_positions]
        ]
    return operacoes

def parse_bpp_furos_topo(file_path, peca_largura):
    face1_holes_raw = []
    try:
        with open(file_path, 'r', encoding='latin-1') as f: content = f.read()
    except Exception as e:
        print(f"  -> Erro ao ler arquivo BPP {file_path.name}: {e}")
        return []

    program_section = re.search(r'\[PROGRAM\](.*)', content, re.DOTALL)
    if not program_section: return []

    for line in program_section.group(1).strip().split('\n'):
        line = line.strip()
        if not line.startswith('@ BH'): continue
        try:
            parts = [p.strip() for p in line.split(',')]
            side_param = parts[5].replace('"', '')
            face_parts = side_param.split(':')
            if len(face_parts) < 2: continue
            
            face = face_parts[1].strip()
            if face == '1':
                face1_holes_raw.append({
                    "x_bpp": float(parts[7]), "y_bpp": float(parts[8]),
                    "profundidade": float(parts[10]), "diametro": float(parts[11])
                })
        except (IndexError, ValueError):
            continue
    
    operacoes_finais = []
    for hole in face1_holes_raw:
        y_rel, x_rel = hole['x_bpp'], hole['y_bpp']
        y_final = peca_largura - y_rel

        # NOMES DAS FACES ATUALIZADOS AQUI
        operacoes_finais.append({
            "tipo": "Furo", "x": round(x_rel, 2), "y": round(y_final, 2),
            "profundidade": hole['profundidade'], "diametro": hole['diametro'], "face": "Topo (L1)"
        })
        operacoes_finais.append({
            "tipo": "Furo", "x": round(x_rel, 2), "y": round(y_final, 2),
            "profundidade": hole['profundidade'], "diametro": hole['diametro'], "face": "Topo (L3)"
        })
            
    return operacoes_finais

def parse_dxt_producao(root, dxt_path):
    print("🚀 Início do parse_dxt_producao")
    all_parts_data = []
    for part_node in root.findall(".//Part"):
        fields = {field.find('Name').text: field.find('Value').text for field in part_node.findall("Field") if field.find('Name') is not None and field.find('Name').text is not None}
        if fields: all_parts_data.append(fields)

    if not all_parts_data: return []

    primeira_peca_info = all_parts_data[0]
    nome_do_cliente = primeira_peca_info.get("Client", "Cliente não encontrado")
    nome_do_projeto = primeira_peca_info.get("Project", "Projeto não encontrado")
    titulo_pacote = f"{nome_do_cliente} - {nome_do_projeto}"
    pecas_importadas = []
    pasta_base_dxf = dxt_path.parent
    print(f"📦 Itens <Part> encontrados no DXT: {len(all_parts_data)}")

    for item_data in all_parts_data:
        try:
            descricao_item = item_data.get("PartName", "Sem Nome").strip().upper()
            dxf_da_peca = item_data.get("Filename")
            if not dxf_da_peca: continue
            caminho_dxf = pasta_base_dxf / dxf_da_peca
            if not caminho_dxf.exists(): continue

            print(f"  -> Processando: {descricao_item} | DXF: {dxf_da_peca}")
            comprimento, largura, espessura = float(item_data.get("Length", 0)), float(item_data.get("Width", 0)), float(item_data.get("Thickness", 0))
            
            operacoes_dxf = processar_dxf_producao(caminho_dxf, {'comprimento': comprimento, 'largura': largura})
            
            operacoes_bpp = []
            caminho_bpp = caminho_dxf.with_suffix('.bpp')
            if caminho_bpp.exists():
                print(f"     -> Arquivo BPP encontrado: {caminho_bpp.name}.")
                operacoes_bpp = parse_bpp_furos_topo(caminho_bpp, largura)
                if operacoes_bpp: print(f"        -> {len(operacoes_bpp)} furos de topo (faces 1 e 3) criados simetricamente.")

            pecas_importadas.append({
                "nome": descricao_item, "codigo_peca": Path(dxf_da_peca).stem,
                "comprimento": comprimento, "largura": largura, "espessura": espessura,
                "material": item_data.get("Material", "Desconhecido"), "cliente": nome_do_cliente,
                "ambiente": nome_do_projeto, "observacoes": item_data.get("Comment", ""),
                "orientacao": "horizontal" if comprimento > largura else "vertical",
                "operacoes": operacoes_dxf + operacoes_bpp
            })
        except Exception as e:
            print(f"⚠️ Erro inesperado ao processar '{item_data.get('PartName', '')}': {e}.")
    
    if not pecas_importadas: return []
    print(f"✅ Sucesso! Peças importadas: {len(pecas_importadas)}")
    return [{"titulo": titulo_pacote, "pecas": pecas_importadas}]

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
            except Exception as e: return {"erro": f"Erro crítico no arquivo DXT: {e}"}

        if arquivo_xml:
            print(f"📄 Fluxo XML iniciado com '{arquivo_xml.filename}'.")
            caminho_xml = Path(tmpdirname) / arquivo_xml.filename
            root = ET.fromstring(caminho_xml.read_bytes())
            tipo_xml = "orcamento" if root.find(".//DATA[@ID='nomecliente']") is not None else "producao"
            print(f"   - Tipo de XML detectado: {tipo_xml}")
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
        f.write(f'<?xml version="1.0"?>\n<ListInformation>\n  <ApplicationData>\n    <Name />\n    <Version>1.0</Version>\n    <Date>{datetime.now().strftime("%d/%m/%Y %H:%M:%S")}</Date>\n  </ApplicationData>\n  <PartData>\n')
        for p in todas:
            f.write('    <Part>\n')
            for k, v in p.items(): f.write(f"      <Field><Name>{k}</Name><Type>{'Text' if isinstance(v, str) else 'Real'}</Type><Value>{v}</Value></Field>\n")
            f.write('    </Part>\n')
        f.write('  </PartData>\n</ListInformation>\n')
    return {"status": "ok", "mensagem": "Arquivos gerados com sucesso."}

def parse_xml_orcamento(root):
    pacotes, cliente_node = [], root.find(".//DATA[@ID='nomecliente']")
    nome_cliente = cliente_node.attrib.get("VALUE", "") if cliente_node is not None else "SemCliente"
    ambiente_node = root.find(".//AMBIENT")
    nome_ambiente = ambiente_node.attrib.get("DESCRIPTION", "") if ambiente_node is not None else "SemDescricao"
    titulo, pecas = f"{nome_cliente} - {nome_ambiente}", []
    for item in root.findall(".//ITEM"):
        nome, nome_item = item.attrib.get("DESCRICAO", "").lower(), item.attrib.get("DESCRIPTION", "").upper()
        if any(p in nome for p in ["fita", "dobradiça", "parafuso", "puxador", "suporte", "batente"]) or classificar_item(item.attrib) != "mdf": continue
        try:
            largura, comprimento = float(item.attrib.get("DEPTH", "0")), float(item.attrib.get("WIDTH", "0"))
            if ("PORTA" in nome or "FRENTE DE" in nome) and "BASCULANTE" not in nome:
                largura, comprimento = float(item.attrib.get("HEIGHT", "0")), float(item.attrib.get("WIDTH", "0"))
        except ValueError: continue
        ref_parts = item.attrib.get("REFERENCE", "").split(".")
        espessura = ref_parts[2] if len(ref_parts) > 2 else "?"
        cor = ref_parts[-1] if len(ref_parts) > 4 else "?"
        peca = {"nome": nome_item, "largura": largura, "comprimento": comprimento, "espessura": espessura, "material": materiais.get((espessura, cor), f"Desconhecido ({espessura}/{cor})"), "cliente": nome_cliente, "ambiente": nome_ambiente, "observacoes": item.attrib.get("OBSERVATIONS", ""), "orientacao": "horizontal" if comprimento > largura else "vertical"}
        peca["operacoes"] = inferir_operacoes_por_nome(peca["nome"], largura, comprimento)
        pecas.append(peca)
    if pecas: pacotes.append({"titulo": titulo, "pecas": pecas})
    return pacotes

def parse_xml_producao(root, xml_path):
    print("🚀 Início do parse_xml_producao")
    pacotes, pecas = [], []
    try:
        nome_cliente = root.find(".//CLIENTE_LOJA").attrib["NOME"]
    except:
        nome_cliente = "SemCliente"
    project_node = root.find(".//UNIQUE_ID[@PROJECTNAME]")
    nome_ambiente = project_node.attrib.get("PROJECTNAME", "SemProjeto") if project_node is not None else "SemProjeto"
    titulo, pasta_base = f"{nome_cliente} - Projeto - {nome_ambiente}", Path(os.path.abspath(xml_path)).parent
    itens = root.findall(".//ITEM")
    print(f"📦 Total de itens encontrados no XML: {len(itens)}")
    for item in itens:
        try:
            desenho_id = item.attrib.get("DESENHO")
            if not desenho_id:
                continue
            filename, caminho_dxf = f"{desenho_id}.dxf", pasta_base / f"{desenho_id}.dxf"
            if not caminho_dxf.exists():
                continue
            descricao = item.attrib.get("DESCRICAO", "").strip().upper()
            print(f"-> Peça válida encontrada: '{descricao}'. Processando...")
            
            comprimento_xml, largura_xml, espessura = float(item.attrib.get("LARGURA", "0")), float(item.attrib.get("PROFUNDIDADE", "0")), float(item.attrib.get("ALTURA", "0"))
            
            operacoes_dxf = processar_dxf_producao(caminho_dxf, {'comprimento': comprimento_xml, 'largura': largura_xml})
            
            operacoes_bpp = []
            caminho_bpp = caminho_dxf.with_suffix('.bpp')
            if caminho_bpp.exists():
                print(f"     -> Arquivo BPP encontrado: {caminho_bpp.name}.")
                operacoes_bpp = parse_bpp_furos_topo(caminho_bpp, largura_xml)
                if operacoes_bpp:
                    print(f"        -> {len(operacoes_bpp)} furos de topo (faces 1 e 3) criados simetricamente.")

            material_node = item.find(".//COLUNA[@CODIGO='Material']")
            material = material_node.attrib.get("RESPOSTA", "Desconhecido") if material_node is not None else "Desconhecido"
            
            pecas.append({
                "nome": descricao, "codigo_peca": Path(filename).stem, 
                "largura": largura_xml, "comprimento": comprimento_xml, "espessura": espessura, 
                "material": material, 
                "cliente": nome_cliente, "ambiente": nome_ambiente, "observacoes": "", 
                "orientacao": "horizontal" if comprimento_xml > largura_xml else "vertical", 
                "operacoes": operacoes_dxf + operacoes_bpp
            })
        except Exception as e:
            print(f"⚠️ Erro crítico ao processar um item: {str(e)}")
            
    if pecas:
        print(f"📦 Total de peças válidas importadas: {len(pecas)}")
        pacotes.append({"titulo": titulo, "pecas": pecas})
    print("✅ Finalizado parse_xml_producao")
    return pacotes