"""Simplified wrapper for the Packaide nesting engine.

This module attempts to provide a minimal integration layer for
`Packaide` so it can be used transparently by the existing nesting
functions.  If the third party library is not available the code falls
back to a very naive rectangle packing algorithm implemented with
`shapely` merely to keep the service functional during development.

The wrapper exposes a single function ``pack`` which receives a list of
pieces (dictionaries with ``Length`` and ``Width``) and returns a list of
bins with placement information compatible with ``rectpack`` objects.

When ``packaide`` is not installed as a Python package the module attempts
to load it from ``externals/Packaide`` under the repository root.  If the
library is still missing a simplified heuristic algorithm is used instead.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Dict, Tuple
from pathlib import Path
import importlib
import sys

try:  # pragma: no cover - optional dependency
    import packaide  # type: ignore
except Exception:  # pragma: no cover - import failure handled at runtime
    packaide = None
    _ext_dir = Path(__file__).resolve().parents[3] / "externals" / "Packaide"
    if _ext_dir.exists():
        sys.path.append(str(_ext_dir))
        try:
            packaide = importlib.import_module("packaide")  # type: ignore
        except Exception:
            packaide = None

from shapely.geometry import box
from shapely import affinity


@dataclass
class Placement:
    """Represents a positioned piece on the plate."""

    x: float
    y: float
    width: float
    height: float
    rid: Dict
    rotated: bool = False


class Bin(list):
    """Simple container mirroring ``rectpack`` bin interface."""

    width: float
    height: float

    def __init__(self, width: float, height: float, placements: Iterable[Placement] | None = None) -> None:
        super().__init__(placements or [])
        self.width = width
        self.height = height


# ---------------------------------------------------------------------------
# Naive fallback algorithm
# ---------------------------------------------------------------------------

def _naive_pack(
    pieces: List[Dict],
    bin_width: float,
    bin_height: float,
    rotation: bool = True,
) -> List[Bin]:
    """Very small heuristic packing used when Packaide is unavailable."""
    bins: List[Bin] = []
    current = Bin(bin_width, bin_height)
    x = y = 0.0
    row_h = 0.0

    def new_bin() -> None:
        nonlocal current, x, y, row_h
        if current:
            bins.append(current)
        current = Bin(bin_width, bin_height)
        x = y = 0.0
        row_h = 0.0

    for p in pieces:
        w = float(p.get("Length", 0))
        h = float(p.get("Width", 0))
        rot = False
        if rotation and h > w and h <= bin_width and w <= bin_height:
            w, h = h, w
            rot = True
        if x + w > bin_width:
            x = 0
            y += row_h
            row_h = 0
        if y + h > bin_height:
            new_bin()
        current.append(Placement(x, y, w, h, p, rot))
        x += w
        row_h = max(row_h, h)
    if current:
        bins.append(current)
    return bins


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def pack(
    pieces: List[Dict],
    bin_width: float,
    bin_height: float,
    rotation: bool = True,
    rotation_step: int = 90,
) -> List[Bin]:
    """Pack pieces using Packaide when available.

    When the third party library is missing a simplified heuristic is
    employed so that the nesting process can still run albeit with lower
    efficiency.
    """

    if packaide is not None:  # pragma: no cover - external dependency
        # NOTE: The real implementation depends on the Packaide API which is
        # not available in this environment.  The call below reflects the
        # expected usage but may require adjustments when the library is
        # properly installed.
        engine = packaide.NestingEngine(  # type: ignore[attr-defined]
            width=bin_width,
            height=bin_height,
            rotation_step=rotation_step,
            allow_rotation=rotation,
        )
        for p in pieces:
            poly = box(0, 0, p["Length"], p["Width"])
            engine.add_shape(poly, rid=p)  # type: ignore[attr-defined]
        bins: List[Bin] = []
        for plate in engine.execute():  # type: ignore[attr-defined]
            placements = [
                Placement(
                    pl.x,
                    pl.y,
                    pl.width,
                    pl.height,
                    pl.rid,
                    getattr(pl, "rotated", False),
                )
                for pl in plate
            ]
            bins.append(Bin(bin_width, bin_height, placements))
        return bins

    # Fallback for development without Packaide
    return _naive_pack(pieces, bin_width, bin_height, rotation)
