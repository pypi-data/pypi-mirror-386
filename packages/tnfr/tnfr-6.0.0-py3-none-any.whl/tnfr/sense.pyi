from __future__ import annotations

from collections.abc import Mapping
from typing import Optional

from .types import NodeId, SigmaVector, TNFRGraph

__all__: tuple[str, ...]

GLYPH_UNITS: dict[str, complex]

def glyph_angle(g: str) -> float: ...

def glyph_unit(g: str) -> complex: ...

def push_sigma_snapshot(G: TNFRGraph, t: Optional[float] = None) -> None: ...

def register_sigma_callback(G: TNFRGraph) -> None: ...

def sigma_rose(G: TNFRGraph, steps: Optional[int] = None) -> dict[str, int]: ...

def sigma_vector(dist: Mapping[str, float]) -> SigmaVector: ...

def sigma_vector_from_graph(
    G: TNFRGraph, weight_mode: Optional[str] = None
) -> SigmaVector: ...

def sigma_vector_node(
    G: TNFRGraph, n: NodeId, weight_mode: Optional[str] = None
) -> Optional[SigmaVector]: ...
