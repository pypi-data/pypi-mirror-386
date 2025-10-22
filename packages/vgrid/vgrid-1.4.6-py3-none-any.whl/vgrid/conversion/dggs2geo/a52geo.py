"""
A5 to Geometry Module

This module provides functionality to convert A5 cell IDs to Shapely Polygons and GeoJSON FeatureCollection.

Key Functions:
    a52geo: Convert A5 cell IDs to Shapely Polygons
    a52geojson: Convert A5 cell IDs to GeoJSON FeatureCollection
    a52geo_cli: Command-line interface for polygon conversion
    a52geojson_cli: Command-line interface for GeoJSON conversion
"""

import json
import argparse
import a5
from shapely.geometry import Polygon
from vgrid.utils.geometry import geodesic_dggs_to_feature


def a52geo(a5_hexes, options=None):
    """
    Convert A5 cell IDs to Shapely geometry objects.

    Accepts a single a5_id (string or int) or a list of a5_ids. For each valid A5 cell ID,
    creates a Shapely Polygon representing the grid cell boundaries. Skips invalid or
    error-prone cells.

    Parameters
    ----------
    a5_hexes : str, int, or list of str/int
        A5 cell ID(s) to convert. Can be a single string/int or a list of strings/ints.
        Example format: "8e65b56628e0d07"

    Returns
    -------
    shapely.geometry.Polygon or list of shapely.geometry.Polygon
        If a single A5 cell ID is provided, returns a single Shapely Polygon object.
        If a list of IDs is provided, returns a list of Shapely Polygon objects.
        Each polygon represents the boundaries of the corresponding A5 cell.

    Examples
    --------
    >>> a52geo("8e65b56628e0d07")
    <shapely.geometry.polygon.Polygon object at ...>

    >>> a52geo(["8e65b56628e0d07", "8e65b56628e6adf"])
    [<shapely.geometry.polygon.Polygon object at ...>, <shapely.geometry.polygon.Polygon object at ...>]
    """
    if isinstance(a5_hexes, str):
        a5_hexes = [a5_hexes]
    a5_polygons = []
    for a5_hex in a5_hexes:
        try:
            cell_u64 = a5.hex_to_u64(a5_hex)
            # options = {"segments": 1000}
            cell_boundary = a5.cell_to_boundary(cell_u64, options)  # testing equal area
            cell_polygon = Polygon(cell_boundary)
            a5_polygons.append(cell_polygon)
        except Exception:
            continue
    if len(a5_polygons) == 1:
        return a5_polygons[0]
    return a5_polygons


def a52geo_cli():
    """
    Command-line interface for a52geo supporting multiple a5 cell IDs.
    """
    parser = argparse.ArgumentParser(
        description="Convert a5 cell ID(s) to Shapely Polygons"
    )
    parser.add_argument(
        "a5",
        nargs="+",
        help="Input a5 cell ID(s), e.g., a52geo 8e65b56628e0d07 8e65b56628e6adf",
    )
    args = parser.parse_args()
    polys = a52geo(args.a5)
    return polys


def a52geojson(a5_hexes, options=None):
    """
    Convert A5 cell IDs to GeoJSON FeatureCollection.

    Accepts a single a5_id (string or int) or a list of a5_ids. For each valid A5 cell ID,
    creates a GeoJSON feature with polygon geometry representing the grid cell boundaries.
    Skips invalid or error-prone cells.

    Parameters
    ----------
    a5_hexes : str, int, or list of str/int
        A5 cell ID(s) to convert. Can be a single string/int or a list of strings/ints.
        Example format: "8e65b56628e0d07"

    Returns
    -------
    dict
        A GeoJSON FeatureCollection containing polygon features for each valid A5 cell.
        Each feature includes:
        - geometry: Polygon representing the cell boundaries
        - properties: Contains the A5 cell ID, resolution level, and cell metadata

    Examples
    --------
    >>> a52geojson("8e65b56628e0d07")
    {'type': 'FeatureCollection', 'features': [...]}

    >>> a52geojson(["8e65b56628e0d07", "8e65b56628e6adf"])
    {'type': 'FeatureCollection', 'features': [...]}
    """
    # Handle single input (string or int)
    if isinstance(a5_hexes, str):
        a5_hexes = [a5_hexes]

    a5_features = []
    for a5_hex in a5_hexes:
        try:
            cell_polygon = a52geo(a5_hex, options)
            num_edges = 5
            resolution = a5.get_resolution(a5.hex_to_u64(a5_hex))
            a5_feature = geodesic_dggs_to_feature(
                "a5", a5_hex, resolution, cell_polygon, num_edges
            )
            a5_features.append(a5_feature)
        except Exception:
            continue
    return {"type": "FeatureCollection", "features": a5_features}


def a52geojson_cli():
    """
    Command-line interface for a52geojson supporting multiple A5 cell hex.
    """
    parser = argparse.ArgumentParser(description="Convert A5 cell hex to GeoJSON")
    parser.add_argument(
        "a5",
        nargs="+",
        help="Input a5 cell hex, e.g., a52geojson 8e65b56628e0d07 8e65b56628e6adf",
    )
    args = parser.parse_args()
    geojson_data = json.dumps(a52geojson(args.a5))
    print(geojson_data)


if __name__ == "__main__":
    a52geojson_cli()
