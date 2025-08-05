import csv
import re
import io
import ezdxf
from ezdxf.math import BoundingBox
from datetime import datetime
import os
from pathlib import Path


def parse_float(value, default=0.0):
    """Converte valores numéricos tratando vírgula e ponto."""
    try:
        return float(str(value).replace(',', '.'))
    except (ValueError, TypeError):
        return default

def normalize_material_name(material):
    """Remove casas decimais da espessura no nome do material."""
    if not isinstance(material, str):
        return material
    return re.sub(r'(\d+)[.,]\d+(?=\s*mm)', r'\1', material, flags=re.IGNORECASE)

def fix_dxf_content(file_path):
    encodings_to_try = ['cp1252', 'latin-1', 'utf-8']
    for enc in encodings_to_try:
        try:
            with open(file_path, 'r', encoding=enc) as f:
                content = f.read()
            return content.replace(',', '.')
        except (UnicodeDecodeError, Exception):
            continue
    print(f"ERRO CRÍTICO: Não foi possível ler o arquivo {file_path.name} com nenhuma codificação testada.")
    return None

def processar_dxf_producao(caminho_dxf, dimensoes_xml, is_porta=False):
    corrected_content = fix_dxf_content(caminho_dxf)
    if corrected_content is None: return []

    try:
        doc = ezdxf.read(io.StringIO(corrected_content))
        msp = doc.modelspace()
    except (IOError, ezdxf.DXFStructureError) as e:
        print(f"Erro ao ler o stream do DXF: {e}")
        return []

    operacoes = []

    comp_peca = dimensoes_xml.get("comprimento", 0)
    larg_peca = dimensoes_xml.get("largura", 0)

    for entidade in msp:
        layer_nome = entidade.dxf.layer.upper()
        if layer_nome == "CONTORNO": continue

        match_rasgo = re.search(r"RASGO_([\d\.\-]+)_([\d\.\-]+)", layer_nome)
        if match_rasgo:
            try:
                rasgo_largura = float(match_rasgo.group(1).replace('-', '.'))
                rasgo_profundidade = float(match_rasgo.group(2).replace('-', '.'))

                points = []
                entity_type = entidade.dxftype()
                if entity_type == 'LINE':
                    points = [entidade.dxf.start, entidade.dxf.end]
                elif entity_type in ['LWPOLYLINE', 'POLYLINE']:
                    points = [v.dxf.location for v in entidade.vertices] if entity_type == 'POLYLINE' else list(entidade.get_points('xy'))

                if not points:
                    print(f"Aviso: Não foi possível extrair geometria para o rasgo na camada {layer_nome}.")
                    continue

                bbox = BoundingBox(points)
                min_x, min_y, _ = bbox.extmin
                max_x, max_y, _ = bbox.extmax

                epsilon = 0.1
                is_horizontal = (max_y - min_y) < epsilon
                is_vertical = (max_x - min_x) < epsilon

                if is_horizontal:
                    rect_x = min_x
                    rect_y = min_y - (rasgo_largura / 2)
                    rect_comprimento = max_x - min_x
                    rect_largura = rasgo_largura
                elif is_vertical:
                    rect_x = min_x - (rasgo_largura / 2)
                    rect_y = min_y
                    rect_comprimento = rasgo_largura
                    rect_largura = max_y - min_y
                else:
                    print(f"Aviso: Rasgo inclinado na camada {layer_nome} não foi processado.")
                    continue

                x_rel = comp_peca + rect_x if rect_x < 0 else rect_x
                y_rel = larg_peca + rect_y if rect_y < 0 else rect_y
                y_final = larg_peca - (y_rel + rect_largura)

                operacoes.append({
                    "tipo": "Retângulo",
                    "x": round(x_rel, 2),
                    "y": round(y_final, 2),
                    "comprimento": round(rect_comprimento, 2),
                    "largura": round(rect_largura, 2),
                    "profundidade": rasgo_profundidade, 
                    "estrategia": "Desbaste",
                    "face": "Face (F0)"
                })
                continue
            except Exception as e:
                print(f"Erro ao processar rasgo da camada {layer_nome}: {e}")
                pass

        match_furo = re.search(r"FURO_([\d\.\-]+)_([\d\.\-]+)", layer_nome)
        if match_furo and entidade.dxftype() == 'CIRCLE':
            try:
                diametro_op = float(match_furo.group(1).replace('-', '.'))
                profundidade_op = float(match_furo.group(2).replace('-', '.'))
                abs_center = entidade.dxf.center

                x_abs = round(abs_center.x, 2)
                y_abs = round(abs_center.y, 2)

                x_rel = comp_peca + x_abs if x_abs < 0 else x_abs
                y_rel = larg_peca + y_abs if y_abs < 0 else y_abs

                if is_porta:
                    x_rel, y_rel = y_rel, x_rel

                y_final = larg_peca - y_rel

                operacoes.append({
                    "tipo": "Furo",
                    "x": round(x_rel, 2),
                    "y": round(y_final, 2),
                    "diametro": diametro_op,
                    "profundidade": profundidade_op,
                    "face": "Face (F0)"
                })
            except Exception:
                pass

        match_usinar = re.search(r"(?:USINAR|PuxadorCava1|PuxadorCava2|PuxadorCavaCurvo1|PuxadorCavaCurvo2|Corte45|PuxadorCava30)_([\d\.\-]+)_([\w\-]+)", layer_nome)
        if match_usinar:
            try:
                profundidade = float(match_usinar.group(1).replace('-', '.'))
                estrategia = match_usinar.group(2)
                entity_type = entidade.dxftype()

                if entity_type == 'CIRCLE':
                    raio = float(entidade.dxf.radius)
                    diametro = raio * 2
                    abs_center = entidade.dxf.center
                    x_abs = round(abs_center.x, 2)
                    y_abs = round(abs_center.y, 2)
                    x_rel = comp_peca + x_abs if x_abs < 0 else x_abs
                    y_rel = larg_peca + y_abs if y_abs < 0 else y_abs
                    y_final = larg_peca - y_rel
                    operacoes.append({
                        "tipo": "Círculo",
                        "x": round(x_rel, 2),
                        "y": round(y_final, 2),
                        "diametro": round(diametro, 2),
                        "profundidade": profundidade,
                        "estrategia": estrategia,
                        "face": "Face (F0)"
                    })
                else:
                    points = []
                    if entity_type == 'LINE':
                        points = [entidade.dxf.start, entidade.dxf.end]
                    elif entity_type in ['LWPOLYLINE', 'POLYLINE']:
                        points = [v.dxf.location for v in entidade.vertices] if entity_type == 'POLYLINE' else list(entidade.get_points('xy'))

                    if not points:
                        continue

                    bbox = BoundingBox(points)
                    min_x, min_y, _ = bbox.extmin
                    max_x, max_y, _ = bbox.extmax

                    rect_x = min_x
                    rect_y = min_y
                    rect_comprimento = max_x - min_x
                    rect_largura = max_y - min_y

                    x_rel = comp_peca + rect_x if rect_x < 0 else rect_x
                    y_rel = larg_peca + rect_y if rect_y < 0 else rect_y
                    y_final = larg_peca - (y_rel + rect_largura)

                    operacoes.append({
                        "tipo": "Retângulo",
                        "x": round(x_rel, 2),
                        "y": round(y_final, 2),
                        "comprimento": round(rect_comprimento, 2),
                        "largura": round(rect_largura, 2),
                        "profundidade": profundidade,
                        "estrategia": estrategia,
                        "face": "Face (F0)"
                    })
            except Exception:
                pass

    return operacoes

