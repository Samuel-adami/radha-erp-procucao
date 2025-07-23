# coding: utf-8
"""Algoritmo de nesting utilizando heurística "IA".

Esta implementação usa a biblioteca ``rectpack`` para
alocar as peças inicialmente em sobras cadastradas e,
caso necessário, em novas chapas. As peças são tratadas
como polígonos e podem ser rotacionadas integralmente,
preservando as operações internas.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from rectpack import newPacker
from shapely import affinity
from shapely.geometry import Polygon, box


def _arranjar_poligonos_ia(
    pecas: List[Dict],
    largura: float,
    altura: float,
    espaco: float = 0.0,
    rotacionar: bool = True,
    estoque: Optional[List[Dict]] = None,
) -> List[List[Dict]]:
    """Arranja peças utilizando ``rectpack``.

    As sobras do estoque são usadas como bins iniciais. Cada peça
    é adicionada como um retângulo com ``espaco`` adicional para evitar
    colisões. O algoritmo respeita a rotação quando ``rotacionar`` for
    ``True``.
    """

    packer = newPacker(rotation=rotacionar)

    # Registrar peças
    for idx, p in enumerate(pecas):
        poly: Polygon = p.get("polygon") or box(0, 0, p.get("Length", 0), p.get("Width", 0))
        minx, miny, maxx, maxy = poly.bounds
        w = maxx - minx + espaco
        h = maxy - miny + espaco
        packer.add_rect(w, h, rid=idx)

    # Bins provenientes de sobras
    if estoque:
        for s in estoque:
            w = float(s.get("comprimento", largura))
            h = float(s.get("largura", altura))
            packer.add_bin(w, h, count=1)

    # Bin padrão para chapas novas (ilimitado)
    packer.add_bin(largura, altura)

    packer.pack()

    placas: List[List[Dict]] = []
    for abin in packer.bin_list():
        placa: List[Dict] = []
        for rect in abin:
            rid = rect.rid
            p = pecas[rid]
            rot = bool(rect.rotation)
            poly = p.get("polygon") or box(0, 0, p.get("Length", 0), p.get("Width", 0))
            g = affinity.rotate(poly, 90 if rot else 0, origin=(0, 0))
            minx, miny, maxx, maxy = g.bounds
            g = affinity.translate(g, rect.x - minx, rect.y - miny)
            novo = p.copy()
            novo.update(
                {
                    "x": rect.x,
                    "y": rect.y,
                    "Length": rect.width - espaco,
                    "Width": rect.height - espaco,
                    "polygon": g,
                    "rotated": rot,
                    "rotationAngle": 90 if rot else 0,
                }
            )
            placa.append(novo)
        if placa:
            placas.append(placa)
    return placas
