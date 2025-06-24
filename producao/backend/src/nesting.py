import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict
from datetime import datetime

from shapely.geometry import box
from shapely.ops import unary_union

from rectpack import newPacker
import ezdxf
from PIL import Image, ImageDraw


def _ler_dxt(dxt_path: Path) -> List[Dict]:
    """Le um arquivo .dxt e extrai dados das peças."""
    root = ET.fromstring(dxt_path.read_text(encoding="utf-8", errors="ignore"))
    pecas = []
    for part in root.findall('.//Part'):
        fields = {f.find('Name').text: f.find('Value').text for f in part.findall('Field')}
        if not fields:
            continue
        try:
            pecas.append({
                'PartName': fields.get('PartName', 'SemNome'),
                'Length': float(fields.get('Length', 0)),
                'Width': float(fields.get('Width', 0)),
                'Thickness': float(fields.get('Thickness', 0)),
                'Program1': fields.get('Program1', ''),
                'Material': fields.get('Material', 'Desconhecido'),
                'Filename': fields.get('Filename', ''),
            })
        except ValueError:
            continue
    return pecas


def _gcode_peca(
    p: Dict,
    ox: float = 0,
    oy: float = 0,
    ferramentas: list[dict] | None = None,
    dxf_path: Path | None = None,
    config_layers: list[dict] | None = None,
    config_maquina: dict | None = None,
    templates: dict | None = None,
    tipo: str = "Peça",
) -> str:
    """Gera G-code para uma peça considerando múltiplas ferramentas."""

    def substituir(texto: str, valores: dict) -> str:
        for k, v in valores.items():
            texto = texto.replace(f'[{k}]', str(v))
        return texto

    def buscar_ferramenta(nome: str) -> dict | None:
        if not ferramentas:
            return None
        for f in ferramentas:
            if str(f.get("codigo")) == str(nome) or f.get("descricao") == nome:
                return f
        return None

    l = p["Length"]
    w = p["Width"]
    linhas = [f"({tipo.upper()} - {l:.0f} x {w:.0f})"]

    ops = []
    if dxf_path and config_layers:
        try:
            doc = ezdxf.readfile(dxf_path)
            msp = doc.modelspace()
            for ent in msp:
                layer = ent.dxf.layer
                cfg = next(
                    (
                        c
                        for c in config_layers
                        if c.get("nome", "").lower() == layer.lower()
                        and c.get("tipo") == "Operação"
                    ),
                    None,
                )
                if not cfg:
                    continue
                ferramenta_cfg = buscar_ferramenta(cfg.get("ferramenta", ""))
                if not ferramenta_cfg:
                    continue
                prof = float(cfg.get("profundidade", 1))
                if ent.dxftype() == "CIRCLE":
                    x = ox + float(ent.dxf.center.x)
                    y = oy + float(ent.dxf.center.y)
                    ops.append({
                        "tool": ferramenta_cfg,
                        "x": x,
                        "y": y,
                        "prof": prof,
                        "layer": layer,
                    })
        except Exception:
            pass

    # Operação padrão - contorno
    ferramenta_padrao = ferramentas[0] if ferramentas else None
    ops.insert(
        0,
        {
            "tool": ferramenta_padrao,
            "contorno": True,
            "l": l,
            "w": w,
        },
    )

    header_tpl = templates.get("header", "") if templates else ""
    troca_tpl = templates.get("troca", "") if templates else ""

    atual = None
    for op in ops:
        tool = op["tool"]
        if tool and tool != atual:
            valores = {
                "T": tool.get("codigo", ""),
                "TOOL_DESCRIPTION": tool.get("descricao", ""),
                "ZH": config_maquina.get("zHoming", "") if config_maquina else "",
                "XH": config_maquina.get("xHoming", "") if config_maquina else "",
                "YH": config_maquina.get("yHoming", "") if config_maquina else "",
                "CMD_EXTRA": tool.get("comandoExtra", ""),
            }
            tpl = header_tpl if atual is None else troca_tpl
            if tpl:
                linhas.extend(substituir(tpl, valores).splitlines())
            else:
                linhas.extend(
                    [
                        "G0 Z50.0",
                        f"M6 T{tool.get('codigo', '')}",
                        f"M3 S{tool.get('velocidadeRotacao', '20000')}",
                    ]
                )
            atual = tool

        if op.get("contorno"):
            linhas.extend(
                [
                    f"G0 X{ox:.4f} Y{oy:.4f} Z5.0",
                    "G1 Z-1.0 F3000",
                    f"G1 X{ox + l:.4f} Y{oy:.4f}",
                    f"G1 X{ox + l:.4f} Y{oy + w:.4f}",
                    f"G1 X{ox:.4f} Y{oy + w:.4f}",
                    f"G1 X{ox:.4f} Y{oy:.4f}",
                    "G0 Z50.0",
                ]
            )
        else:
            linhas.extend(
                [
                    f"({op['layer']})",
                    f"G0 X{op['x']:.4f} Y{op['y']:.4f} Z5.0",
                    f"G1 Z-{op['prof']:.4f} F3000",
                    "G0 Z50.0",
                ]
            )

    return "\n".join(linhas)


