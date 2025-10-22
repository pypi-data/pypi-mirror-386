"""
DGGRID to Geometry Module

This module provides functionality to convert DGGRID cell IDs to Shapely Polygons and GeoJSON FeatureCollection.

Key Functions:
    dggrid2geo: Convert DGGRID cell IDs to Shapely Polygons
    dggrid2geojson: Convert DGGRID cell IDs to GeoJSON FeatureCollection
    dggrid2geo_cli: Command-line interface for polygon conversion
    dggrid2geojson_cli: Command-line interface for GeoJSON conversion
"""

import json
import argparse

from dggrid4py import dggs_types
from dggrid4py.dggrid_runner import output_address_types
from vgrid.utils.io import (
    validate_dggrid_type,
    validate_dggrid_resolution,
    create_dggrid_instance,
)


def dggrid2geo(
    dggrid_instance, dggs_type, dggrid_ids, resolution=None, input_address_type="SEQNUM"
):
    """
    Convert DGGRID cell IDs to Shapely geometry objects.

    Accepts a single dggrid_id (string/int) or a list of dggrid_ids. For each valid DGGRID cell ID,
    creates a Shapely Polygon representing the grid cell boundaries. Skips invalid or
    error-prone cells.

    Parameters
    ----------
    dggrid_instance : object
        DGGRID instance for processing.
    dggs_type : str
        DGGRID DGGS type (e.g., "ISEA7H", "ISEA4T").
    dggrid_ids : str, int, or list of str/int
        DGGRID cell ID(s) to convert. Can be a single string/int or a list of strings/ints.
        Example format: "783229476878"
    resolution : int, optional
        Resolution level for the DGGS. If None, will be validated based on dggs_type.
    input_address_type : str, default "SEQNUM"
        Input address type for the cell IDs.

    Returns
    -------
    geopandas.GeoDataFrame
        A GeoDataFrame containing polygon geometries for each valid DGGRID cell.
        Each row includes:
        - geometry: Polygon representing the cell boundaries
        - dggrid_{dggs_type.lower()}: The original cell ID
        - resolution: The resolution level

    Examples
    --------
    >>> dggrid2geo(instance, "ISEA7H", "783229476878", 13)
    <geopandas.GeoDataFrame object at ...>

    >>> dggrid2geo(instance, "ISEA7H", ["783229476878", "783229476879"], 13)
    <geopandas.GeoDataFrame object at ...>
    """
    dggs_type = validate_dggrid_type(dggs_type)
    resolution = validate_dggrid_resolution(dggs_type, resolution)
    if isinstance(dggrid_ids, (str, int)):
        dggrid_ids = [dggrid_ids]

    # Convert from input_address_type to SEQNUM if needed
    if input_address_type and input_address_type != "SEQNUM":
        address_type_transform = dggrid_instance.address_transform(
            dggrid_ids,
            dggs_type=dggs_type,
            resolution=resolution,
            mixed_aperture_level=None,
            input_address_type=input_address_type,
            output_address_type="SEQNUM",
        )
        # Extract all SEQNUM values, not just the first one
        dggrid_ids = address_type_transform["SEQNUM"].tolist()

    dggrid_cells = dggrid_instance.grid_cell_polygons_from_cellids(
        dggrid_ids, dggs_type, resolution, split_dateline=True
    )

    # Convert global_id back to input_address_type if needed
    if input_address_type and input_address_type != "SEQNUM":
        # Get the SEQNUM values from global_id column
        seqnum_values = dggrid_cells["global_id"].tolist()

        # Transform back to input_address_type
        reverse_transform = dggrid_instance.address_transform(
            seqnum_values,
            dggs_type=dggs_type,
            resolution=resolution,
            mixed_aperture_level=None,
            input_address_type="SEQNUM",
            output_address_type=input_address_type,
        )

        # Replace global_id values with the original input_address_type values
        dggrid_cells["global_id"] = reverse_transform[input_address_type].values

    # Rename global_id column to dggrid_{dggs_type.lower()}
    dggrid_cells = dggrid_cells.rename(
        columns={"global_id": f"dggrid_{dggs_type.lower()}"}
    )
    # Add resolution property
    dggrid_cells["resolution"] = resolution

    return dggrid_cells