materiais = {
    ("18", "700"): "Branco TX 18mm",
    ("18", "999"): "Nogal Terracota 18mm",
}

def classificar_item(item, xml_type='orcamento'):
    """Classifica o item do XML como MDF, ferragem ou outro."""
    desc = item.get("DESCRIPTION", item.get("DESCRICAO", "")).lower()

    if xml_type == 'producao':
        caminho = item.get("CAMINHOITEMCATALOG", "").lower()
        if "montagem" in caminho:
            return "mdf"
        if "ferragens" in caminho or item.get("TIPO_PRODUTO") == "C":
            return "ferragem"
        if (
            "cozinhas" in caminho
            or "fita de borda" in desc
            or item.get("ID") == "CHAPA"
        ):
            return "ignorar"
        if any(
            kw in desc
            for kw in [
                "parafuso",
                "dobradiça",
                "suporte",
                "bucha",
                "cavilha",
                "prego",
                "puxador",
            ]
        ):
            return "ferragem"
        return "outro"

    # xml_type == 'orcamento'
    ref = item.get("REFERENCE", "")
    supplier = item.get("SUPPLIER", "")
    family = item.get("FAMILY", "").lower()
    tipo = item.get("TYPE", "").lower()

    if (
        tipo == "accessory"
        or "parafuso" in desc
        or "dobradiça" in desc
        or "puxador" in desc
        or supplier
        or family in ["acessórios", "ferragem", "ferragens", "puxadores"]
    ):
        return "ferragem"

    if "fita" in desc or item.get("PRODUCTTYPE") == "EdgeBanding":
        return "ignorar"

    try:
        largura = parse_float(item.get("WIDTH", 0))
        comprimento = parse_float(item.get("DEPTH", 0))
        espessura = parse_float(item.get("HEIGHT", 0))
        if (
            item.get("COMPONENT") == "Y"
            and item.get("STRUCTURE") == "N"
            and ref
            and largura > 0
            and comprimento > 0
            and espessura > 0
        ):
            return "mdf"
    except (ValueError, TypeError):
        return "outro"

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
            *[{"tipo": "Furo", "x": 9, "y": y, "diametro": 8, "profundidade": 24, "face": "Topo (L1)"} for y in y_positions],
            *[{"tipo": "Furo", "x": espessura - 9.5, "y": y, "diametro": 8, "profundidade": 24, "face": "Topo (L3)"} for y in y_positions]
        ]
    return operacoes