def _gerar_cyc(chapas: List[List[Dict]], saida: Path):
    for i, pecas in enumerate(chapas, start=1):
        material = pecas[0].get("Material", "chapa") if pecas else "chapa"
        thickness = int(pecas[0].get("Thickness", 0)) if pecas else 0
        prefix = f"{i:03d}-MDF {thickness}mm {material}"
        root = ET.Element('CycleFile')
        for p in pecas:
            cycle = ET.SubElement(root, 'Cycle', Name='Cycle_Label')
            ET.SubElement(cycle, 'Field', Name='LabelName', Value=f"{p['Program1']}.bmp")
            ET.SubElement(cycle, 'Field', Name='X', Value=str(p['x'] + p['Length']/2))
            ET.SubElement(cycle, 'Field', Name='Y', Value=str(p['y'] + p['Width']/2))
            ET.SubElement(cycle, 'Field', Name='R', Value='0')
        tree = ET.ElementTree(root)
        tree.write(saida / f'{prefix}.cyc', encoding='utf-8', xml_declaration=False)


def _gerar_xml_chapas(
    chapas: List[List[Dict]],
    saida: Path,
    largura_chapa: float,
    altura_chapa: float,
) -> None:
    """Gera um XML listando todas as chapas otimizadas."""
    root = ET.Element("CycleFile")
    for i, pecas in enumerate(chapas, start=1):
        material = pecas[0].get("Material", "chapa") if pecas else "chapa"
        thickness = int(pecas[0].get("Thickness", 0)) if pecas else 0
        prefix = f"{i:03d}-MDF {thickness}mm {material} ({largura_chapa:.0f}mm X {altura_chapa:.0f}mm)"
        cycle = ET.SubElement(root, "Cycle", Name="Cycle_List")
        ET.SubElement(cycle, "Field", Name="PlateID", Value=f"{prefix}.nc")
        ET.SubElement(cycle, "Field", Name="LabelName", Value=f"{prefix}.cyc")
        ET.SubElement(cycle, "Field", Name="Height", Value=f"{altura_chapa:.3f}")
        ET.SubElement(cycle, "Field", Name="Width", Value=f"{largura_chapa:.3f}")
        ET.SubElement(cycle, "Field", Name="Thickness", Value=f"{thickness:02d}")
        ET.SubElement(cycle, "Field", Name="LargeImage", Value=f"{i}.bmp")
        ET.SubElement(cycle, "Field", Name="SmallImage", Value=f"{i}.bmp")
    tree = ET.ElementTree(root)
    try:
        ET.indent(tree, space="  ")  # Python 3.9+
    except AttributeError:
        pass
    tree.write(saida / "chapas.xml", encoding="utf-8", xml_declaration=True)


def _gerar_imagens_chapas(
    chapas: List[List[Dict]],
    saida: Path,
    largura_chapa: float,
    altura_chapa: float,
    config_maquina: dict | None = None,
) -> None:
    """Gera imagens BMP com a disposição das peças em cada chapa."""
    escala = 800 / max(largura_chapa, altura_chapa)
    largura_img = int(largura_chapa * escala)
    altura_img = int(altura_chapa * escala)
    for i, pecas in enumerate(chapas, start=1):
        img = Image.new("RGB", (largura_img, altura_img), "white")
        draw = ImageDraw.Draw(img)
        for p in pecas:
            x1 = int(p["x"] * escala)
            y1 = int(p["y"] * escala)
            x2 = int((p["x"] + p["Length"]) * escala)
            y2 = int((p["y"] + p["Width"]) * escala)
            # converter para origem no canto superior esquerdo
            y1 = altura_img - y1
            y2 = altura_img - y2
            draw.rectangle([x1, y2, x2, y1], outline="black", width=2)
        if config_maquina:
            if config_maquina.get("inverterXChapa"):
                img = img.transpose(Image.FLIP_LEFT_RIGHT)
            if config_maquina.get("inverterYChapa"):
                img = img.transpose(Image.FLIP_TOP_BOTTOM)
            angulo = str(config_maquina.get("anguloRotacaoChapa", "0"))
            if angulo.startswith("90"):
                img = img.rotate(-90, expand=True)
            elif angulo.startswith("180"):
                img = img.rotate(180, expand=True)
            elif angulo.startswith("270"):
                img = img.rotate(-270, expand=True)
        ext = "bmp"
        if config_maquina and config_maquina.get("formatoImagemChapa"):
            ext = config_maquina["formatoImagemChapa"].lower()
        img.save(saida / f"{i}.{ext}")


