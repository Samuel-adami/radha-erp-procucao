# gerador_dxf.py
import ezdxf
import os
import xml.etree.ElementTree as ET
from datetime import datetime

def gerar_dxf_base(comprimento, largura, saida_path):
    doc = ezdxf.new()
    msp = doc.modelspace()

    pontos = [
        (0, 0),
        (comprimento, 0),
        (comprimento, largura),
        (0, largura),
        (0, 0)
    ]

    polyline = msp.add_polyline2d(pontos, dxfattribs={"layer": "borda_externa"})
    polyline.close(True)

    doc.saveas(saida_path)
    print(f"📄 Arquivo DXT gerado em: {nome_arquivo}")

def gerar_dxt_final(pecas, pasta_saida, nome_lote):
    nome_arquivo = os.path.join(pasta_saida, f"{nome_lote}.dxt")
    root = ET.Element("ListInformation")

    app_data = ET.SubElement(root, "ApplicationData")
    ET.SubElement(app_data, "Name").text = ""
    ET.SubElement(app_data, "Version").text = "1.0"
    ET.SubElement(app_data, "Date").text = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    part_data = ET.SubElement(root, "PartData")

    for nome, dados in pecas.items():
        info = dados['info']
        part = ET.SubElement(part_data, "Part")

        def add_field(name, value, tipo):
            field = ET.SubElement(part, "Field")
            ET.SubElement(field, "Name").text = name
            ET.SubElement(field, "Type").text = tipo
            ET.SubElement(field, "Value").text = str(value)

        add_field("Filename", nome, "Text")
        add_field("PartName", info.get('PartName', ''), "Text")
        add_field("Length", info.get('Length', 0), "Real")
        add_field("Width", info.get('Width', 0), "Real")
        add_field("Thickness", info.get('Thickness', 0), "Real")
        add_field("Material", info.get('Material', ''), "Text")
        add_field("Client", info.get('Client', ''), "Text")
        add_field("Project", info.get('Project', ''), "Text")
        add_field("Program1", info.get('Program1', ''), "Text")
        add_field("Comment", info.get('comment', ''), "Text")

    tree = ET.ElementTree(root)
    tree.write(nome_arquivo, encoding='utf-8', xml_declaration=True)
    print(f"📄 Arquivo DXT gerado em: {nome_arquivo}")
