import xml.etree.ElementTree as ET
from collections import OrderedDict
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import itertools
import re
from datetime import datetime

from shapely.geometry import box, CAP_STYLE, JOIN_STYLE
from shapely.ops import unary_union
from shapely.geometry import Polygon, MultiPolygon
from shapely import affinity

from rectpack import newPacker
import ezdxf
import math
from ezdxf.math import ConstructionArc
from PIL import Image, ImageDraw

# Área mínima aproveitável para registrar sobras (0,1 m² em mm²)
AREA_MIN_SOBRA = 0.1 * 1000 * 1000


def _retangulo_sobra(g: Polygon, tol: float = 1e-6) -> Optional[Polygon]:
    """Return a rectangular polygon if ``g`` already forms a rectangle."""
    if not isinstance(g, Polygon) or g.is_empty:
        return None
    rect = box(*g.bounds)
    if g.symmetric_difference(rect).area > tol:
        return None
    if rect.area < AREA_MIN_SOBRA:
        return None
    return rect

# Fallback templates to ensure `.nc` files always contain the standard headers
# and footers even quando a configuração da máquina estiver ausente ou vazia.
DEFAULT_INTRO = (
    "%\n"
    "( Powered by Radha ERP )\n"
    "( Criação: [CREATION_DATE_TIME] )\n"
    "( Pós processador: [POST_PROCESSOR_NAME] )\n"
    "( Lote: [BATCH_NAME] )\n"
    "( Material: [MATERIAL] )\n"
    "( Dimensões: X:[X_LENGHT] Y:[Y_LENGHT] Z:[Z_LENGHT] )\n"
    "            ( Ferramentas necessárias para a execução dos trabalhos: )\n"
    "[LIST_OF_USED_TOOLS]\n"
)

# Template utilizado para o primeiro bloco de cabeçalho logo após a
# introdução quando nenhum valor é definido na configuração da máquina.
DEFAULT_HEADER = (
    "(######## HEADER ########)\n"
    "( NUMERO DA FERRAMENTA: [T] - [TOOL_DESCRIPTION] )\n"
    "G0 Z[ZH]\n"
    "M6 T[T]\n"
    "[CMD_EXTRA]\n"
)

DEFAULT_TROCA = (
    "(######## Troca de ferramentas ########)\n"
    "( NUMERO DA FERRAMENTA: [T] - [TOOL_DESCRIPTION] )\n"
    "G0 Z[ZH]\n"
    "M6 T[T]\n"
    "[CMD_EXTRA]\n"
)

DEFAULT_FOOTER = (
    "(######## FOOTER ########)\n"
    "G0 Z[ZH]\n"
    "(G0 X[XH]Y[YH] retirado a pedido do Samuel)\n"
    "M5\n"
    "M30\n"
    "%\n"
)

DEFAULT_COMANDO_FUROS = "(####### Desliga Magazine de Furação #######)\n" "M15\n"


def _parse_angle(value: Optional[str]) -> int:
    """Return rotation angle in degrees extracted from a string."""
    if not value:
        return 0
    digits = re.findall(r"-?\d+", str(value))
    if not digits:
        return 0
    try:
        angle = int(digits[0]) % 360
    except ValueError:
        angle = 0
    return angle


def _apply_image_orientation(img: Image.Image, cfg: Dict) -> Image.Image:
    """Rotate/flip image according to machine configuration."""
    if cfg.get("inverterXChapa"):
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
    if cfg.get("inverterYChapa"):
        img = img.transpose(Image.FLIP_TOP_BOTTOM)
    ang = _parse_angle(cfg.get("anguloRotacaoChapa"))
    if ang == 90:
        img = img.rotate(-90, expand=True)
    elif ang == 180:
        img = img.rotate(180, expand=True)
    elif ang == 270:
        img = img.rotate(-270, expand=True)
    return img


from database import get_db_connection
from sqlalchemy import text
from database import schema, PLACEHOLDER

SCHEMA_PREFIX = f"{schema}." if schema else ""


def _sanitize_extension(ext: Optional[str], default: str = "bmp") -> str:
    """Normalize and validate an image extension."""
    ext = str(ext or "").strip().lower().lstrip(".")
    if not ext or f".{ext}" not in Image.registered_extensions():
        return default
    return ext


def _sanitize_material_name(name: str) -> str:
    """Return material name without fractional thickness like 18.5mm."""
    name = str(name or "").strip()
    return re.sub(r"(\d+)\.\d+(?=mm)", r"\1", name, flags=re.IGNORECASE)


def _is_operacao(cfg: Dict) -> bool:
    """Return True if layer configuration represents an operation."""
    tipo = str(cfg.get("tipo", "")).lower()
    return tipo in {"operação", "operacao"}


def _rotate_rect_cw(x: float, y: float, w: float, h: float, largura: float) -> tuple:
    """Rotate rectangle 270 degrees clockwise so that the rotated plate starts
    at the lower-left origin."""
    return y, x, h, w


def _rotate_poly_cw(poly: Polygon, largura: float) -> Polygon:
    """Rotate polygon 270 degrees clockwise keeping coordinates positive with
    origin at the lower-left."""
    g = affinity.rotate(poly, -90, origin=(0, 0))
    g = affinity.scale(g, yfact=-1, origin=(0, 0))
    minx, miny, _, _ = g.bounds
    return affinity.translate(g, xoff=-minx, yoff=-miny)


def _rotate_plate_cw(chapa: Dict) -> Dict:
    """Rotate entire plate data (in-place) 270 degrees clockwise."""
    largura = chapa.get("largura", 0)
    altura = chapa.get("altura", 0)
    for op in chapa.get("operacoes", []):
        x, y, w, h = op.get("x", 0), op.get("y", 0), op.get("largura", 0), op.get("altura", 0)
        nx, ny, nw, nh = _rotate_rect_cw(x, y, w, h, largura)
        op["x"], op["y"], op["largura"], op["altura"] = nx, ny, nw, nh
        if op.get("coords"):
            op["coords"] = [[cy, cx] for cx, cy in op["coords"]]
        if isinstance(op.get("polygon"), (Polygon, MultiPolygon)):
            op["polygon"] = _rotate_poly_cw(op["polygon"], largura)
    chapa["largura"], chapa["altura"] = altura, largura
    return chapa


def _rotate_placa_cw(placa: List[Dict], largura: float) -> List[Dict]:
    """Rotate coordinates of each piece on a plate clockwise."""
    for p in placa:
        x, y = p.get("x", 0), p.get("y", 0)
        l, w = p.get("Length", 0), p.get("Width", 0)
        nx, ny, nl, nw = _rotate_rect_cw(x, y, l, w, largura)
        p["x"], p["y"], p["Length"], p["Width"] = nx, ny, nl, nw
        if isinstance(p.get("polygon"), (Polygon, MultiPolygon)):
            p["polygon"] = _rotate_poly_cw(p["polygon"], largura)
    return placa


def _expand_cmd_extra(tool: Optional[Dict]) -> str:
    """Substitute placeholders in ``comandoExtra`` for milling tools."""
    if not tool:
        return ""
    extra = tool.get("comandoExtra", "")
    if tool.get("tipo") != "Broca":
        extra = extra.replace("[S]", str(tool.get("velocidadeRotacao", "")))
        extra = extra.replace("[T]", str(tool.get("codigo", "")))
    return extra


def _add_field(cycle: ET.Element, name: str, value: str) -> ET.Element:
    """Create a ``Field`` element ensuring ``Value`` precedes ``Name``."""
    attrib = OrderedDict([("Value", value), ("Name", name)])
    return ET.SubElement(cycle, "Field", attrib=attrib)


