import os
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict


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


def _gcode_basico(p: Dict) -> str:
    """Gera um G-code simples para contornar um retângulo."""
    l = p['Length']
    w = p['Width']
    return '\n'.join([
        '( Powered by Radha ERP )',
        f'( Peça: {p["PartName"]} )',
        'G0 Z50.0',
        'M6 T1',
        'M3 S20000',
        'G0 X0 Y0 Z5.0',
        'G1 Z-1.0 F3000',
        f'G1 X{l:.4f} Y0',
        f'G1 X{l:.4f} Y{w:.4f}',
        f'G1 X0 Y{w:.4f}',
        'G1 X0 Y0',
        'G0 Z50.0',
        'M5',
        'M30',
    ])


def _gerar_cyc(pecas: List[Dict], saida: Path):
    root = ET.Element('CycleFile')
    for p in pecas:
        cycle = ET.SubElement(root, 'Cycle', Name='Cycle_Label')
        ET.SubElement(cycle, 'Field', Name='LabelName', Value=f"{p['Program1']}.bmp")
        ET.SubElement(cycle, 'Field', Name='X', Value=str(p['Length']/2))
        ET.SubElement(cycle, 'Field', Name='Y', Value=str(p['Width']/2))
        ET.SubElement(cycle, 'Field', Name='R', Value='0')
    tree = ET.ElementTree(root)
    tree.write(saida / 'labels.cyc', encoding='utf-8', xml_declaration=False)


def gerar_nesting(pasta_lote: str) -> str:
    """Gera arquivos .nc e .cyc em uma subpasta 'nesting' dentro da pasta do lote."""
    pasta = Path(pasta_lote)
    if not pasta.is_dir():
        raise FileNotFoundError(f"Pasta '{pasta_lote}' não encontrada")
    dxts = list(pasta.glob('*.dxt'))
    if not dxts:
        raise FileNotFoundError('Arquivo DXT não encontrado na pasta do lote')
    pecas = _ler_dxt(dxts[0])
    pasta_saida = pasta / 'nesting'
    pasta_saida.mkdir(exist_ok=True)
    for idx, p in enumerate(pecas, start=1):
        gcode = _gcode_basico(p)
        nc_path = pasta_saida / f"peca_{idx}.nc"
        nc_path.write_text(gcode, encoding='utf-8')
    _gerar_cyc(pecas, pasta_saida)
    return str(pasta_saida)
