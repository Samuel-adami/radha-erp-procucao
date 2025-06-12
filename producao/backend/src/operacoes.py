# src/operacoes.py
import re
import io
import ezdxf
from ezdxf.math import BoundingBox

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
                    "face": "Face (F0)" # <-- NOME DA FACE PADRONIZADO
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
                    "tipo": "Furo", "x": round(x_rel, 2), "y": round(y_final, 2),
                    "diametro": diametro_op, "profundidade": profundidade_op, 
                    "face": "Face (F0)" # <-- NOME DA FACE PADRONIZADO
                })
            except: pass

    return operacoes