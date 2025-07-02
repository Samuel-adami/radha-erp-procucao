# leitor_dxf.py
import ezdxf

def aplicar_usinagem_retangular(caminho_entrada, caminho_saida, cmd, info_peca):
    doc = ezdxf.readfile(caminho_entrada)
    msp = doc.modelspace()

    # --- LÓGICA ATUALIZADA ---
    # Adicionado 'Linha' à condição para que seja tratada como um retângulo.
    if cmd['tipo'] in ['Retângulo', 'Linha']:
        x = float(cmd['x'])
        y = float(cmd['y'])
        w = float(cmd['comprimento'])
        h = float(cmd['largura'])
        profundidade = float(cmd['profundidade'])
        estrategia = cmd['estrategia']
        prefixo = cmd.get('prefixo', 'USINAR')
        layer_nome = f"{prefixo}_{profundidade}_{estrategia}"

        pontos = [
            (x, y),
            (x + w, y),
            (x + w, y + h),
            (x, y + h),
            (x, y)
        ]
        pl = msp.add_polyline2d(pontos, dxfattribs={"layer": layer_nome})
        pl.close(True)

    elif cmd['tipo'] == 'Círculo':
        x = float(cmd['x'])
        y = float(cmd['y'])
        diametro = float(cmd['diametro'])
        profundidade = float(cmd['profundidade'])
        estrategia = cmd['estrategia']
        prefixo = cmd.get('prefixo', 'USINAR')
        layer_nome = f"{prefixo}_{profundidade}_{estrategia}"
        raio = diametro / 2
        msp.add_circle((x, y), raio, dxfattribs={"layer": layer_nome})

    elif cmd['tipo'] == 'Furo':
        x = float(cmd['x'])
        y = float(cmd['y'])
        diametro = float(cmd['diametro'])
        profundidade = float(cmd['profundidade'])
        layer_nome = f"FURO_{diametro}_{profundidade}"
        raio = diametro / 2
        msp.add_circle((x, y), raio, dxfattribs={"layer": layer_nome})

    doc.saveas(caminho_saida)


def gerar_dxf_base(nome_arquivo, largura, altura, caminho_saida):
    doc = ezdxf.new(setup=True)
    msp = doc.modelspace()
    pontos = [
        (0, 0),
        (largura, 0),
        (largura, altura),
        (0, altura),
        (0, 0)
    ]
    pl = msp.add_polyline2d(pontos, dxfattribs={"layer": "CONTORNO"})
    pl.close(True)
    doc.saveas(caminho_saida)
