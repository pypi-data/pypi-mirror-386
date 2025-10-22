# Import all constants and VGRID class from VGRID.py
from .VGRID import (
    HIERARCHY_LEVEL_BITS,
    HIERARCHY_LEVEL_MASK,
    MAX_HIERARCHY_LEVEL,
    TILE_INDEX_BITS,
    TILE_INDEX_MASK,
    MAX_TILE_INDEX,
    OBJECT_INDEX_BITS,
    OBJECT_INDEX_MASK,
    MAX_OBJECT_INDEX,
    VGRID,
)

# Export everything for easy access
__all__ = [
    "HIERARCHY_LEVEL_BITS",
    "HIERARCHY_LEVEL_MASK",
    "MAX_HIERARCHY_LEVEL",
    "TILE_INDEX_BITS",
    "TILE_INDEX_MASK",
    "MAX_TILE_INDEX",
    "OBJECT_INDEX_BITS",
    "OBJECT_INDEX_MASK",
    "MAX_OBJECT_INDEX",
    "VGRID",
]