def parse_bpp_furos_topo(file_path, peca_largura):
    face1_holes_raw = []
    try:
        with open(file_path, 'r', encoding='latin-1') as f: content = f.read()
    except Exception as e:
        print(f"   -> Erro ao ler arquivo BPP {file_path.name}: {e}")
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
    nome_pacote = f"{nome_do_cliente} - {nome_do_projeto}"
    pecas_importadas = []
    pasta_base_dxf = dxt_path.parent
    print(f"📦 Itens <Part> encontrados no DXT: {len(all_parts_data)}")

    for item_data in all_parts_data:
        try:
            descricao_item = item_data.get("PartName", "Sem Nome").strip().upper()
            dxf_da_peca = item_data.get("Filename", "").strip()
            if not dxf_da_peca:
                continue

            dxf_relativo = Path(dxf_da_peca.replace("\\", "/"))
            caminho_dxf = (pasta_base_dxf / dxf_relativo).resolve()

            if not caminho_dxf.exists():
                # tenta localizar o arquivo de forma case-insensitive
                possivel = None
                if caminho_dxf.parent.exists():
                    nome_lower = dxf_relativo.name.lower()
                    for f in caminho_dxf.parent.iterdir():
                        if f.name.lower() == nome_lower:
                            possivel = f
                            break
                if not possivel:
                    for f in pasta_base_dxf.rglob('*'):
                        if f.is_file() and f.name.lower() == dxf_relativo.name.lower():
                            possivel = f
                            break
                if possivel:
                    caminho_dxf = possivel
                else:
                    print(f"      -> AVISO: Arquivo DXF não encontrado: {dxf_relativo}")
                    continue

            print(f"    -> Processando: {descricao_item} | DXF: {dxf_da_peca}")
            comprimento = parse_float(item_data.get("Length", 0))
            largura = parse_float(item_data.get("Width", 0))
            espessura = parse_float(item_data.get("Thickness", 0))

            operacoes_dxf = processar_dxf_producao(
                caminho_dxf,
                {"comprimento": comprimento, "largura": largura},
            )

            operacoes_bpp = []
            caminho_bpp = caminho_dxf.with_suffix('.bpp')
            if caminho_bpp.exists():
                print(f"      -> Arquivo BPP encontrado: {caminho_bpp.name}.")
                operacoes_bpp = parse_bpp_furos_topo(caminho_bpp, largura)
                if operacoes_bpp: print(f"          -> {len(operacoes_bpp)} furos de topo (faces 1 e 3) criados simetricamente.")

            material_node = item_data.get("Material")
            material = material_node if material_node is not None else "Desconhecido"
            material = normalize_material_name(material)

            id_raw = item_data.get("Program1") or Path(dxf_da_peca).stem
            try:
                peca_id = int(str(id_raw).lstrip("0") or "0")
            except (ValueError, TypeError):
                peca_id = None

            pecas_importadas.append({
                "id": peca_id,
                "nome": descricao_item,
                "codigo_peca": Path(dxf_da_peca).stem,
                "comprimento": comprimento,
                "largura": largura,
                "espessura": espessura,
                "material": material,
                "cliente": nome_do_cliente,
                "ambiente": nome_do_projeto,
                "observacoes": item_data.get("Comment", ""),
                "orientacao": "horizontal" if comprimento > largura else "vertical",
                "operacoes": operacoes_dxf + operacoes_bpp,
            })
        except Exception as e:
            print(f"⚠️ Erro inesperado ao processar '{item_data.get('PartName', '')}': {e}.")

    if not pecas_importadas: return []
    print(f"✅ Sucesso! Peças importadas: {len(pecas_importadas)}")
    return [{"nome_pacote": nome_pacote, "pecas": pecas_importadas}]