def _cfg_val(cfg: Optional[Dict], *keys: str, default: float = 0.0) -> float:
    """Return ``float`` value from ``cfg`` trying multiple key variants."""
    if not cfg:
        return default
    for k in keys:
        if k in cfg:
            try:
                return float(cfg[k])
            except Exception:
                break
    return float(cfg.get(keys[0], default))


def _invert_x(x: float, width: float, chapa_width: float) -> float:
    """Return ``x`` mirrored using the right edge of the sheet as origin."""
    return chapa_width - (x + width)


def _medidas_dxf(path: Path) -> Optional[Tuple[float, float]]:
    # (Sem alteração — mesma função de extração de medidas do DXF)
    try:
        doc = ezdxf.readfile(path)
    except Exception:
        return None
    msp = doc.modelspace()
    xs: List[float] = []
    ys: List[float] = []
    for ent in msp:
        layer = str(ent.dxf.layer).lower()
        if layer in ("borda_externa", "contorno"):
            try:
                if ent.dxftype() == "LINE":
                    xs.extend([float(ent.dxf.start.x), float(ent.dxf.end.x)])
                    ys.extend([float(ent.dxf.start.y), float(ent.dxf.end.y)])
                elif ent.dxftype() in ("LWPOLYLINE", "POLYLINE"):
                    if ent.dxftype() == "POLYLINE":
                        for v in ent.vertices:
                            xs.append(float(v.dxf.location.x))
                            ys.append(float(v.dxf.location.y))
                    else:
                        for x, y in ent.get_points("xy"):
                            xs.append(float(x))
                            ys.append(float(y))
                elif ent.dxftype() == "CIRCLE":
                    cx = float(ent.dxf.center.x)
                    cy = float(ent.dxf.center.y)
                    r = float(ent.dxf.radius)
                    xs.extend([cx - r, cx + r])
                    ys.extend([cy - r, cy + r])
                elif ent.dxftype() == "ARC":
                    arc = ConstructionArc(
                        ent.dxf.center,
                        ent.dxf.radius,
                        ent.dxf.start_angle,
                        ent.dxf.end_angle,
                    )
                    bbox = arc.bounding_box
                    xs.extend([float(bbox.extmin.x), float(bbox.extmax.x)])
                    ys.extend([float(bbox.extmin.y), float(bbox.extmax.y)])
            except Exception:
                continue
    if not xs or not ys:
        return None
    return max(xs) - min(xs), max(ys) - min(ys)


def _ler_dxt(dxt_path: Path) -> List[Dict]:
    # (Sem alteração — parse do DXT)
    root = ET.fromstring(dxt_path.read_text(encoding="utf-8", errors="ignore"))
    pecas = []
    pasta = dxt_path.parent
    for part in root.findall(".//Part"):
        fields = {
            f.find("Name").text: f.find("Value").text
            for f in part.findall("Field")
            if f.find("Name") is not None and f.find("Value") is not None
        }
        if not fields:
            continue
        try:
            filename = fields.get("Filename", "")
            length = float(fields.get("Length", 0))
            width = float(fields.get("Width", 0))
            if filename:
                medidas = _medidas_dxf(pasta / filename)
                if medidas:
                    length, width = medidas
            pecas.append(
                {
                    "PartName": fields.get("PartName", "SemNome"),
                    "Length": length,
                    "Width": width,
                    "Thickness": float(fields.get("Thickness", 0)),
                    "Program1": fields.get("Program1", ""),
                    "Material": fields.get("Material", "Desconhecido"),
                    "Filename": filename,
                    "Client": fields.get("Client", ""),
                    "Project": fields.get("Project", ""),
                }
            )
        except ValueError:
            continue
    return pecas


