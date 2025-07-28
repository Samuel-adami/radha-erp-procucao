import json
import tempfile
import shutil
from pathlib import Path

from nesting import _encontrar_dxt, _ler_dxt


def gerar_seccionadora_preview(pasta_lote: str, largura_chapa: float, altura_chapa: float,
                               estoque_sel=None) -> list[list[dict]]:
    """
    Gera um preview simples de corte por guilhotina em chapas retangulares.
    Retorna uma lista de chapas, cada uma contendo itens posicionados como dicionários
    com chaves: x, y, width, height, Material.
    """
    pasta = Path(pasta_lote)
    dxt = _encontrar_dxt(pasta)
    if not dxt:
        raise FileNotFoundError("Arquivo DXT não encontrado para seccionadora")
    pecas = _ler_dxt(dxt)
    # Coleta retângulos (width, length) de cada peça
    items = []
    for p in pecas:
        try:
            w = float(p.get('Width', 0))
            h = float(p.get('Length', 0))
        except Exception:
            continue
        if w <= 0 or h <= 0:
            continue
        items.append({'width': w, 'height': h, 'Material': p.get('Material')})

    chapas = []
    # Algoritmo de guilhotina simplificado: empilha peças em colunas
    remaining = items.copy()
    while remaining:
        sheet = []
        y = 0.0
        to_remove = []
        # para cada item tenta inserir na chapa atual em colunas
        for it in remaining:
            if it['width'] <= largura_chapa and y + it['height'] <= altura_chapa:
                sheet.append({'x': 0.0, 'y': y,
                              'width': it['width'], 'height': it['height'],
                              'Material': it.get('Material')})
                y += it['height']
                to_remove.append(it)
        for it in to_remove:
            remaining.remove(it)
        chapas.append(sheet)
        # Separa em nova chapa se ainda houver itens
        if not to_remove:
            # Nenhum cabeu na chapa atual, evita laço infinito
            chapas[-1] = []
            break
    return chapas


def gerar_seccionadora(pasta_lote: str, largura_chapa: float, altura_chapa: float,
                       estoque_sel=None) -> tuple[str, list[list[dict]], list[list[dict]]]:
    """
    Executa corte por guilhotina definitivo, retornando pasta de saída,
    sobras (chapas restantes) e preview semelhante a gerar_seccionadora_preview.
    """
    preview = gerar_seccionadora_preview(pasta_lote, largura_chapa, altura_chapa, estoque_sel)
    pasta_saida = Path(pasta_lote).name
    pasta_resultado = Path(tempfile.mkdtemp(prefix=f"Seccionadora_{pasta_saida}_"))
    # Salva preview em JSON
    arquivo = pasta_resultado / "preview_seccionadora.json"
    with open(arquivo, 'w', encoding='utf-8') as f:
        json.dump(preview, f)
    # Calcula sobras como chapas sem itens posicionados
    sobras = [sheet for sheet in preview if not sheet]
    return str(pasta_resultado), sobras, preview
