import xml.etree.ElementTree as ET
from typing import IO


def parse_promob_xml(file: IO) -> dict:
    """Parse Promob XML budget file and return projects dict."""
    try:
        tree = ET.parse(file)
    except ET.ParseError:
        return {"projetos": {}}

    root = tree.getroot()
    projetos = {}

    for amb in root.findall('.//AMBIENT'):
        nome = amb.attrib.get('DESCRIPTION', 'Projeto')
        itens = []
        total_amb = 0.0
        for item in amb.findall('.//ITEM'):
            desc = item.attrib.get('DESCRIPTION', '').strip()
            quantidade = int(float(item.attrib.get('QUANTITY', '1')))
            price_node = item.find('PRICE')
            total_item = 0.0
            if price_node is not None:
                try:
                    total_item = float(price_node.attrib.get('TOTAL', '0').replace(',', '.'))
                except ValueError:
                    total_item = 0.0
            unitario = total_item / quantidade if quantidade else total_item
            itens.append({
                'descricao': desc,
                'unitario': unitario,
                'quantidade': quantidade,
                'total': total_item,
            })
            total_amb += total_item
        if itens:
            projetos[nome] = {'itens': itens, 'total': total_amb}
    return {'projetos': projetos}
