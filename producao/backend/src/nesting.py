import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict

from rectpack import newPacker


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
            })
        except ValueError:
            continue
    return pecas


def _gcode_peca(p: Dict, ox: float = 0, oy: float = 0, ferramenta: dict | None = None) -> str:
    """Gera um G-code simples para contornar um retângulo com deslocamento."""
    l = p['Length']
    w = p['Width']
    codigo = '1'
    rpm = '20000'
    if ferramenta:
        codigo = str(ferramenta.get('codigo', codigo))
        rpm = str(ferramenta.get('velocidadeRotacao', rpm))
    return '\n'.join([
        f'( Peça: {p["PartName"]} )',
        'G0 Z50.0',
        f'M6 T{codigo}',
        f'M3 S{rpm}',
        f'G0 X{ox:.4f} Y{oy:.4f} Z5.0',
        'G1 Z-1.0 F3000',
        f'G1 X{ox + l:.4f} Y{oy:.4f}',
        f'G1 X{ox + l:.4f} Y{oy + w:.4f}',
        f'G1 X{ox:.4f} Y{oy + w:.4f}',
        f'G1 X{ox:.4f} Y{oy:.4f}',
        'G0 Z50.0',
    ])


def _gerar_cyc(chapas: List[List[Dict]], saida: Path):
    for i, pecas in enumerate(chapas, start=1):
        root = ET.Element('CycleFile')
        for p in pecas:
            cycle = ET.SubElement(root, 'Cycle', Name='Cycle_Label')
            ET.SubElement(cycle, 'Field', Name='LabelName', Value=f"{p['Program1']}.bmp")
            ET.SubElement(cycle, 'Field', Name='X', Value=str(p['x'] + p['Length']/2))
            ET.SubElement(cycle, 'Field', Name='Y', Value=str(p['y'] + p['Width']/2))
            ET.SubElement(cycle, 'Field', Name='R', Value='0')
        tree = ET.ElementTree(root)
        tree.write(saida / f'chapa_{i}.cyc', encoding='utf-8', xml_declaration=False)


def _gerar_gcodes(chapas: List[List[Dict]], saida: Path, ferramenta: dict | None = None):
    for i, pecas in enumerate(chapas, start=1):
        linhas = ['( Powered by Radha ERP )']
        for p in pecas:
            linhas.extend(_gcode_peca(p, p['x'], p['y'], ferramenta).split('\n'))
        linhas.append('M5')
        linhas.append('M30')
        (saida / f'chapa_{i}.nc').write_text('\n'.join(linhas), encoding='utf-8')


def gerar_nesting(pasta_lote: str, largura_chapa: float = 2750, altura_chapa: float = 1850, ferramentas: list | None = None) -> str:
    """Realiza o nesting das peças do lote usando rectpack."""
    pasta = Path(pasta_lote)
    if not pasta.is_dir():
        raise FileNotFoundError(f"Pasta '{pasta_lote}' não encontrada")
    dxts = list(pasta.glob('*.dxt'))
    if not dxts:
        raise FileNotFoundError('Arquivo DXT não encontrado na pasta do lote')

    pecas = _ler_dxt(dxts[0])
    packer = newPacker(rotation=False)
    for p in pecas:
        packer.add_rect(int(p['Length']), int(p['Width']), rid=p)

    for _ in range(len(pecas)):
        packer.add_bin(int(largura_chapa), int(altura_chapa))

    packer.pack()

    chapas: List[List[Dict]] = []
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
            placa.append(piece)
        chapas.append(placa)

    pasta_saida = pasta / 'nesting'
    pasta_saida.mkdir(exist_ok=True)
    ferramenta = None
    if ferramentas:
        for f in ferramentas:
            if f.get('tipo') == 'Fresa':
                ferramenta = f
                break

    _gerar_gcodes(chapas, pasta_saida, ferramenta)
    _gerar_cyc(chapas, pasta_saida)
    return str(pasta_saida)