def dggrid2geo_cli():
    """
    Command-line interface for dggrid2geo supporting multiple DGGRID cell IDs.
    """
    parser = argparse.ArgumentParser(
        description="Convert DGGRID cell ID(s) to Shapely Polygons. \
                                     Usage: dggrid2geo <cell_ids> <dggs_type> <res> [input_address_type]. \
                                     Ex: dggrid2geo 783229476878 ISEA7H 13 SEQNUM"
    )
    parser.add_argument(
        "dggs_type",
        choices=dggs_types,
        help="Select a DGGS type from the available options.",
    )

    parser.add_argument("dggrid_ids", nargs="+", help="Input DGGRID cell ID(s)")

    parser.add_argument("resolution", type=int, help="resolution")
    parser.add_argument(
        "input_address_type",
        choices=output_address_types,
        default="SEQNUM",
        nargs="?",  # This makes the argument optional
        help="Select an input address type from the available options.",
    )

    args = parser.parse_args()
    dggrid_instance = create_dggrid_instance()
    polys = dggrid2geo(
        dggrid_instance,
        args.dggs_type,
        args.dggrid_ids,
        args.resolution,
        args.input_address_type,
    )
    return polys


def dggrid2geojson(
    dggrid_instance, dggs_type, dggrid_ids, resolution, input_address_type="SEQNUM"
):
    """
    Convert DGGRID cell IDs to GeoJSON FeatureCollection.

    Accepts a single dggrid_id (string/int) or a list of dggrid_ids. For each valid DGGRID cell ID,
    creates a GeoJSON feature with polygon geometry representing the grid cell boundaries.
    Skips invalid or error-prone cells.

    Parameters
    ----------
    dggrid_instance : object
        DGGRID instance for processing.
    dggs_type : str
        DGGRID DGGS type (e.g., "ISEA7H", "ISEA4T").
    dggrid_ids : str, int, or list of str/int
        DGGRID cell ID(s) to convert. Can be a single string/int or a list of strings/ints.
        Example format: "783229476878"
    resolution : int
        Resolution level for the DGGS.
    input_address_type : str, default "SEQNUM"
        Input address type for the cell IDs.

    Returns
    -------
    dict
        A GeoJSON FeatureCollection containing polygon features for each valid DGGRID cell.
        Each feature includes:
        - geometry: Polygon representing the cell boundaries
        - properties: Contains the DGGRID cell ID, resolution level, and cell metadata

    Examples
    --------
    >>> dggrid2geojson(instance, "ISEA7H", "783229476878", 13)
    {'type': 'FeatureCollection', 'features': [...]}

    >>> dggrid2geojson(instance, "ISEA7H", ["783229476878", "783229476879"], 13)
    {'type': 'FeatureCollection', 'features': [...]}
    """
    if isinstance(dggrid_ids, (str, int)):
        dggrid_ids = [dggrid_ids]

    # Get the GeoDataFrame from dggrid2geo
    gdf = dggrid2geo(
        dggrid_instance, dggs_type, dggrid_ids, resolution, input_address_type
    )
    # Convert GeoDataFrame to GeoJSON dictionary
    geojson_dict = json.loads(gdf.to_json())

    return geojson_dict


def dggrid2geojson_cli():
    """
    Command-line interface for dggrid2geojson supporting multiple DGGRID cell IDs.
    """
    parser = argparse.ArgumentParser(
        description="Convert DGGRID cell ID(s) to GeoJSON. \
                                     Usage: dggrid2geojson <cell_ids> <dggs_type> <res> [input_address_type]. \
                                     Ex: dggrid2geojson 783229476878 ISEA7H 13 SEQNUM"
    )

    parser.add_argument(
        "dggs_type",
        choices=dggs_types,
        help="Select a DGGS type from the available options.",
    )
    parser.add_argument("dggrid_ids", nargs="+", help="Input DGGRID cell ID(s)")
    parser.add_argument("resolution", type=int, help="resolution")
    parser.add_argument(
        "input_address_type",
        choices=output_address_types,
        default="SEQNUM",
        nargs="?",  # This makes the argument optional
        help="Select an input address type from the available options.",
    )

    args = parser.parse_args()
    dggrid_instance = create_dggrid_instance()
    geojson_data = json.dumps(
        dggrid2geojson(
            dggrid_instance,
            args.dggs_type,
            args.dggrid_ids,
            args.resolution,
            args.input_address_type,
        )
    )
    print(geojson_data)


if __name__ == "__main__":
    dggrid2geojson_cli()
