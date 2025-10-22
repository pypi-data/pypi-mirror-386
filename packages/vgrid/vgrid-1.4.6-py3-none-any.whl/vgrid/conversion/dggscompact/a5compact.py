"""
A5 Compact Module

This module provides functionality to compact and expand A5 cells with flexible input and output formats.

Key Functions:
    a5compact: Compact a set of A5 cells to their minimal covering set
    a5expand: Expand (uncompact) a set of A5 cells to a target resolution
    a5compact_cli: Command-line interface for compaction
    a5expand_cli: Command-line interface for expansion
"""

import os
import argparse
import geopandas as gpd
from collections import defaultdict
import a5
from vgrid.conversion.dggs2geo.a52geo import a52geo
from vgrid.utils.geometry import geodesic_dggs_to_geoseries
from vgrid.utils.io import (
    process_input_data_compact,
    convert_to_output_format,
    validate_a5_resolution,
)
from vgrid.utils.constants import OUTPUT_FORMATS, STRUCTURED_FORMATS


# --- A5 Compaction Logic ---
def a5_compact(a5_hexes):
    """
    Compact a list of A5 cell IDs to their minimal covering set.

    Groups A5 cells by their parents and replaces complete sets of children
    with their parent cells, repeating until no more compaction is possible.

    Parameters
    ----------
    a5_hexes : list of str
        List of A5 hex cell IDs to compact.

    Returns
    -------
    list of str
        Sorted list of compacted A5 cell IDs representing the minimal covering set.

    Examples
    --------
    >>> a5_hexes = ["8e65b56628e0d07", "8e65b56628e0d08", "8e65b56628e0d09"]
    >>> compacted = a5_compact(a5_hexes)
    >>> print(f"Compacted {len(a5_hexes)} cells to {len(compacted)} cells")
    """

    a5_hexes = set(a5_hexes)  # Remove duplicates

    # Main compaction loop
    while True:
        grouped_by_parent = defaultdict(set)

        # Group cells by their parent
        for a5_hex in a5_hexes:
            try:
                parent = a5.cell_to_parent(a5.hex_to_u64(a5_hex))
                if parent is not None:
                    grouped_by_parent[parent].add(a5_hex)
            except Exception:
                # Skip cells that can't be processed
                continue

        new_a5_hexes = set(a5_hexes)
        changed = False

        # Check if we can replace children with parent
        for parent_u64, children_hexes in grouped_by_parent.items():
            try:
                # Get the resolution of the parent
                parent_resolution = a5.get_resolution(parent_u64)
                next_resolution = parent_resolution + 1

                # Get all children of the parent at the next resolution
                expected_children = set()
                children_u64s = a5.cell_to_children(parent_u64, next_resolution)
                if children_u64s:
                    expected_children = {
                        a5.u64_to_hex(child) for child in children_u64s
                    }

                # Check if all expected children are present
                if children_hexes == expected_children and len(expected_children) > 0:
                    # Replace children with parent
                    new_a5_hexes.difference_update(children_hexes)  # Remove children
                    new_a5_hexes.add(a5.u64_to_hex(parent_u64))  # Add parent
                    changed = True

            except Exception:
                # If we can't process this parent, keep the original children
                continue

        if not changed:
            break  # No more compaction possible

        a5_hexes = new_a5_hexes

    return sorted(a5_hexes)


def a5_expand(a5_hexes, resolution):
    """
    Expand a list of A5 cells to the target resolution.

    Takes A5 cells and expands them to their children at the specified resolution.

    Parameters
    ----------
    a5_hexes : list of str
        List of A5 hex cell IDs to expand.
    resolution : int
        Target resolution to expand the cells to.

    Returns
    -------
    list of str
        List of expanded A5 cell IDs at the target resolution.

    Examples
    --------
    >>> a5_hexes = ["8e65b56628e0d07"]
    >>> expanded = a5_expand(a5_hexes, 5)
    >>> print(f"Expanded to {len(expanded)} cells at resolution 5")
    """
    expanded_cells = []
    for a5_hex in a5_hexes:
        children = a5.cell_to_children(a5.hex_to_u64(a5_hex), resolution)
        if children:
            expanded_cells.extend(a5.u64_to_hex(child) for child in children)
        else:
            # If we can't get children, keep the original cell
            expanded_cells.append(a5_hex)
    return expanded_cells


