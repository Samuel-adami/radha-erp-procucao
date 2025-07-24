"""
Integração inicial com svgnest-python para nesting poligonal.

Use svgnest para gerar um nesting poligonal em SVG, depois extraia as posições
dos objetos para converter em coordenadas de corte.

Para instalar:
    pip install svgnest

Passos gerais:
1. Converta cada polígono de peça em elementos <path> ou <rect> em um SVG.
2. Chame svgnest.nest() passando o SVG das peças e da chapa.
3. Recupere o SVG de saída e extraia as transformações (x/y/rotate).
4. Converta em lista de dicts compatíveis com _arranjar_poligonos_ia.

Por ora esta função é um stub que deve ser implementado.
"""
from typing import List, Dict, Optional

def arranjar_poligonos_svgnest(
    pecas: List[Dict],
    largura: float,
    altura: float,
    espaco: float = 0.0,
    rotacionar: bool = True,
    estoque: Optional[List[Dict]] = None,
) -> List[List[Dict]]:
    """Stub para nesting via svgnest-python.

    Retorna listas de chapas com posições de peças sem sobreposição.
    Substitua esta implementação pelo uso de svgnest.nest() real.
    """
    raise NotImplementedError("arranjar_poligonos_svgnest não implementado")