def parse_xml_orcamento(root):
    """Lê um XML de orçamento gerado pelo Promob e extrai peças e ferragens."""
    pacotes, cliente_node = [], root.find(".//DATA[@ID='nomecliente']")
    nome_cliente = (
        cliente_node.attrib.get("VALUE", "") if cliente_node is not None else "SemCliente"
    )
    ambiente_node = root.find(".//AMBIENT")
    nome_ambiente = (
        ambiente_node.attrib.get("DESCRIPTION", "") if ambiente_node is not None else "SemDescricao"
    )

    nome_pacote = f"{nome_cliente} - {nome_ambiente}"
    pecas, ferragens = [], []

    for item in root.findall(".//ITEM"):
        atributos = item.attrib
        tipo_item = classificar_item(atributos, xml_type="orcamento")

        if tipo_item == "mdf":
            try:
                nome_item = atributos.get("DESCRIPTION", "").upper()
                largura = parse_float(atributos.get("DEPTH", "0"))
                comprimento = parse_float(atributos.get("WIDTH", "0"))
                if (
                    "PORTA" in nome_item or "FRENTE DE" in nome_item
                ) and "BASCULANTE" not in nome_item:
                    largura = parse_float(atributos.get("HEIGHT", "0"))

                ref_parts = atributos.get("REFERENCE", "").split(".")
                espessura = ref_parts[2] if len(ref_parts) > 2 else "?"
                espessura = re.sub(r'(\d+)[.,]\d+', r'\1', str(espessura))
                cor = ref_parts[-1] if len(ref_parts) > 4 else "?"
                material = materiais.get((espessura, cor), f"Desconhecido ({espessura}/{cor})")
                material = normalize_material_name(material)

                peca = {
                    "nome": nome_item,
                    "largura": largura,
                    "comprimento": comprimento,
                    "espessura": espessura,
                    "material": material,
                    "cliente": nome_cliente,
                    "ambiente": nome_ambiente,
                    "observacoes": atributos.get("OBSERVATIONS", ""),
                    "orientacao": "horizontal" if comprimento > largura else "vertical",
                    "status": "Pendente",
                    "codigo_peca": atributos.get("UNIQUEID", ""),
                }
                peca["operacoes"] = inferir_operacoes_por_nome(peca["nome"], largura, comprimento)
                pecas.append(peca)
            except (ValueError, TypeError) as e:
                print(
                    f"Aviso: Ignorando item MDF malformado (Orçamento). Erro: {e}. Atributos: {atributos}"
                )
                continue
        elif tipo_item == "ferragem":
            nome_ferragem = atributos.get("DESCRIPTION", "Ferragem sem descrição")
            try:
                quantidade = int(parse_float(atributos.get("AMOUNT", "1")))
            except ValueError:
                quantidade = 1
            item_existente = next((f for f in ferragens if f["nome"] == nome_ferragem), None)
            if item_existente:
                item_existente["quantidade"] += quantidade
            else:
                ferragens.append({"nome": nome_ferragem, "quantidade": quantidade})

    # Combina MDF e ferragens em um único pacote para que o frontend exiba as
    # ferragens como um "subpacote" dentro da tela do pacote principal.
    pacote = {"nome_pacote": nome_pacote}
    if pecas:
        pacote["pecas"] = pecas
    if ferragens:
        pacote["ferragens"] = ferragens

    if pacote.get("pecas") or pacote.get("ferragens"):
        pacotes.append(pacote)

    return pacotes