def _gerar_etiquetas(
    chapas: List[List[Dict]],
    saida: Path,
    config_maquina: dict | None = None,
) -> None:
    """Gera imagens das etiquetas conforme layout configurado."""
    if not config_maquina or not config_maquina.get("layoutEtiqueta"):
        return
    layout = config_maquina.get("layoutEtiqueta", [])
    largura = float(config_maquina.get("tamanhoEtiquetadoraX", 50))
    altura = float(config_maquina.get("tamanhoEtiquetadoraY", 30))
    escala = 4
    ext = str(config_maquina.get("formatoImagemEtiqueta", "bmp")).lower()
    for p in [pc for placa in chapas for pc in placa]:
        img = Image.new("RGB", (int(largura * escala), int(altura * escala)), "white")
        draw = ImageDraw.Draw(img)
        for item in layout:
            campo = item.get("campo")
            if not campo:
                continue
            valor = p.get(campo, "")
            x = float(item.get("x", 0)) * escala
            y = float(item.get("y", 0)) * escala
            draw.text((x, y), str(valor), fill="black")
        nome = Path(p.get("Filename", p.get("PartName", "etiqueta"))).stem
        img.save(saida / f"{nome}.{ext}")


def _gerar_gcodes(
    chapas: List[List[Dict]],
    saida: Path,
    largura_chapa: float,
    altura_chapa: float,
    ferramentas: list[dict] | None = None,
    config_layers: list[dict] | None = None,
    config_maquina: dict | None = None,
    pasta_lote: Path | None = None,
):
    """Gera arquivos .nc usando as configuracoes e chapas fornecidas."""

    def substituir(texto: str, valores: dict) -> str:
        for k, v in valores.items():
            texto = texto.replace(f'[{k}]', str(v))
        return texto

    data_criacao = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

    lista_ferramentas = []
    if config_maquina and config_maquina.get('introducao'):
        if ferramentas:
            for f in ferramentas:
                lista_ferramentas.append(f"{f.get('codigo')} - {f.get('descricao','')}")

    intro_tpl = '( Powered by Radha ERP )'
    if config_maquina and config_maquina.get('introducao'):
        intro_tpl = config_maquina['introducao']

    header_tpl = config_maquina.get('cabecalho', '') if config_maquina else ''
    footer_tpl = config_maquina.get('rodape', '') if config_maquina else ''

    for i, pecas in enumerate(chapas, start=1):
        material = pecas[0].get('Material', 'chapa') if pecas else 'chapa'
        thickness = int(pecas[0].get('Thickness', 0)) if pecas else 0
        prefix = f"{i:03d}-MDF {thickness}mm {material}"

        valores_intro = {
            'CREATION_DATE_TIME': data_criacao,
            'POST_PROCESSOR_NAME': config_maquina.get('nome', '') if config_maquina else '',
            'BATCH_NAME': pasta_lote.name if pasta_lote else '',
            'MATERIAL': material,
            'X_LENGHT': config_maquina.get('comprimentoX', largura_chapa) if config_maquina else largura_chapa,
            'Y_LENGHT': config_maquina.get('comprimentoY', altura_chapa) if config_maquina else altura_chapa,
            'Z_LENGHT': config_maquina.get('movimentacaoZ', 0) if config_maquina else 0,
            'LIST_OF_USED_TOOLS': '\n'.join(f'({t})' for t in lista_ferramentas),
        }
        linhas = substituir(intro_tpl, valores_intro).splitlines()

        primeira_ferramenta = ferramentas[0] if ferramentas else None
        valores_header = {
            'T': primeira_ferramenta.get('codigo') if primeira_ferramenta else '',
            'TOOL_DESCRIPTION': primeira_ferramenta.get('descricao', '') if primeira_ferramenta else '',
            'ZH': config_maquina.get('zHoming', '') if config_maquina else '',
            'XH': config_maquina.get('xHoming', '') if config_maquina else '',
            'YH': config_maquina.get('yHoming', '') if config_maquina else '',
            'CMD_EXTRA': primeira_ferramenta.get('comandoExtra', '') if primeira_ferramenta else '',
        }
        linhas.extend(substituir(header_tpl, valores_header).splitlines())

        for p in pecas:
            dxf_path = None
            if pasta_lote and p.get('Filename'):
                dxf_path = pasta_lote / p['Filename']
            linhas.extend(
                _gcode_peca(
                    p,
                    p['x'],
                    p['y'],
                    ferramentas,
                    dxf_path,
                    config_layers,
                    config_maquina,
                    {'header': '', 'troca': config_maquina.get('trocaFerramenta','') if config_maquina else ''},
                    tipo='PECAS',
                ).split('\n')
            )

        # Gerar sobras
        placa_poly = box(0, 0, largura_chapa, altura_chapa)
        pecas_polys = [box(p['x'], p['y'], p['x'] + p['Length'], p['y'] + p['Width']) for p in pecas]
        sobra_geo = placa_poly.difference(unary_union(pecas_polys))
        if not sobra_geo.is_empty:
            geoms = [sobra_geo] if sobra_geo.geom_type == 'Polygon' else list(sobra_geo.geoms)
            for g in geoms:
                minx, miny, maxx, maxy = g.bounds
                sobra = {
                    'PartName': 'Sobra',
                    'Length': maxx - minx,
                    'Width': maxy - miny,
                    'Thickness': thickness,
                    'Material': material,
                    'Filename': '',
                    'x': minx,
                    'y': miny,
                }
                linhas.extend(
                    _gcode_peca(
                        sobra,
                        sobra['x'],
                        sobra['y'],
                        ferramentas,
                        None,
                        None,
                        config_maquina,
                        {'header': '', 'troca': config_maquina.get('trocaFerramenta','') if config_maquina else ''},
                        tipo='SOBRAS',
                    ).split('\n')
                )

        linhas.extend(substituir(footer_tpl, valores_header).splitlines())
        (saida / f'{prefix}.nc').write_text('\n'.join(linhas), encoding='utf-8')