def a5compact(
    input_data,
    a5_hex=None,
    output_format="gpd",
    options=None,
):
    """
    Compact A5 cells to their minimal covering set.

    Compacts a set of A5 cells by replacing complete sets of children with their parent cells,
    repeating until no more compaction is possible. Supports flexible input and output formats.

    Parameters
    ----------
    input_data : str, dict, geopandas.GeoDataFrame, or list
        Input data containing A5 cell IDs. Can be:
        - File path (GeoJSON, Shapefile, CSV, Parquet)
        - URL to a file
        - GeoJSON dictionary
        - GeoDataFrame
        - List of A5 cell IDs
    a5_hex : str, optional
        Name of the column containing A5 cell IDs. Defaults to "a5".
    output_format : str, default "gpd"
        Output format. Options:
        - "gpd": Returns GeoPandas GeoDataFrame (default)
        - "csv": Returns CSV file path
        - "geojson": Returns GeoJSON file path
        - "geojson_dict": Returns GeoJSON FeatureCollection as Python dict
        - "parquet": Returns Parquet file path
        - "shapefile"/"shp": Returns Shapefile file path
        - "gpkg"/"geopackage": Returns GeoPackage file path
    options : dict, optional
        Options for a52geo.
    Returns
    -------
    geopandas.GeoDataFrame or str or dict or None
        The compacted A5 cells in the specified format, or None if no valid cells found.

    Examples
    --------
    >>> # Compact from file
    >>> result = a5compact("cells.geojson")
    >>> print(f"Compacted to {len(result)} cells")

    >>> # Compact from list
    >>> result = a5compact(["8e65b56628e0d07", "8e65b56628e0d08"])

    >>> # Compact to GeoJSON file
    >>> result = a5compact("cells.geojson", output_format="geojson")
    >>> print(f"Saved to: {result}")
    """
    if not a5_hex:
        a5_hex = "a5"
    gdf = process_input_data_compact(input_data, a5_hex)
    a5_hexes = gdf[a5_hex].drop_duplicates().tolist()
    if not a5_hexes:
        print(f"No A5 IDs found in <{a5_hex}> field.")
        return
    try:
        a5_hexes_compact = a5_compact(a5_hexes)
    except Exception:
        raise Exception("Compact cells failed. Please check your A5 ID field.")
    if not a5_hexes_compact:
        return None
    rows = []
    for a5_hex_compact in a5_hexes_compact:
        try:
            cell_polygon = a52geo(a5_hex_compact, options)
            cell_resolution = a5.get_resolution(a5.hex_to_u64(a5_hex_compact))
            num_edges = 5  # A5 cells are pentagons
            row = geodesic_dggs_to_geoseries(
                "a5", a5_hex_compact, cell_resolution, cell_polygon, num_edges
            )
            rows.append(row)
        except Exception:
            continue
    out_gdf = gpd.GeoDataFrame(rows, geometry="geometry", crs="EPSG:4326")
    ouput_name = None
    if output_format in OUTPUT_FORMATS:
        if isinstance(input_data, str):
            base = os.path.splitext(os.path.basename(input_data))[0]
            ouput_name = f"{base}_a5_compacted"
        else:
            ouput_name = "a5_compacted"
    return convert_to_output_format(out_gdf, output_format, ouput_name)


def a5compact_cli():
    """
    Command-line interface for a5compact with flexible input/output.
    """
    parser = argparse.ArgumentParser(description="A5 Compact")
    parser.add_argument(
        "-i",
        "--input",
        type=str,
        required=True,
        help="Input A5 (GeoJSON, Shapefile, CSV, Parquet, or pickled GeoDataFrame .gpd/.geopandas)",
    )
    parser.add_argument("-cellid", "--cellid", type=str, help="A5 Hex field")
    parser.add_argument(
        "-f", "--output_format", type=str, default="gpd", choices=OUTPUT_FORMATS
    )

    args = parser.parse_args()
    input_data = args.input
    cellid = args.cellid
    output_format = args.output_format
    result = a5compact(
        input_data,
        a5_hex=cellid,
        output_format=output_format,
    )
    if output_format in STRUCTURED_FORMATS:
        print(result)