def parse_xml_producao(root, xml_path):
    """Lê um XML de produção exportado pelo Promob e extrai peças e ferragens."""
    print("🚀 Início do parse_xml_producao")
    pacotes, pecas, ferragens = [], [], []

    try:
        nome_cliente = root.find(".//CLIENTE_LOJA").attrib["NOME"]
    except Exception:
        nome_cliente = "SemCliente"

    nome_ambiente = "Projeto"
    primeiro_item = root.find(".//ITENS_PEDIDO/ITEM")
    if primeiro_item is not None:
        unique_id_node = primeiro_item.find("UNIQUE_ID")
        if unique_id_node is not None:
            nome_ambiente = unique_id_node.attrib.get("AMBIENTNAME", "Projeto")

    nome_pacote = f"{nome_cliente} - {nome_ambiente}"
    pasta_base = Path(os.path.abspath(xml_path)).parent

    itens = root.findall(".//ITEM")
    print(f"📦 Total de itens encontrados no XML: {len(itens)}")

    for item in itens:
        atributos = item.attrib
        tipo_item = classificar_item(atributos, xml_type="producao")

        if tipo_item == "mdf":
            try:
                desenho_id = atributos.get("DESENHO")
                if not desenho_id:
                    continue

                filename = f"{desenho_id}.dxf"
                caminho_dxf = pasta_base / filename
                if not caminho_dxf.exists():
                    print(f"  -> AVISO: Arquivo DXF não encontrado para a peça '{desenho_id}'")
                    continue

                descricao = atributos.get("DESCRICAO", "Peça sem descrição").strip().upper()

                comprimento_xml = parse_float(atributos.get("LARGURA", "0"))
                largura_xml = parse_float(atributos.get("PROFUNDIDADE", "0"))
                espessura = parse_float(atributos.get("ALTURA", "0"))

                operacoes_dxf = processar_dxf_producao(
                    caminho_dxf,
                    {"comprimento": comprimento_xml, "largura": largura_xml},
                )

                operacoes_bpp = []
                caminho_bpp = caminho_dxf.with_suffix(".bpp")
                if caminho_bpp.exists():
                    print(f"    -> Arquivo BPP encontrado: {caminho_bpp.name}.")
                    operacoes_bpp = parse_bpp_furos_topo(caminho_bpp, largura_xml)

                material_node = item.find(".//COLUNA[@CODIGO='Material']")
                material = (
                    material_node.attrib.get("RESPOSTA", "Desconhecido")
                    if material_node is not None
                    else "Desconhecido"
                )
                material = normalize_material_name(material)

                pecas.append(
                    {
                        "nome": descricao,
                        "codigo_peca": Path(filename).stem,
                        "largura": largura_xml,
                        "comprimento": comprimento_xml,
                        "espessura": espessura,
                        "material": material,
                        "cliente": nome_cliente,
                        "ambiente": nome_ambiente,
                        "observacoes": "",
                        "orientacao": "horizontal" if comprimento_xml > largura_xml else "vertical",
                        "operacoes": operacoes_dxf + operacoes_bpp,
                        "status": "Pendente",
                    }
                )
            except Exception as e:
                print(f"⚠️ Erro ao processar item MDF de produção: {e}. Atributos: {atributos}")

        elif tipo_item == "ferragem":
            nome_ferragem = atributos.get("DESCRICAO", "Ferragem sem descrição")
            codigo_ferragem = atributos.get("REFERENCIA", "S/REF")
            try:
                quantidade = int(parse_float(atributos.get("QUANTIDADE", "1")))
            except ValueError:
                quantidade = 1

            item_existente = next(
                (f for f in ferragens if f["codigo_ferragem"] == codigo_ferragem),
                None,
            )
            if item_existente:
                item_existente["quantidade"] += quantidade
            else:
                ferragens.append(
                    {
                        "nome": nome_ferragem,
                        "codigo_ferragem": codigo_ferragem,
                        "quantidade": quantidade,
                    }
                )

    if pecas or ferragens:
        print(
            f"✅ Itens classificados: {len(pecas)} peças de MDF, {len(ferragens)} tipos de ferragens."
        )

    # Assim como em parse_xml_orcamento, as ferragens são incorporadas ao mesmo
    # pacote de MDF para facilitar a exibição no frontend.
    pacote = {"nome_pacote": nome_pacote}
    if pecas:
        pacote["pecas"] = pecas
    if ferragens:
        pacote["ferragens"] = ferragens

    if pacote.get("pecas") or pacote.get("ferragens"):
        pacotes.append(pacote)

    print("✅ Finalizado parse_xml_producao")
    return pacotes