def _gcode_peca(
    p: Dict,
    ox: float = 0,
    oy: float = 0,
    ferramentas: Optional[List[Dict]] = None,
    dxf_path: Optional[Path] = None,
    config_layers: Optional[List[Dict]] = None,
    config_maquina: Optional[Dict] = None,
    templates: Optional[Dict] = None,
    tipo: str = "Peça",
    etapa: str = "todas",
    ferramenta_atual: Optional[Dict] = None,
    rotated: bool = False,
    orig_length: Optional[float] = None,
    orig_width: Optional[float] = None,
    rotation_angle: int = 0,
):
    # (Sem alteração estrutural — função já estava em bom padrão, só pequenas correções de nomenclatura.)
    _ = rotation_angle  # parâmetro reservado para uso futuro
    def substituir(texto: str, valores: dict) -> str:
        for k, v in valores.items():
            texto = texto.replace(f"[{k}]", str(v))
        texto = re.sub(r"\[[^\[\]]+\]", "", texto)
        return texto

    def buscar_ferramenta(nome: str) -> Optional[Dict]:
        if not ferramentas:
            return None
        for f in ferramentas:
            if str(f.get("codigo")) == str(nome) or f.get("descricao") == nome:
                return f
        return None

    l = p["Length"]
    w = p["Width"]
    # A descrição da peça não é mais acrescentada automaticamente para evitar
    # comentários extras nos códigos gerados.
    linhas: List[str] = []
    z_seg = float(config_maquina.get("zSeguranca", 48)) if config_maquina else 48
    z_pre = float(config_maquina.get("zAntesTrabalho", 20)) if config_maquina else 20

    try:
        casas_dec = int(config_maquina.get("casasDecimais", 4)) if config_maquina else 4
    except (TypeError, ValueError):
        casas_dec = 4

    def fmt(val: float) -> str:
        return f"{float(val):.{casas_dec}f}"


    mov_rapida = config_maquina.get("movRapida", "") if config_maquina else ""
    mov_corte_ini = (
        config_maquina.get("primeiraMovCorte", "") if config_maquina else ""
    )
    mov_corte = config_maquina.get("movCorte", "") if config_maquina else ""

    def g0(x: float, y: float, z: float) -> str:
        """Return rapid move ensuring all axes are present."""
        if mov_rapida:
            return substituir(
                mov_rapida, {"X": fmt(x), "Y": fmt(y), "Z": fmt(z)}
            )
        return f"G0 X{fmt(x)} Y{fmt(y)} Z{fmt(z)}"

    def g1_ini(x: float, y: float, z: float, f: float) -> str:
        """Return first cut movement (G1) with all axes."""
        if mov_corte_ini:
            return substituir(
                mov_corte_ini,
                {"X": fmt(x), "Y": fmt(y), "Z": fmt(z), "F": fmt(f)},
            )
        return f"G1 X{fmt(x)} Y{fmt(y)} Z{fmt(z)} F{fmt(f)}"

    def g1(x: float, y: float, z: float, f: float) -> str:
        """Return cut movement (G1) with all axes."""
        if mov_corte:
            return substituir(
                mov_corte, {"X": fmt(x), "Y": fmt(y), "Z": fmt(z), "F": fmt(f)}
            )
        return f"G1 X{fmt(x)} Y{fmt(y)} Z{fmt(z)} F{fmt(f)}"

    ops = []
    if dxf_path and config_layers:
        try:
            doc = ezdxf.readfile(dxf_path)
            msp = doc.modelspace()
            from ezdxf.math import Matrix44, Vec2

            cx = ox + (orig_length or l) / 2
            cy = oy + (orig_width or w) / 2

            if rotated:
                ang = rotation_angle or 90
                m = Matrix44.axis_rotate(angle=math.radians(ang), axis="z", center=(cx, cy, 0))

                def rotacionar_ponto(x: float, y: float) -> tuple:
                    v = Vec2(x, y).transform(m)
                    return v.x, v.y
            else:
                def rotacionar_ponto(x: float, y: float) -> tuple:
                    return x, y
            for ent in msp:
                layer = ent.dxf.layer
                cfg = next(
                    (
                        c
                        for c in config_layers
                        if c.get("nome", "").lower() == layer.lower()
                        and _is_operacao(c)
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
                    cx0 = float(ent.dxf.center.x) + ox
                    cy0 = float(ent.dxf.center.y) + oy
                    x, y = rotacionar_ponto(cx0, cy0)
                    ops.append(
                        {
                            "tool": ferramenta_cfg,
                            "x": x,
                            "y": y,
                            "prof": prof,
                            "layer": layer,
                        }
                    )
                elif ent.dxftype() in {"LINE", "LWPOLYLINE", "POLYLINE"}:
                    points = []
                    if ent.dxftype() == "LINE":
                        points = [ent.dxf.start, ent.dxf.end]
                    elif ent.dxftype() == "POLYLINE":
                        points = [
                            (float(v.dxf.location.x), float(v.dxf.location.y))
                            for v in ent.vertices
                        ]
                    else:
                        points = list(ent.get_points("xy"))
                    xs = [float(p[0]) for p in points]
                    ys = [float(p[1]) for p in points]
                    if xs and ys:
                        x = min(xs)
                        y = min(ys)
                        x0 = x + ox
                        y0 = y + oy
                        x, y = rotacionar_ponto(x0, y0)
                        ops.append(
                            {
                                "tool": ferramenta_cfg,
                                "x": x,
                                "y": y,
                                "prof": prof,
                                "layer": layer,
                            }
                        )
        except Exception:
            pass

    # Operação padrão - contorno (para peça ou sobra)
    ferramenta_padrao = ferramentas[0] if ferramentas else None
    contorno_op = {
        "tool": ferramenta_padrao,
        "contorno": True,
        "l": l,
        "w": w,
    }
    ops.insert(0, contorno_op)

    # ``troca_tpl`` define o bloco emitido sempre que ocorre mudança de
    # ferramenta. Ele também é utilizado para a primeira ferramenta da peça.
    troca_tpl = templates.get("troca", "") if templates else ""

    # Ordenar e agrupar operações (para garantir ordem de furos, fresas, contorno)
    if ops and ops[0].get("contorno"):
        contorno_op = ops.pop(0)
    else:
        contorno_op = None

    furos_ops = [o for o in ops if o.get("tool", {}).get("tipo") == "Broca"]
    fresa_ops = [o for o in ops if o.get("tool", {}).get("tipo") != "Broca"]

    furos_ops.sort(key=lambda o: (o.get("y", 0), o.get("x", 0)))

    if etapa == "furos":
        ops = furos_ops
    elif etapa == "fresas":
        ops = fresa_ops
    elif etapa == "contorno":
        ops = [contorno_op] if contorno_op else []
    else:
        ops = furos_ops + fresa_ops
        if contorno_op:
            ops.append(contorno_op)

    atual = ferramenta_atual
    usadas: List[str] = []
    last_layer: Optional[str] = None

    for op in ops:
        tool = op["tool"]
        if tool:
            desc = f"{tool.get('codigo')} - {tool.get('descricao','')}"
            if desc not in usadas:
                usadas.append(desc)
        if tool and tool != atual:
            valores = {
                "T": tool.get("codigo", ""),
                "TOOL_DESCRIPTION": tool.get("descricao", ""),
                "ZH": config_maquina.get("zHoming", "") if config_maquina else "",
                "XH": config_maquina.get("xHoming", "") if config_maquina else "",
                "YH": config_maquina.get("yHoming", "") if config_maquina else "",
                "CMD_EXTRA": _expand_cmd_extra(tool),
            }
            # Sempre utilizar o template de troca de ferramentas, inclusive para
            # a primeira ferramenta. Isso garante que todos os blocos iniciem
            # com o mesmo cabeçalho padronizado.
            tpl = troca_tpl
            if tpl:
                linhas.extend(substituir(tpl, valores).splitlines())
                linhas.append("")
            atual = tool


        if op.get("contorno"):
            tipo_lbl = tipo.upper()
            if tipo_lbl == "PECA":
                tipo_lbl = "PECAS"
            elif tipo_lbl == "SOBRA":
                tipo_lbl = "SOBRAS"
            linhas.append(f"({tipo_lbl} - {int(round(l))} x {int(round(w))})")
            linhas.extend(
                [
                    g0(ox, oy, z_seg),
                    g0(ox, oy, z_pre),
                    "(Step:1/1)",
                    g1_ini(ox + l, oy, 0.2, 3500.0),
                    g1(ox + l, oy + w, 0.2, 7000.0),
                    g1(ox, oy + w, 0.2, 7000.0),
                    g1(ox, oy, 0.2, 7000.0),
                    g0(ox, oy, z_seg),
                ]
            )
        else:
            if op["layer"] != last_layer:
                linhas.append(f"({op['layer']})")
                last_layer = op["layer"]
            linhas.extend(
                [
                    g0(op["x"], op["y"], z_seg),
                    g0(op["x"], op["y"], z_pre),
                    "(Step:1/1)",
                    g1_ini(op["x"], op["y"], op["prof"], 5000.0),
                    g0(op["x"], op["y"], z_seg),
                ]
            )

    return "\n".join(linhas), atual, usadas


# (continua na próxima mensagem — Funções de geração de NC, sobras, etiquetas, etc)


def _gerar_cyc(
    chapas: List[List[Dict]],
    saida: Path,
    largura_chapa: float,
    sobras: Optional[List[List[Dict]]] = None,
) -> None:
    """Gera arquivos ``.cyc`` posicionando etiquetas de peças e sobras."""
    for i, pecas in enumerate(chapas, start=1):
        todas = list(pecas)
        if sobras and i - 1 < len(sobras):
            todas.extend(sobras[i - 1])
        material = pecas[0].get("Material", "chapa") if pecas else "chapa"
        material = _sanitize_material_name(material)
        prefix = f"{i:03d}-{material}"
        root = ET.Element("CycleFile")
        for p in todas:
            cycle = ET.SubElement(root, "Cycle", Name="Cycle_Label")
            _add_field(cycle, "LabelName", f"{p['Program1']}.bmp")
            _add_field(
                cycle,
                "X",
                str(
                    _invert_x(
                        p["x"],
                        p["Length"],
                        largura_chapa,
                    )
                    + p["Length"] / 2
                ),
            )
            _add_field(cycle, "Y", str(p["y"] + p["Width"] / 2))
            _add_field(cycle, "R", "0")
        tree = ET.ElementTree(root)
        try:
            ET.indent(tree, space="  ")
        except AttributeError:
            pass
        tree.write(saida / f"{prefix}.cyc", encoding="utf-8", xml_declaration=True)


def _gerar_xml_chapas(
    chapas: List[List[Dict]],
    saida: Path,
    largura_chapa: float,
    altura_chapa: float,
    nome_lote: str,
) -> None:
    """Gera o XML com a lista de chapas seguindo o formato da máquina."""

    root = ET.Element("CycleFile")

    orientacao = "Vertical" if largura_chapa >= altura_chapa else "Horizontal"
    color_val = f"{orientacao}({altura_chapa/1000:.2f}X{largura_chapa/1000:.2f})"
    lote_fmt = nome_lote.replace("_", " ")

    for i, pecas in enumerate(chapas, start=1):
        material = pecas[0].get("Material", "chapa") if pecas else "chapa"
        material = _sanitize_material_name(material)
        thickness = int(pecas[0].get("Thickness", 0)) if pecas else 0
        # Use the exact NC file name generated for the plate
        # to ensure the XML references match the real files.
        prefix = f"{i:03d}-{material}"

        cycle = ET.SubElement(root, "Cycle", Name="Cycle_List")
        _add_field(cycle, "PlateID", f"{prefix}.nc")
        _add_field(cycle, "LabelName", f"{prefix}.cyc")
        _add_field(cycle, "LargeImage", f"{prefix}_LargeImage.bmp")
        _add_field(cycle, "SmallImage", f"{prefix}_SmallImage.bmp")
        _add_field(cycle, "Color", color_val)
        _add_field(cycle, "Thickness", str(thickness))

    tree = ET.ElementTree(root)
    try:
        ET.indent(tree, space="  ")
    except AttributeError:
        pass

    tree.write(saida / f"{lote_fmt}.xml", encoding="utf-8", xml_declaration=True)


def _gerar_imagens_chapas(
    chapas: List[List[Dict]],
    saida: Path,
    largura_chapa: float,
    altura_chapa: float,
    config_maquina: Optional[Dict] = None,
    sobras: Optional[List[List[Dict]]] = None,
) -> None:
    escala = 800 / max(largura_chapa, altura_chapa)
    largura_img = int(largura_chapa * escala)
    altura_img = int(altura_chapa * escala)
    tamanho_grande = (592, 890)
    tamanho_pequeno = (122, 183)
    for i, pecas in enumerate(chapas, start=1):
        img = Image.new("RGBA", (largura_img, altura_img), "white")
        draw = ImageDraw.Draw(img)
        todas = list(pecas)
        if sobras and i - 1 < len(sobras):
            todas.extend(sobras[i - 1])
        for p in todas:
            poly = p.get("polygon")
            if isinstance(poly, (Polygon, MultiPolygon)):
                geoms = [poly] if isinstance(poly, Polygon) else list(poly.geoms)
                for geom in geoms:
                    coords = [
                        (int(x * escala), altura_img - int(y * escala))
                        for x, y in geom.exterior.coords
                    ]
                    draw.polygon(coords, outline="black")
                    for interior in geom.interiors:
                        coords = [
                            (int(x * escala), altura_img - int(y * escala))
                            for x, y in interior.coords
                        ]
                        draw.polygon(coords, outline="black")
            else:
                x1 = int(p["x"] * escala)
                y1 = int(p["y"] * escala)
                x2 = int((p["x"] + p["Length"]) * escala)
                y2 = int((p["y"] + p["Width"]) * escala)
                y1 = altura_img - y1
                y2 = altura_img - y2
                draw.rectangle([x1, y2, x2, y1], outline="black", width=2)
        if config_maquina:
            img = _apply_image_orientation(img, config_maquina)
        material = pecas[0].get("Material", "chapa") if pecas else "chapa"
        material = _sanitize_material_name(material)
        prefix = f"{i:03d}-{material}"
        img_large = img.resize(tamanho_grande)
        img_small = img.resize(tamanho_pequeno)
        img_large.save(saida / f"{prefix}_LargeImage.bmp")
        img_small.save(saida / f"{prefix}_SmallImage.bmp")


def _gerar_etiquetas(
    chapas: List[List[Dict]],
    saida: Path,
    config_maquina: Optional[Dict] = None,
    sobras: Optional[List[List[Dict]]] = None,
) -> None:
    if not config_maquina or not config_maquina.get("layoutEtiqueta"):
        return
    layout = config_maquina.get("layoutEtiqueta", [])
    largura = float(config_maquina.get("tamanhoEtiquetadoraX", 50))
    altura = float(config_maquina.get("tamanhoEtiquetadoraY", 30))
    escala = 4
    ext = _sanitize_extension(config_maquina.get("formatoImagemEtiqueta", "bmp"))

    pecas = [pc for placa in chapas for pc in placa]
    if sobras:
        for s in sobras:
            pecas.extend(s)
    for p in pecas:
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
        if config_maquina:
            img = _apply_image_orientation(img, config_maquina)
        nome = (
            p.get("Program1")
            or Path(p.get("Filename", p.get("PartName", "etiqueta"))).stem
        )
        path = saida / f"{nome}.{ext}"
        try:
            img.save(path)
        except ValueError:
            img.save(saida / f"{nome}.bmp")


def _gerar_gcodes(
    chapas: List[List[Dict]],
    saida: Path,
    largura_chapa: float,
    altura_chapa: float,
    ferramentas: Optional[List[Dict]] = None,
    config_layers: Optional[List[Dict]] = None,
    config_maquina: Optional[Dict] = None,
    pasta_lote: Optional[Path] = None,
):
    def substituir(texto: str, valores: dict) -> str:
        for k, v in valores.items():
            texto = texto.replace(f"[{k}]", str(v))
        texto = re.sub(r"\[[^\[\]]+\]", "", texto)
        return texto

    data_criacao = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    try:
        casas_dec = int(config_maquina.get("casasDecimais", 4)) if config_maquina else 4
    except (TypeError, ValueError):
        casas_dec = 4

    def fmt(val: float) -> str:
        return f"{float(val):.{casas_dec}f}"

    # Gerador de IDs sequenciais para sobras
    max_id = 0
    for placa in chapas:
        for p in placa:
            try:
                val = int(re.sub(r"\D", "", str(p.get("Program1", ""))) or 0)
            except ValueError:
                continue
            if val > max_id:
                max_id = val
    proximo_id = itertools.count(max_id + 1)

    def coletar_ferramentas(pecas: List[Dict]) -> Tuple[List[str], Optional[Dict]]:
        usadas: List[str] = []
        primeira: Optional[Dict] = None
        for p in pecas:
            dxf_path = None
            if pasta_lote and p.get("Filename"):
                dxf_path = pasta_lote / p["Filename"]
            _, last_tool, used = _gcode_peca(
                p,
                _invert_x(p.get("x", 0), p.get("Length", 0), largura_chapa),
                p.get("y", 0),
                ferramentas,
                dxf_path,
                config_layers,
                config_maquina,
                {"header": "", "troca": ""},
                etapa="todas",
                rotated=p.get("rotated", False),
                orig_length=p.get("originalLength"),
                orig_width=p.get("originalWidth"),
                rotation_angle=p.get("rotationAngle", 90 if p.get("rotated") else 0),
            )
            if used and primeira is None:
                code = used[0].split(" - ", 1)[0]
                primeira = next(
                    (f for f in (ferramentas or []) if str(f.get("codigo")) == code),
                    None,
                )
            for u in used:
                if u not in usadas:
                    usadas.append(u)
        return usadas, primeira

    intro_tpl = (
        config_maquina.get("introducao") if config_maquina else None
    ) or DEFAULT_INTRO

    header_tpl = (
        config_maquina.get("cabecalho") if config_maquina else None
    ) or DEFAULT_HEADER

    # Para garantir uniformidade no programa gerado o bloco inicial de
    # ferramenta utiliza o mesmo template aplicado nas trocas seguintes.
    troca_tpl = (
        config_maquina.get("trocaFerramenta") if config_maquina else None
    ) or DEFAULT_TROCA
    footer_tpl = (
        config_maquina.get("rodape") if config_maquina else None
    ) or DEFAULT_FOOTER
    cmd_furos = (
        config_maquina.get("comandoFinalFuros") if config_maquina else None
    ) or DEFAULT_COMANDO_FUROS

    sobras_por_chapa: List[List[Dict]] = []
    for i, pecas in enumerate(chapas, start=1):
        material = pecas[0].get("Material", "chapa") if pecas else "chapa"
        material = _sanitize_material_name(material)
        thickness = int(float(pecas[0].get("Thickness", 0))) if pecas else 0
        prefix = f"{i:03d}-{material}"

        # Margens de refilo configuradas para a máquina
        ref_inf = _cfg_val(config_maquina, "refiloInferior", "refilo_inferior")
        ref_sup = _cfg_val(config_maquina, "refiloSuperior", "refilo_superior")
        ref_esq = _cfg_val(config_maquina, "refiloEsquerda", "refilo_esquerda")
        ref_dir = _cfg_val(config_maquina, "refiloDireita", "refilo_direita")
        area_larg = largura_chapa - ref_esq - ref_dir
        area_alt = altura_chapa - ref_inf - ref_sup
        espaco = (
            float(config_maquina.get("espacoEntrePecas", 0)) if config_maquina else 0
        )

        lista_ferramentas, primeira_ferramenta = coletar_ferramentas(pecas)

        # Garantir que sempre haja uma ferramenta inicial para preencher o
        # cabeçalho. Quando não há operações de furação (Broca) a
        # função ``coletar_ferramentas`` pode retornar ``None``.
        if primeira_ferramenta is None and ferramentas:
            primeira_ferramenta = ferramentas[0]

        material_desc = f"{prefix} [{largura_chapa}mm X {altura_chapa}mm]"
        valores_intro = {
            "CREATION_DATE_TIME": data_criacao,
            "POST_PROCESSOR_NAME": (
                config_maquina.get("nome", "") if config_maquina else ""
            ),
            "BATCH_NAME": pasta_lote.name if pasta_lote else "",
            "MATERIAL": material_desc,
            "X_LENGHT": fmt(
                config_maquina.get("comprimentoX", largura_chapa)
                if config_maquina
                else largura_chapa
            ),
            "Y_LENGHT": fmt(
                config_maquina.get("comprimentoY", altura_chapa)
                if config_maquina
                else altura_chapa
            ),
            "Z_LENGHT": fmt(
                config_maquina.get("movimentacaoZ", 0) if config_maquina else 0
            ),
            "LIST_OF_USED_TOOLS": "\n".join(f"({t})" for t in lista_ferramentas),
        }
        linhas = substituir(intro_tpl, valores_intro).splitlines()
        linhas.append("")

        valores_header = {
            "T": primeira_ferramenta.get("codigo") if primeira_ferramenta else "",
            "TOOL_DESCRIPTION": (
                primeira_ferramenta.get("descricao", "") if primeira_ferramenta else ""
            ),
            "ZH": config_maquina.get("zHoming", "") if config_maquina else "",
            "XH": config_maquina.get("xHoming", "") if config_maquina else "",
            "YH": config_maquina.get("yHoming", "") if config_maquina else "",
            "CMD_EXTRA": _expand_cmd_extra(primeira_ferramenta),
        }
        linhas.extend(substituir(header_tpl, valores_header).splitlines())
        linhas.append("G90")
        linhas.append("")
        if config_maquina and config_maquina.get("furos"):
            linhas.extend(
                substituir(config_maquina["furos"], valores_header).splitlines()
            )

        last_tool = primeira_ferramenta
        tpl_troca = {"header": "", "troca": troca_tpl}

        furos_lines: List[str] = []
        for p in pecas:
            dxf_path = None
            if pasta_lote and p.get("Filename"):
                dxf_path = pasta_lote / p["Filename"]
            codigo, last_tool, _ = _gcode_peca(
                p,
                _invert_x(p["x"], p["Length"], largura_chapa),
                p["y"],
                ferramentas,
                dxf_path,
                config_layers,
                config_maquina,
                tpl_troca,
                tipo="PECAS",
                etapa="furos",
                ferramenta_atual=last_tool,
                rotated=p.get("rotated", False),
                orig_length=p.get("originalLength"),
                orig_width=p.get("originalWidth"),
                rotation_angle=p.get("rotationAngle", 90 if p.get("rotated") else 0),
            )
            furos_lines.extend(codigo.split("\n")[1:])
        if last_tool and last_tool.get("tipo") == "Broca":
            furos_lines.extend(str(cmd_furos).splitlines())

        fresas_lines: List[str] = []
        primeira_fresa = True
        tem_fresa_por_peca: List[bool] = []
        for p in pecas:
            dxf_path = None
            if pasta_lote and p.get("Filename"):
                dxf_path = pasta_lote / p["Filename"]
            codigo, last_tool, _ = _gcode_peca(
                p,
                _invert_x(p["x"], p["Length"], largura_chapa),
                p["y"],
                ferramentas,
                dxf_path,
                config_layers,
                config_maquina,
                tpl_troca,
                tipo="PECAS",
                etapa="fresas",
                ferramenta_atual=last_tool,
                rotated=p.get("rotated", False),
                orig_length=p.get("originalLength"),
                orig_width=p.get("originalWidth"),
                rotation_angle=p.get("rotationAngle", 90 if p.get("rotated") else 0),
            )
            if codigo.strip():
                tem_fresa = True
            else:
                tem_fresa = False
            tem_fresa_por_peca.append(tem_fresa)
            if primeira_fresa:
                fresas_lines.extend(codigo.split("\n"))
                primeira_fresa = False
            else:
                fresas_lines.extend(codigo.split("\n")[1:])

        contorno_lines: List[str] = []
        for idx, p in enumerate(pecas):
            dxf_path = None
            if pasta_lote and p.get("Filename"):
                dxf_path = pasta_lote / p["Filename"]
            codigo, last_tool, _ = _gcode_peca(
                p,
                _invert_x(p["x"], p["Length"], largura_chapa),
                p["y"],
                ferramentas,
                dxf_path,
                config_layers,
                config_maquina,
                tpl_troca,
                tipo="PECAS",
                etapa="contorno",
                ferramenta_atual=last_tool,
                rotated=p.get("rotated", False),
                orig_length=p.get("originalLength"),
                orig_width=p.get("originalWidth"),
                rotation_angle=p.get("rotationAngle", 90 if p.get("rotated") else 0),
            )
            if tem_fresa_por_peca[idx]:
                contorno_lines.extend(codigo.split("\n")[1:])
            else:
                contorno_lines.extend(codigo.split("\n"))

        linhas.extend(furos_lines)
        linhas.extend(fresas_lines)
        linhas.extend(contorno_lines)

        # Geração de sobras nas bordas da chapa
        # As posições das peças já incluem a margem de refilo. Para gerar as
        # sobras corretamente precisamos considerar apenas a área útil da
        # chapa (sem o refilo), por isso subtraímos o refilo das coordenadas
        # absolutas das peças.
        x_min = min((p["x"] - ref_esq for p in pecas), default=0)
        y_min = min((p["y"] - ref_inf for p in pecas), default=0)
        x_max = max(
            (p["x"] - ref_esq + p["Length"] + espaco for p in pecas), default=0
        )
        y_max = max(
            (p["y"] - ref_inf + p["Width"] + espaco for p in pecas), default=0
        )

        pecas_polys = [
            box(p["x"], p["y"], p["x"] + p["Length"], p["y"] + p["Width"])
            for p in pecas
        ]
        pecas_union = unary_union(pecas_polys) if pecas_polys else None

        sobras_chapa: List[Dict] = []
        sobras_polys: List[Polygon] = []

        def add_sobra(px: float, py: float, w: float, h: float):
            nonlocal last_tool, sobras_polys
            if w <= 0 or h <= 0:
                return
            nova = box(px, py, px + w, py + h)
            if pecas_union:
                nova = nova.difference(pecas_union)
            for p_exist in sobras_polys:
                nova = nova.difference(p_exist)
                if nova.is_empty:
                    return
            geoms = [nova] if isinstance(nova, Polygon) else list(nova.geoms)
            for g in geoms:
                if pecas_union:
                    g = g.difference(pecas_union)
                if g.is_empty:
                    continue
                g_rect = _retangulo_sobra(g)
                if not g_rect:
                    continue
                minx, miny, maxx, maxy = g_rect.bounds
                sobra = {
                    "PartName": "SB",
                    "Length": maxx - minx,
                    "Width": maxy - miny,
                    "Thickness": thickness,
                    "Material": material,
                    "Observacao": f"Sobra da chapa original {largura_chapa}x{altura_chapa}",
                    "Filename": "",
                    "Program1": f"{next(proximo_id):08d}",
                    "x": minx,
                    "y": miny,
                    "polygon": g_rect,
                }
                codigo, last_tool, _ = _gcode_peca(
                    sobra,
                    _invert_x(sobra["x"], sobra["Length"], largura_chapa),
                    sobra["y"],
                    ferramentas,
                    None,
                    None,
                    config_maquina,
                    tpl_troca,
                    tipo="Sobra",
                    etapa="contorno",
                    ferramenta_atual=last_tool,
                    rotation_angle=0,
                )
                sobras_chapa.append(sobra)
                sobras_polys.append(g_rect)
                linhas.extend(codigo.split("\n"))

        # As sobras devem considerar apenas a área útil da chapa, logo é
        # necessário aplicar o deslocamento dos refilos nas coordenadas.
        cut_l = max(0.0, x_min)
        cut_b = max(0.0, y_min)
        cut_r = min(area_larg, x_max)
        cut_t = min(area_alt, y_max)

        add_sobra(ref_esq, ref_inf, cut_l, area_alt)
        add_sobra(ref_esq + cut_r, ref_inf, area_larg - cut_r, area_alt)
        add_sobra(ref_esq, ref_inf, area_larg, cut_b)
        add_sobra(ref_esq, ref_inf + cut_t, area_larg, area_alt - cut_t)

        # Sobras internas (vazios entre peças)
        internas = _calcular_sobras_polys(
            pecas_polys, ref_esq, ref_inf, area_larg, area_alt, espaco
        )

        if sobras_polys:
            internas = [g.difference(unary_union(sobras_polys)) for g in internas]
        if pecas_union:
            internas = [g.difference(pecas_union) for g in internas]
        for g in internas:
            if g.is_empty:
                continue
            geoms = [g] if isinstance(g, Polygon) else list(g.geoms)
            for geom in geoms:
                if pecas_union:
                    geom = geom.difference(pecas_union)
                if geom.is_empty:
                    continue
                g_rect = _retangulo_sobra(geom)
                if not g_rect:
                    continue
                minx, miny, maxx, maxy = g_rect.bounds
                sobra = {
                    "PartName": "SB",
                    "Length": maxx - minx,
                    "Width": maxy - miny,
                    "Thickness": thickness,
                    "Material": material,
                    "Observacao": f"Sobra da chapa original {largura_chapa}x{altura_chapa}",
                    "Filename": "",
                    "Program1": f"{next(proximo_id):08d}",
                    "x": minx,
                    "y": miny,
                    "polygon": g_rect,
                }
                codigo, last_tool, _ = _gcode_peca(
                    sobra,
                    _invert_x(sobra["x"], sobra["Length"], largura_chapa),
                    sobra["y"],
                    ferramentas,
                    None,
                    None,
                    config_maquina,
                    tpl_troca,
                    tipo="Sobra",
                    etapa="contorno",
                    ferramenta_atual=last_tool,
                    rotation_angle=0,
                )
                sobras_chapa.append(sobra)
                sobras_polys.append(g_rect)
                linhas.extend(codigo.split("\n"))

        sobras_por_chapa.append(sobras_chapa)

        linhas.extend(substituir(footer_tpl, valores_header).splitlines())
        (saida / f"{prefix}.nc").write_text("\r\n".join(linhas), encoding="utf-8")

    return sobras_por_chapa


def _encontrar_dxt(pasta: Path) -> Optional[Path]:
    """Retorna o primeiro arquivo .dxt encontrado ignorando o case."""
    for arq in pasta.iterdir():
        if arq.is_file() and arq.suffix.lower() == ".dxt":
            return arq
    return None


def _ops_from_dxf(
    caminho: Path,
    config_layers: Optional[List[Dict]] = None,
    ox: float = 0.0,
    oy: float = 0.0,
    rotated: bool = False,
    orig_length: Optional[float] = None,
    orig_width: Optional[float] = None,
) -> List[Dict]:
    """Retorna operações encontradas no DXF em ``caminho``.

    Atualmente apenas círculos, linhas e polilinhas são considerados. O
    ``ox``/``oy`` é aplicado como offset para posicionar a operação dentro da
    chapa.
    """
    if not config_layers:
        return []
    try:
        doc = ezdxf.readfile(caminho)
    except Exception:
        return []
    msp = doc.modelspace()
    ops: List[Dict] = []
    next_id = 1
    for ent in msp:
        layer = str(ent.dxf.layer)
        cfg = next(
            (
                c
                for c in config_layers
                if c.get("nome", "").lower() == layer.lower() and _is_operacao(c)
            ),
            None,
        )
        if not cfg:
            continue
        if ent.dxftype() == "CIRCLE":
            r = float(ent.dxf.radius)
            cx = float(ent.dxf.center.x)
            cy = float(ent.dxf.center.y)
            if rotated and orig_length and orig_width:
                cx, cy = orig_width - cy, cx
            cx += ox
            cy += oy
            ops.append(
                {
                    "id": next_id,
                    "nome": layer,
                    "tipo": "Operacao",
                    "layer": layer,
                    "x": cx - r,
                    "y": cy - r,
                    "largura": 2 * r,
                    "altura": 2 * r,
                    # A rotação já é aplicada nos cálculos de posição quando a pe
                    # ça está rotacionada. Para o visualizador manter as
                    # operações dentro da peça, não precisamos informar este
                    # ângulo separadamente.
                    "rotacao": 0,
                }
            )
            next_id += 1
        elif ent.dxftype() in {"LINE", "LWPOLYLINE", "POLYLINE"}:
            points = []
            if ent.dxftype() == "LINE":
                points = [ent.dxf.start, ent.dxf.end]
            elif ent.dxftype() == "POLYLINE":
                points = [
                    (float(v.dxf.location.x), float(v.dxf.location.y))
                    for v in ent.vertices
                ]
            else:
                points = list(ent.get_points("xy"))
            xs = [float(p[0]) for p in points]
            ys = [float(p[1]) for p in points]
            if xs and ys:
                x = min(xs)
                y = min(ys)
                w = max(xs) - min(xs)
                h = max(ys) - min(ys)
                if rotated and orig_length and orig_width:
                    x, y, w, h = (
                        orig_width - (y + h),
                        x,
                        h,
                        w,
                    )
                    x += ox
                    y += oy
                else:
                    x = x + ox
                    y = y + oy
                ops.append(
                    {
                        "id": next_id,
                        "nome": layer,
                        "tipo": "Operacao",
                        "layer": layer,
                        "x": x,
                        "y": y,
                        "largura": w,
                        "altura": h,
                        # A rotação das operações já foi levada em conta ao
                        # recalcular ``x`` e ``y`` quando a peça é girada.
                        "rotacao": 0,
                    }
                )
                next_id += 1
    return ops


def _calcular_sobras_polys(
    pecas_polys: List[Polygon],
    ref_esq: float,
    ref_inf: float,
    area_larg: float,
    area_alt: float,
    espaco: float = 0.0,
) -> List[Polygon]:
    """Retorna polígonos de sobra da chapa considerando as peças posicionadas.

    ``espaco`` corresponde ao afastamento entre as peças. Ele é subtraído da
    área útil, pois representa o material removido pela fresa no contorno externo.
    """

    chapa = box(ref_esq, ref_inf, ref_esq + area_larg, ref_inf + area_alt)
    if espaco > 0:
        pecas_polys = [
            p.buffer(
                espaco / 2,
                cap_style=CAP_STYLE.square,
                join_style=JOIN_STYLE.mitre,
            )
            for p in pecas_polys
        ]

    if pecas_polys:
        pecas_union = unary_union(pecas_polys)
        sobra = chapa.difference(pecas_union)
    else:
        pecas_union = None
        sobra = chapa

    geoms = [sobra] if isinstance(sobra, Polygon) else list(sobra.geoms)
    if pecas_union:
        geoms = [g.difference(pecas_union) for g in geoms]
    return [g for g in geoms if not g.is_empty]


def _carregar_estoque(materiais: List[str]) -> Dict[str, List[Dict]]:
    """Retorna sobras cadastradas no estoque para os materiais informados."""
    estoque: Dict[str, List[Dict]] = {}
    try:
        with get_db_connection() as conn:
            for mat in materiais:
                rows = (
                    conn.exec_driver_sql(
                        f"SELECT id, chapa_id, descricao, comprimento, largura FROM {SCHEMA_PREFIX}chapas_estoque WHERE descricao ILIKE {PLACEHOLDER}",
                        (f"%{mat}%",),
                    )
                    .mappings()
                    .all()
                )
                if rows:
                    estoque[mat] = [dict(r) for r in rows]
    except Exception:
        pass
    return estoque


def gerar_nesting_preview(
    pasta_lote: str,
    largura_chapa: float = 2750,
    altura_chapa: float = 1850,
    ferramentas: Optional[List[Dict]] = None,
    config_layers: Optional[List[Dict]] = None,
    config_maquina: Optional[Dict] = None,
    estoque: Optional[Dict[str, List[Dict]]] = None,
) -> List[Dict]:
    """Gera apenas a disposição das chapas sem criar arquivos."""

    pasta = Path(pasta_lote)
    if not pasta.is_dir():
        raise FileNotFoundError(f"Pasta '{pasta_lote}' não encontrada")

    dxt_path = _encontrar_dxt(pasta)
    if not dxt_path:
        raise FileNotFoundError("Arquivo DXT não encontrado na pasta do lote")
    pecas = _ler_dxt(dxt_path)

    # Configurações de chapas cadastradas
    chapas_cfg: Dict[str, Dict] = {}
    try:
        with get_db_connection() as conn:
            rows = conn.execute(
                text(
                    "SELECT propriedade, possui_veio, comprimento, largura FROM chapas"
                )
            ).fetchall()
            for r in rows:
                chapas_cfg[r["propriedade"]] = dict(r._mapping)
    except Exception:
        pass

    pecas_por_material: Dict[str, List[Dict]] = {}
    for p in pecas:
        material = p.get("Material", "Desconhecido")
        pecas_por_material.setdefault(material, []).append(p)

    if estoque is None:
        estoque = _carregar_estoque(list(pecas_por_material.keys()))




    chapas: List[Dict] = []
    idx = 1
    espaco = float(config_maquina.get("espacoEntrePecas", 0)) if config_maquina else 0
    ref_inf = _cfg_val(config_maquina, "refiloInferior", "refilo_inferior")
    ref_sup = _cfg_val(config_maquina, "refiloSuperior", "refilo_superior")
    ref_esq = _cfg_val(config_maquina, "refiloEsquerda", "refilo_esquerda")
    ref_dir = _cfg_val(config_maquina, "refiloDireita", "refilo_direita")
    area_larg = largura_chapa - ref_esq - ref_dir
    area_alt = altura_chapa - ref_inf - ref_sup

    for material, lista in pecas_por_material.items():
        cfg = chapas_cfg.get(material, {})
        rot = False if cfg.get("possui_veio") else True
        largura = float(cfg.get("comprimento", area_larg))
        altura = float(cfg.get("largura", area_alt))

        packer = newPacker(rotation=rot)
        for p in lista:
            packer.add_rect(int(p["Length"] + espaco), int(p["Width"] + espaco), rid=p)
        estoque_material = estoque.get(material) if estoque else []
        if estoque_material:
            min_l = min(float(p["Length"]) for p in lista)
            min_w = min(float(p["Width"]) for p in lista)
            for s in estoque_material:
                c = float(s.get("comprimento", 0))
                l = float(s.get("largura", 0))
                fits = (
                    (c >= min_l and l >= min_w)
                    or (rot and c >= min_w and l >= min_l)
                )
                if fits:
                    packer.add_bin(int(c), int(l))
        for _ in range(len(lista)):
            packer.add_bin(int(largura), int(altura))
        packer.pack()

        for abin in packer:
            if not abin:
                continue
            operacoes: List[Dict] = []
            sobras_polys: List[Polygon] = []
            x_min = 1e9
            y_min = 1e9
            x_max = 0.0
            y_max = 0.0
            op_id = 1
            pecas_polys: List[Polygon] = []
            for rect in abin:
                p = rect.rid.copy()
                orig_l = float(p.get("Length", 0))
                orig_w = float(p.get("Width", 0))
                p_x = float(rect.x) + ref_esq
                p_y = float(rect.y) + ref_inf
                w = float(rect.width) - espaco
                h = float(rect.height) - espaco
                rotated_piece = (
                    abs(w - orig_w) < 1e-6
                    and abs(h - orig_l) < 1e-6
                    and orig_l != orig_w
                )
                p["originalLength"] = orig_l
                p["originalWidth"] = orig_w
                p["rotated"] = rotated_piece
                p["rotationAngle"] = 90 if rotated_piece else 0
                operacoes.append(
                    {
                        "id": op_id,
                        "nome": p.get("PartName", f"Peca {op_id}"),
                        "tipo": "Peca",
                        "x": p_x,
                        "y": p_y,
                        "largura": w,
                        "altura": h,
                        "cliente": p.get("Client", ""),
                        "ambiente": p.get("Project", ""),
                    }
                )
                op_id += 1
                if p.get("Filename") and config_layers:
                    dxf_ops = _ops_from_dxf(
                        pasta / p["Filename"],
                        config_layers,
                        p_x,
                        p_y,
                        rotated_piece,
                        orig_l,
                        orig_w,
                    )
                    for d in dxf_ops:
                        d["id"] = op_id
                        d["cliente"] = p.get("Client", "")
                        d["ambiente"] = p.get("Project", "")
                        operacoes.append(d)
                        op_id += 1
                x_min = min(x_min, rect.x)
                y_min = min(y_min, rect.y)
                x_max = max(x_max, rect.x + rect.width)
                y_max = max(y_max, rect.y + rect.height)
                pecas_polys.append(box(p_x, p_y, p_x + w, p_y + h))

            pecas_union = unary_union(pecas_polys) if pecas_polys else None

            def add_sobra(px: float, py: float, w: float, h: float):
                nonlocal op_id, sobras_polys
                if w <= 0 or h <= 0:
                    return
                nova = box(px, py, px + w, py + h)
                if pecas_union:
                    nova = nova.difference(pecas_union)
                for p_exist in sobras_polys:
                    nova = nova.difference(p_exist)
                    if nova.is_empty:
                        return
                geoms = [nova] if isinstance(nova, Polygon) else list(nova.geoms)
                for g in geoms:
                    if pecas_union:
                        g = g.difference(pecas_union)
                    if g.is_empty:
                        continue
                    g_rect = _retangulo_sobra(g)
                    if not g_rect:
                        continue
                    minx, miny, maxx, maxy = g_rect.bounds
                    operacoes.append(
                        {
                            "id": op_id,
                            "nome": "Sobra",
                            "tipo": "Sobra",
                            "x": minx,
                            "y": miny,
                            "largura": maxx - minx,
                            "altura": maxy - miny,
                            "coords": [
                                [float(cx), float(cy)] for cx, cy in g_rect.exterior.coords
                            ],
                        }
                    )
                    sobras_polys.append(g_rect)
                    op_id += 1

            # Ajusta as sobras considerando o deslocamento das margens de refilo
            cut_l = max(0.0, x_min)
            cut_b = max(0.0, y_min)
            cut_r = min(area_larg, x_max)
            cut_t = min(area_alt, y_max)

            add_sobra(ref_esq, ref_inf, cut_l, area_alt)
            add_sobra(ref_esq + cut_r, ref_inf, area_larg - cut_r, area_alt)
            add_sobra(ref_esq, ref_inf, area_larg, cut_b)
            add_sobra(ref_esq, ref_inf + cut_t, area_larg, area_alt - cut_t)

            # Sobras internas
            internas = _calcular_sobras_polys(
                pecas_polys, ref_esq, ref_inf, area_larg, area_alt, espaco
            )

            if sobras_polys:
                internas = [g.difference(unary_union(sobras_polys)) for g in internas]
            if pecas_union:
                internas = [g.difference(pecas_union) for g in internas]
            for g in internas:
                if g.is_empty:
                    continue
                geoms = [g] if isinstance(g, Polygon) else list(g.geoms)
                for geom in geoms:
                    if pecas_union:
                        geom = geom.difference(pecas_union)
                    if geom.is_empty:
                        continue
                    g_rect = _retangulo_sobra(geom)
                    if not g_rect:
                        continue
                    minx, miny, maxx, maxy = g_rect.bounds
                    operacoes.append(
                        {
                            "id": op_id,
                            "nome": "Sobra",
                            "tipo": "Sobra",
                            "x": minx,
                            "y": miny,
                            "largura": maxx - minx,
                            "altura": maxy - miny,
                            "coords": [
                                [float(cx), float(cy)] for cx, cy in g_rect.exterior.coords
                            ],
                        }
                    )
                    sobras_polys.append(g_rect)
                    op_id += 1

            if operacoes:
                desc_chapa = cfg.get("propriedade", material)
                desc_chapa = f"{desc_chapa} ({int(largura)} x {int(altura)})"
                chapa = {
                    "id": idx,
                    "codigo": f"{idx:03d}",
                    "descricao": desc_chapa,
                    "temVeio": bool(cfg.get("possui_veio")),
                    "largura": largura,
                    "altura": altura,
                    "operacoes": operacoes,
                }
                chapas.append(_rotate_plate_cw(chapa))
                idx += 1

    return chapas


def gerar_nesting(
    pasta_lote: str,
    largura_chapa: float = 2750,
    altura_chapa: float = 1850,
    ferramentas: Optional[List] = None,
    config_layers: Optional[List[Dict]] = None,
    config_maquina: Optional[Dict] = None,
    estoque: Optional[Dict[str, List[Dict]]] = None,
) -> tuple[str, List[List[Dict]]]:
    pasta = Path(pasta_lote)
    if not pasta.is_dir():
        raise FileNotFoundError(f"Pasta '{pasta_lote}' não encontrada")
    dxt_path = _encontrar_dxt(pasta)
    if not dxt_path:
        raise FileNotFoundError("Arquivo DXT não encontrado na pasta do lote")

    pecas = _ler_dxt(dxt_path)

    # Carregar configuracoes de chapas
    chapas_cfg: Dict[str, Dict] = {}
    try:
        with get_db_connection() as conn:
            rows = conn.execute(
                text(
                    "SELECT propriedade, possui_veio, comprimento, largura FROM chapas"
                )
            ).fetchall()
            for r in rows:
                chapas_cfg[r["propriedade"]] = dict(r._mapping)
    except Exception:
        pass

    pecas_por_material: Dict[str, List[Dict]] = {}
    for p in pecas:
        material = p.get("Material", "Desconhecido")
        pecas_por_material.setdefault(material, []).append(p)
    if estoque is None:
        estoque = _carregar_estoque(list(pecas_por_material.keys()))


    espaco = float(config_maquina.get("espacoEntrePecas", 0)) if config_maquina else 0
    ref_inf = _cfg_val(config_maquina, "refiloInferior", "refilo_inferior")
    ref_sup = _cfg_val(config_maquina, "refiloSuperior", "refilo_superior")
    ref_esq = _cfg_val(config_maquina, "refiloEsquerda", "refilo_esquerda")
    ref_dir = _cfg_val(config_maquina, "refiloDireita", "refilo_direita")
    area_larg = largura_chapa - ref_esq - ref_dir
    area_alt = altura_chapa - ref_inf - ref_sup

    chapas: List[List[Dict]] = []
    for material, lista in pecas_por_material.items():
        cfg = chapas_cfg.get(material, {})
        rot = False if cfg.get("possui_veio") else True
        largura = float(cfg.get("comprimento", area_larg))
        altura = float(cfg.get("largura", area_alt))
        packer = newPacker(rotation=rot)
        for p in lista:
            packer.add_rect(int(p["Length"] + espaco), int(p["Width"] + espaco), rid=p)
        estoque_material = estoque.get(material) if estoque else []
        if estoque_material:
            min_l = min(float(p["Length"]) for p in lista)
            min_w = min(float(p["Width"]) for p in lista)
            for s in estoque_material:
                c = float(s.get("comprimento", 0))
                l = float(s.get("largura", 0))
                fits = (
                    (c >= min_l and l >= min_w)
                    or (rot and c >= min_w and l >= min_l)
                )
                if fits:
                    packer.add_bin(int(c), int(l))
        for _ in range(len(lista)):
            packer.add_bin(int(largura), int(altura))
        packer.pack()

        for abin in packer:
            if not abin:
                continue
            placa = []
            for rect in abin:
                piece = rect.rid.copy()
                orig_l = float(piece.get("Length", 0))
                orig_w = float(piece.get("Width", 0))
                piece["x"] = float(rect.x) + ref_esq
                piece["y"] = float(rect.y) + ref_inf
                piece["Length"] = float(rect.width) - espaco
                piece["Width"] = float(rect.height) - espaco
                piece["Material"] = material
                rotated_piece = (
                    abs(rect.width - orig_w) < 1e-6
                    and abs(rect.height - orig_l) < 1e-6
                    and orig_l != orig_w
                )
                piece["originalLength"] = orig_l
                piece["originalWidth"] = orig_w
                piece["rotated"] = rotated_piece
                piece["rotationAngle"] = 90 if rotated_piece else 0
                placa.append(piece)
            if placa:
                chapas.append(_rotate_placa_cw(placa, largura))

    pasta_saida = pasta / "nesting"
    pasta_saida.mkdir(exist_ok=True)
    sobras = _gerar_gcodes(
        chapas,
        pasta_saida,
        altura_chapa,
        largura_chapa,
        ferramentas,
        config_layers,
        config_maquina,
        Path(pasta_lote),
    )
    _gerar_cyc(chapas, pasta_saida, altura_chapa, sobras)
    _gerar_xml_chapas(
        chapas,
        pasta_saida,
        altura_chapa,
        largura_chapa,
        pasta.name,
    )
    _gerar_imagens_chapas(
        chapas,
        pasta_saida,
        altura_chapa,
        largura_chapa,
        config_maquina,
        sobras,
    )
    _gerar_etiquetas(
        chapas,
        pasta_saida,
        config_maquina,
        sobras,
    )
    return str(pasta_saida), sobras