def a5expand(
    input_data,
    resolution,
    a5_hex=None,
    output_format="gpd",
    options=None,
):
    """
    Expand (uncompact) A5 cells to a target resolution.

    Expands A5 cells to their children at the specified resolution. The target resolution
    must be greater than or equal to the maximum resolution of the input cells.

    Parameters
    ----------
    input_data : str, dict, geopandas.GeoDataFrame, or list
        Input data containing A5 cell IDs. Can be:
        - File path (GeoJSON, Shapefile, CSV, Parquet)
        - URL to a file
        - GeoJSON dictionary
        - GeoDataFrame
        - List of A5 cell IDs
    resolution : int
        Target A5 resolution to expand the cells to. Must be >= maximum input resolution.
    a5_hex : str, optional
        Name of the column containing A5 cell IDs. Defaults to "a5".
    output_format : str, default "gpd"
        Output format. Options:
        - "gpd": Returns GeoPandas GeoDataFrame (default)
        - "csv": Returns CSV file path
        - "geojson": Returns GeoJSON file path
        - "geojson_dict": Returns GeoJSON FeatureCollection as Python dict
        - "parquet": Returns Parquet file path
        - "shapefile"/"shp": Returns Shapefile file path
        - "gpkg"/"geopackage": Returns GeoPackage file path
    options : dict, optional
        Options for a52geo.
    Returns
    -------
    geopandas.GeoDataFrame or str or dict or None
        The expanded A5 cells in the specified format, or None if expansion fails.

    Examples
    --------
    >>> # Expand from file
    >>> result = a5expand("cells.geojson", resolution=5)
    >>> print(f"Expanded to {len(result)} cells")

    >>> # Expand from list
    >>> result = a5expand(["8e65b56628e0d07"], resolution=5)

    >>> # Expand to GeoJSON file
    >>> result = a5expand("cells.geojson", resolution=5, output_format="geojson")
    >>> print(f"Saved to: {result}")
    """
    if a5_hex is None:
        a5_hex = "a5"
    resolution = validate_a5_resolution(resolution)
    gdf = process_input_data_compact(input_data, a5_hex)
    a5_hexes = gdf[a5_hex].drop_duplicates().tolist()
    if not a5_hexes:
        print(f"No A5 Hexes found in <{a5_hex}> field.")
        return
    try:
        max_res = max(a5.get_resolution(a5.hex_to_u64(a5_hex)) for a5_hex in a5_hexes)
        if resolution < max_res:
            print(f"Target expand resolution ({resolution}) must >= {max_res}.")
            return None
        a5_hexes_expand = a5_expand(a5_hexes, resolution)
    except Exception:
        raise Exception(
            "Expand cells failed. Please check your A5 ID field and resolution."
        )
    if not a5_hexes_expand:
        return None
    rows = []
    for a5_hex_expand in a5_hexes_expand:
        try:
            cell_polygon = a52geo(a5_hex_expand, options)
            cell_resolution = resolution
            num_edges = 5  # A5 cells are pentagons
            row = geodesic_dggs_to_geoseries(
                "a5", a5_hex_expand, cell_resolution, cell_polygon, num_edges
            )
            rows.append(row)
        except Exception:
            continue
    out_gdf = gpd.GeoDataFrame(rows, geometry="geometry", crs="EPSG:4326")
    ouput_name = None
    if output_format in OUTPUT_FORMATS:
        if isinstance(input_data, str):
            base = os.path.splitext(os.path.basename(input_data))[0]
            ouput_name = f"{base}_a5_expanded"
        else:
            ouput_name = "a5_expanded"
    return convert_to_output_format(out_gdf, output_format, ouput_name)


def a5expand_cli():
    """
    Command-line interface for a5expand with flexible input/output.
    """
    parser = argparse.ArgumentParser(description="A5 Expand (Uncompact)")
    parser.add_argument(
        "-i",
        "--input",
        type=str,
        required=True,
        help="Input A5 (GeoJSON, Shapefile, CSV, Parquet, or pickled GeoDataFrame .gpd/.geopandas)",
    )
    parser.add_argument(
        "-r",
        "--resolution",
        type=int,
        required=True,
        help="Target A5 resolution to expand to (must be greater than input cells)",
    )
    parser.add_argument("-cellid", "--cellid", type=str, help="A5 Hex field")
    parser.add_argument(
        "-f",
        "--output_format",
        type=str,
        default="gpd",
        choices=OUTPUT_FORMATS,
        help="Output format",
    )
    parser.add_argument("-cellid", "--cellid", type=str, help="A5 Hex field")

    args = parser.parse_args()
    input_data = args.input
    resolution = args.resolution
    cellid = args.cellid
    output_format = args.output_format
    result = a5expand(
        input_data,
        resolution,
        a5_hex=cellid,
        output_format=output_format,
    )
    if output_format in STRUCTURED_FORMATS:
        print(result)
