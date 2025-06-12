# leitor_xml.py
import xml.etree.ElementTree as ET
import os

def ler_pecas_xml_promob_orcamento(caminho):
    tree = ET.parse(caminho)
    root = tree.getroot()

    pecas = {}

    nome_cliente = root.findtext(".//DATA[@ID='nomecliente']", default="")
    ambiente = root.find(".//AMBIENT")
    ambiente_nome = ambiente.attrib.get("DESCRIPTION", "") if ambiente is not None else ""

    for item in root.findall(".//ITEM"):
        if "PAI" in item.attrib.get("ID", "").upper():
            nome = item.attrib.get("DESCRIPTION", "sem_nome")
            nome_arquivo = nome.upper().replace(" ", "_") + ".DXF"

            info = {
                'PartName': nome,
                'Length': float(item.attrib.get('WIDTH', 0)),   # Comprimento (C)
                'Width': float(item.attrib.get('DEPTH', 0)),    # Largura (L)
                'Thickness': float(item.attrib.get('HEIGHT', 0)),
                'Material': "Roble Catedral18mm",
                'Client': nome_cliente,
                'Project': ambiente_nome,
                'comment': item.attrib.get('OBSERVATIONS', '')
            }

            pecas[nome_arquivo] = info

    return pecas