from pathlib import Path
import csv

def parse_gabster(csv_path: Path) -> list[dict]:
    """Importa arquivos CSV e DXF/GBS exportados pelo Gabster no novo layout DXT Final."""
    print("🚀 Início do parse_gabster")

    pacotes: list[dict] = []
    pecas: list[dict] = []

    with open(csv_path, newline="", encoding="latin-1") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row or len(row) < 10:
                continue

            try:
                # Colunas base
                codigo = row[0].strip()
                comprimento = float(row[1])
                largura = float(row[2])
                espessura = float(row[3])
                material = row[4].strip() + " mm"
                descricao_raw = row[6].strip()
                observacoes = row[7].strip()
                projeto_raw = row[9].strip()

                # Extrai program1 e nome
                if " - " in descricao_raw:
                    program1, nome = descricao_raw.split(" - ", 1)
                else:
                    program1 = ""
                    nome = descricao_raw

                nome = nome.strip().upper()
                program1 = program1.strip()

                # Extrai cliente e ambiente a partir do texto após o hífen
                if "-" in projeto_raw:
                    _, texto = projeto_raw.split("-", 1)
                    cliente = texto.strip()
                else:
                    cliente = projeto_raw.strip()

                ambiente = cliente

                # Localiza DXF
                dxf_path = csv_path.parent / f"{codigo}.dxf"
                if not dxf_path.exists():
                    print(f"  -> AVISO: Arquivo .dxf não encontrado: {dxf_path.name}")
                    continue

                # Processa DXF
                operacoes = processar_dxf_producao(
                    dxf_path, {"comprimento": comprimento, "largura": largura}
                )

                # Tenta processar GBS (se existir)
                gbs_path = dxf_path.with_suffix(".gbs")
                if gbs_path.exists():
                    operacoes += processar_gbs(gbs_path)

                peca = {
                    "nome": nome,
                    "codigo_peca": codigo,
                    "largura": largura,
                    "comprimento": comprimento,
                    "espessura": espessura,
                    "material": material,
                    "cliente": cliente,
                    "ambiente": ambiente,
                    "observacoes": observacoes,
                    "orientacao": "horizontal" if comprimento > largura else "vertical",
                    "operacoes": operacoes,
                    "status": "Pendente",
                }

                pecas.append(peca)

            except Exception as e:
                print(f"⚠️ Erro ao processar linha CSV: {e}. Linha: {row}")

    if pecas:
        pacote = {"nome_pacote": ambiente, "pecas": pecas}
        pacotes.append(pacote)

    print("✅ Finalizado parse_gabster")
    return pacotes