def gerar_nesting(
    pasta_lote: str,
    largura_chapa: float = 2750,
    altura_chapa: float = 1850,
    ferramentas: list | None = None,
    config_layers: list[dict] | None = None,
    config_maquina: dict | None = None,
) -> str:
    """Realiza o nesting das peças do lote usando rectpack."""
    pasta = Path(pasta_lote)
    if not pasta.is_dir():
        raise FileNotFoundError(f"Pasta '{pasta_lote}' não encontrada")
    dxts = list(pasta.glob('*.dxt'))
    if not dxts:
        raise FileNotFoundError('Arquivo DXT não encontrado na pasta do lote')

    pecas = _ler_dxt(dxts[0])

    pecas_por_material: Dict[str, List[Dict]] = {}
    for p in pecas:
        material = p.get("Material", "Desconhecido")
        pecas_por_material.setdefault(material, []).append(p)

    chapas: List[List[Dict]] = []
    for material, lista in pecas_por_material.items():
        packer = newPacker(rotation=False)
        for p in lista:
            packer.add_rect(int(p['Length']), int(p['Width']), rid=p)
        for _ in range(len(lista)):
            packer.add_bin(int(largura_chapa), int(altura_chapa))
        packer.pack()

        for abin in packer:
            if not abin:
                continue
            placa = []
            for rect in abin:
                piece = rect.rid.copy()
                piece['x'] = float(rect.x)
                piece['y'] = float(rect.y)
                piece['Length'] = float(rect.width)
                piece['Width'] = float(rect.height)
                piece['Material'] = material
                placa.append(piece)
            if placa:
                chapas.append(placa)

    pasta_saida = pasta / 'nesting'
    pasta_saida.mkdir(exist_ok=True)
    _gerar_gcodes(
        chapas,
        pasta_saida,
        largura_chapa,
        altura_chapa,
        ferramentas,
        config_layers,
        config_maquina,
        Path(pasta_lote),
    )
    _gerar_cyc(chapas, pasta_saida)
    _gerar_xml_chapas(chapas, pasta_saida, largura_chapa, altura_chapa)
    _gerar_imagens_chapas(
        chapas,
        pasta_saida,
        largura_chapa,
        altura_chapa,
        config_maquina,
    )
    _gerar_etiquetas(
        chapas,
        pasta_saida,
        config_maquina,
    )
    return str(pasta_saida)

