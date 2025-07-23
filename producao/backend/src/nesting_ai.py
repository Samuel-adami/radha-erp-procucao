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

    # Inicializa lista de placas com a quantidade de bins utilizados
    num_bins = len(packer.bin_list())
    placas = [[] for _ in range(num_bins)]

    for bin_id, x, y, w, h, rid in packer.rect_list():
        p = pecas[rid]
        poly = p.get("polygon") or box(0, 0, p.get("Length", 0), p.get("Width", 0))
        minx, miny, maxx, maxy = poly.bounds
        orig_w = maxx - minx
        orig_h = maxy - miny

        # Detectar se houve rotacao comparando com dimensoes originais
        rot = False
        if rotacionar and abs(orig_w + espaco - h) < 1e-6 and abs(orig_h + espaco - w) < 1e-6:
            rot = True

        g = affinity.rotate(poly, 90 if rot else 0, origin=(0, 0))
        minx, miny, maxx, maxy = g.bounds
        g = affinity.translate(g, x - minx, y - miny)

        novo = p.copy()
        novo.update(
            {
                "x": x,
                "y": y,
                "Length": w - espaco,
                "Width": h - espaco,
                "polygon": g,
                "rotated": rot,
                "rotationAngle": 90 if rot else 0,
            }
        )
        placas[bin_id].append(novo)

    # Remove placas vazias
    placas = [p for p in placas if p]

    return placas
