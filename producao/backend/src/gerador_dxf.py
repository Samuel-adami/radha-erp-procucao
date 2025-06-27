# gerador_dxf.py
import ezdxf
import os
import xml.etree.ElementTree as ET
from datetime import datetime

def gerar_dxf_base(comprimento, largura, saida_path, raios=None):
    """Gera um DXF base com o contorno da peça.

    O contorno padrão é um retângulo, mas é possível informar raios nos
    cantos através do dicionário ``raios``. As chaves aceitas são
    ``topLeft``, ``topRight``, ``bottomRight`` e ``bottomLeft``.
    """

    raios = raios or {}
    r_tl = float(raios.get("topLeft", 0))
    r_tr = float(raios.get("topRight", 0))
    r_br = float(raios.get("bottomRight", 0))
    r_bl = float(raios.get("bottomLeft", 0))

    doc = ezdxf.new()
    msp = doc.modelspace()
    layer = {"layer": "borda_externa"}

    # Borda inferior
    msp.add_line((r_bl, 0), (comprimento - r_br, 0), dxfattribs=layer)
    if r_br > 0:
        msp.add_arc(
            (comprimento - r_br, r_br),
            r_br,
            start_angle=-90,
            end_angle=0,
            dxfattribs=layer,
        )

    # Lado direito
    msp.add_line(
        (comprimento, r_br),
        (comprimento, largura - r_tr),
        dxfattribs=layer,
    )
    if r_tr > 0:
        msp.add_arc(
            (comprimento - r_tr, largura - r_tr),
            r_tr,
            start_angle=0,
            end_angle=90,
            dxfattribs=layer,
        )

    # Borda superior
    msp.add_line(
        (comprimento - r_tr, largura),
        (r_tl, largura),
        dxfattribs=layer,
    )
    if r_tl > 0:
        msp.add_arc(
            (r_tl, largura - r_tl),
            r_tl,
            start_angle=90,
            end_angle=180,
            dxfattribs=layer,
        )

    # Lado esquerdo
    msp.add_line((0, largura - r_tl), (0, r_bl), dxfattribs=layer)
    if r_bl > 0:
        msp.add_arc(
            (r_bl, r_bl),
            r_bl,
            start_angle=180,
            end_angle=270,
            dxfattribs=layer,
        )

    doc.saveas(saida_path)
    print(f"📄 Arquivo DXT gerado em: {saida_path}")

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
