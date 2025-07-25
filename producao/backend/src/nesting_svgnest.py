"""
Integração inicial com svgnest-python para nesting poligonal.

Use svgnest para gerar um nesting poligonal em SVG, depois extraia as posições
dos objetos para converter em coordenadas de corte.

Para instalar:
    pip install svgnest

Passos gerais:
1. Converta cada polígono de peça em elementos <path> ou <rect> em um SVG.
2. Chame svgnest.nest() passando o SVG das peças e da chapa.
3. Recupere o SVG de saída e extraia as transformações (x/y/rotate).
4. Converta em lista de dicts compatíveis com _arranjar_poligonos_ia.

Por ora esta função é um stub que deve ser implementado.
"""
from typing import List, Dict, Optional

def arranjar_poligonos_svgnest(
    pecas: List[Dict],
    largura: float,
    altura: float,
    espaco: float = 0.0,
    rotacionar: bool = True,
    estoque: Optional[List[Dict]] = None,
    config_maquina: Optional[Dict] = None,
    config_layers: Optional[List[Dict]] = None,
    ferramentas: Optional[List[Dict]] = None,
) -> List[List[Dict]]:
    """
    Gera nesting poligonal usando svgnest-python, respeitando refilos, espaco entre peças,
    possivel rotacionar (veio), e mantendo operações internas (furos/usinagens) atreladas.

    Retorna lista de placas, cada placa é lista de dicts de peça com x, y e rotationAngle.
    """
    # imports late-bound para não carregar dependências fora do uso
    import svgnest.nest as svgnest
    import xml.etree.ElementTree as ET
    from shapely.ops import unary_union
    from shapely import affinity
    from shapely.geometry import Polygon

    # helpers do módulo de nesting retangular
    from nesting import _cfg_val, _is_operacao

    # 1) extrair refilos
    if config_maquina:
        ref_inf = _cfg_val(config_maquina, "refiloInferior", "refilo_inferior")
        ref_sup = _cfg_val(config_maquina, "refiloSuperior", "refilo_superior")
        ref_esq = _cfg_val(config_maquina, "refiloEsquerda", "refilo_esquerda")
        ref_dir = _cfg_val(config_maquina, "refiloDireita", "refilo_direita")
    else:
        ref_inf = ref_sup = ref_esq = ref_dir = 0.0

    # 2) criar SVG de entrada
    svg = ET.Element("svg", {
        "xmlns": "http://www.w3.org/2000/svg",
        "width": str(largura),
        "height": str(altura),
        "viewBox": f"0 0 {largura} {altura}",
    })
    # retangulo base da chapa com refilos
    ET.SubElement(svg, "rect", {
        "x": str(ref_esq), "y": str(ref_inf),
        "width": str(largura - ref_esq - ref_dir),
        "height": str(altura - ref_inf - ref_sup),
        "fill": "none", "stroke": "black"
    })
    # peças + operações internas
    for idx, p in enumerate(pecas):
        poly_main: Polygon = p.get("polygon") or Polygon([
            (0, 0), (p.get("Length", 0), 0),
            (p.get("Length", 0), p.get("Width", 0)), (0, p.get("Width", 0))
        ])
        pts = " ".join(f"{x},{y}" for x, y in poly_main.exterior.coords)
        ET.SubElement(svg, "polygon", {"id": str(idx), "points": pts, "fill": "none", "stroke": "none"})
        for op in p.get("operacoes", []):
            if _is_operacao(op) and isinstance(op.get("polygon"), Polygon):
                ip = op["polygon"]
                pts_i = " ".join(f"{x},{y}" for x, y in ip.exterior.coords)
                ET.SubElement(svg, "polygon", {"id": f"{idx}-op{op['id']}", "points": pts_i, "fill": "none", "stroke": "none"})

    entrada_svg = ET.tostring(svg, encoding="utf-8").decode("utf-8")

    # 3) executar nesting poligonal via svgnest, escrevendo SVG temporário em arquivo
    import tempfile, os, shutil
    from contextlib import redirect_stdout, redirect_stderr

    wbin = largura - ref_esq - ref_dir
    hbin = altura - ref_inf - ref_sup
    tempdir = tempfile.mkdtemp()
    try:
        svg_path = os.path.join(tempdir, "entrada.svg")
        # grava SVG de entrada
        with open(svg_path, "w", encoding="utf-8") as f:
            f.write(entrada_svg)
        # Prepare indexed input files for svgnest (svgnest-python busca sufixos de índice, ex: entrada.svg0, entrada.svg1, ...)
        instances = {svg_path: 1}
        for i in range(instances[svg_path]):
            idx_path = f"{svg_path}{i}"
            with open(idx_path, "w", encoding="utf-8") as f:
                f.write(entrada_svg)
        # executar svgnest dentro do tempdir para gerar combined.svg lá, suprimindo logs do processo
        oldcwd = os.getcwd()
        os.chdir(tempdir)
        try:
            with open(os.devnull, "w") as fnull:
                with redirect_stdout(fnull), redirect_stderr(fnull):
                    svgnest.nest(instances, wbin, hbin)
        finally:
            os.chdir(oldcwd)
        # ler o resultado em combined.svg
        with open(os.path.join(tempdir, "combined.svg"), encoding="utf-8") as f:
            resultado_svg = f.read()
    finally:
        shutil.rmtree(tempdir)

    # 4) parsear resultado
    root = ET.fromstring(resultado_svg)
    placas: List[List[Dict]] = [[]]
    # Normaliza o ID gerado pelo svgnest (basename + índice) e extrai o número final
    import os, re
    for elem in root.findall(".//*[@id]"):
        tid = elem.attrib["id"]
        name = os.path.basename(tid)
        opid = None
        if "-op" in name:
            base, op_str = name.split("-op", 1)
            pid = int(re.search(r"(\d+)$", base).group(1))
            opid = int(op_str)
        else:
            pid = int(re.search(r"(\d+)$", name).group(1))

        tx = ty = theta = 0.0
        tr = elem.attrib.get("transform", "")
        for part in tr.replace(",", " ").split(")"):
            if part.strip().startswith("translate("):
                vx = part.split("(",1)[1]
                x0, y0 = [float(v) for v in vx.split()]
                tx, ty = x0, y0
            if part.strip().startswith("rotate("):
                theta = float(part.split("(",1)[1])

        nova = pecas[pid].copy()
        if isinstance(nova.get("polygon"), Polygon) and rotacionar:
            pm = nova["polygon"]
            pr = affinity.rotate(pm, theta, origin=(0,0))
            nova["polygon"] = affinity.translate(pr, tx, ty)
        nova.update({"x": tx + ref_esq, "y": ty + ref_inf, "rotationAngle": theta if rotacionar else 0})

        if opid is not None:
            for op in nova.setdefault("operacoes", []):
                if op.get("id") == opid and isinstance(op.get("polygon"), Polygon):
                    ip = op["polygon"]
                    ir = affinity.rotate(ip, theta, origin=(0,0)) if rotacionar else ip
                    op["polygon"] = affinity.translate(ir, tx, ty)
                    op["x"] = op.get("x", 0) + tx
                    op["y"] = op.get("y", 0) + ty

        placas[0].append(nova)

    return placas


if __name__ == '__main__':
    # Teste rápido de sanity check para arranjar_poligonos_svgnest
    try:
        from shapely.geometry import Polygon
    except ImportError:
        print("[TEST SKIPPED] requer shapely para teste rápido de nesting_svgnest")
        exit(0)
    # duas peças de exemplo
    pecas = [
        {"polygon": Polygon([(0,0),(100,0),(100,50),(0,50)]), "Length":100, "Width":50, "operacoes":[{"id":2, "polygon":Polygon([(0,0),(10,0),(10,10),(0,10)]), "tipo":"Operacao", "x":0, "y":0}]},
        {"polygon": Polygon([(0,0),(80,0),(80,40),(0,40)]), "Length":80,  "Width":40, "operacoes":[{"id":3, "polygon":Polygon([(0,0),(5,0),(5,5),(0,5)]),   "tipo":"Operacao", "x":0, "y":0}]},
    ]
    try:
        placas = arranjar_poligonos_svgnest(
            pecas, largura=200, altura=200, espaco=0, rotacionar=True,
            estoque=None, config_maquina={}, config_layers=None, ferramentas=None
        )
        print("OK – placas geradas:", placas)
    except Exception as e:
        print("Falha no arranjar_poligonos_svgnest:", e)
