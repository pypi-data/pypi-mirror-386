"""
Raster to QTM Module

This module provides functionality to convert raster data to QTM (Quaternary Triangular Mesh) DGGS format with automatic resolution determination and multi-band support.

Key Functions:
    raster2qtm: Main conversion function with multiple output formats
    get_nearest_qtm_resolution: Automatically determines optimal QTM resolution
    raster2qtm_cli: Command-line interface for conversion process
"""

import os
import argparse
from math import cos, radians
from tqdm import tqdm
from vgrid.stats.qtmstats import qtm_metrics
from vgrid.conversion.latlon2dggs import latlon2qtm
from vgrid.conversion.dggs2geo.qtm2geo import qtm2geo
from vgrid.utils.io import validate_qtm_resolution, convert_to_output_format
from vgrid.utils.constants import (
    OUTPUT_FORMATS,
    STRUCTURED_FORMATS,
    DGGS_TYPES,
    MIN_CELL_AREA,
)
import geopandas as gpd
from pyproj import datadir

os.environ["PROJ_LIB"] = datadir.get_data_dir()
import rasterio

min_res = DGGS_TYPES["qtm"]["min_res"]
max_res = DGGS_TYPES["qtm"]["max_res"]


def get_nearest_qtm_resolution(raster_path):
    """
    Automatically determine the optimal QTM resolution for a given raster.

    Analyzes the raster's pixel size and determines the most appropriate QTM resolution
    that best matches the raster's spatial resolution.

    Parameters
    ----------
    raster_path : str
        Path to the raster file to analyze.

    Returns
    -------
    tuple
        A tuple containing (cell_size, resolution) where:
        - cell_size: The calculated cell size in square meters
        - resolution: The optimal QTM resolution level

    Examples
    --------
    >>> cell_size, resolution = get_nearest_qtm_resolution("data.tif")
    >>> print(f"Cell size: {cell_size} m², Resolution: {resolution}")
    Cell size: 1000000.0 m², Resolution: 5
    """
    with rasterio.open(raster_path) as src:
        transform = src.transform
        crs = src.crs
        pixel_width = transform.a
        pixel_height = -transform.e
        cell_size = pixel_width * pixel_height

        if crs.is_geographic:
            # Latitude of the raster center
            center_latitude = (src.bounds.top + src.bounds.bottom) / 2
            # Convert degrees to meters
            meter_per_degree_lat = 111_320  # Roughly 1 degree latitude in meters
            meter_per_degree_lon = meter_per_degree_lat * cos(radians(center_latitude))

            pixel_width_m = pixel_width * meter_per_degree_lon
            pixel_height_m = pixel_height * meter_per_degree_lat
            cell_size = pixel_width_m * pixel_height_m

    min_diff = float("inf")
    nearest_resolution = min_res

    for res in range(min_res, max_res + 1):
        _, _, avg_area, _ = qtm_metrics(res)
        if avg_area < MIN_CELL_AREA:
            break
        diff = abs(avg_area - cell_size)
        # If the difference is smaller than the current minimum, update the nearest resolution
        if diff < min_diff:
            min_diff = diff
            nearest_resolution = res

    return cell_size, nearest_resolution


def raster2qtm(raster_path, resolution=None, output_format="gpd"):
    """
    Convert raster data to QTM DGGS format.

    Converts raster data to QTM (Quaternary Triangular Mesh) DGGS format with automatic resolution
    determination and multi-band support. Each pixel is assigned to a QTM cell and
    the first sample value per cell is preserved.

    Parameters
    ----------
    raster_path : str
        Path to the raster file to convert.
    resolution : int, optional
        QTM resolution level. If None, automatically determined based on raster pixel size.
        Valid range: 1-30.
    output_format : str, default "gpd"
        Output format. Options:
        - "gpd": Returns GeoPandas GeoDataFrame (default)
        - "csv": Returns CSV file path
        - "geojson": Returns GeoJSON file path
        - "geojson_dict": Returns GeoJSON FeatureCollection as Python dict
        - "parquet": Returns Parquet file path
        - "shapefile"/"shp": Returns Shapefile file path
        - "gpkg"/"geopackage": Returns GeoPackage file path

    Returns
    -------
    geopandas.GeoDataFrame or str or dict
        The converted data in the specified format. Each row represents a QTM cell
        with geometry and band values from the original raster.

    Examples
    --------
    >>> # Convert with automatic resolution
    >>> result = raster2qtm("data.tif")
    >>> print(f"Converted {len(result)} QTM cells")

    >>> # Convert with specific resolution
    >>> result = raster2qtm("data.tif", resolution=10)

    >>> # Convert to GeoJSON file
    >>> result = raster2qtm("data.tif", output_format="geojson")
    >>> print(f"Saved to: {result}")
    """
    # Step 1: Determine the nearest qtm resolution if none is provided
    if resolution is None:
        cell_size, resolution = get_nearest_qtm_resolution(raster_path)
        print(f"Cell size: {cell_size} m2")
        print(f"Nearest QTM resolution determined: {resolution}")
    else:
        resolution = validate_qtm_resolution(resolution)
    # Open the raster file to get metadata and data
    with rasterio.open(raster_path) as src:
        raster_data = src.read()  # Read all bands
        transform = src.transform
        width, height = src.width, src.height
        band_count = src.count  # Number of bands in the raster

    # Collect band values during the pixel scan, storing the first sample per QTM cell
    qtm_band_values = {}
    for row in range(height):
        for col in range(width):
            lon, lat = transform * (col, row)
            qtm_id = latlon2qtm(lat, lon, resolution)
            if qtm_id not in qtm_band_values:
                vals = raster_data[:, int(row), int(col)]
                qtm_band_values[qtm_id] = [
                    (v.item() if hasattr(v, "item") else v) for v in vals
                ]

    # Always convert to GeoDataFrame for output
    # Build GeoDataFrame
    properties = []
    for qtm_id, band_values in tqdm(
        qtm_band_values.items(), desc="Converting raster to QTM", unit=" cells"
    ):
        cell_polygon = qtm2geo(qtm_id)
        base_props = {"qtm": qtm_id, "geometry": cell_polygon}
        band_props = {f"band_{i + 1}": band_values[i] for i in range(band_count)}
        base_props.update(band_props)
        properties.append(base_props)
    gdf = gpd.GeoDataFrame(properties, geometry="geometry", crs="EPSG:4326")

    # Use centralized output utility
    base_name = os.path.splitext(os.path.basename(raster_path))[0]
    output_name = f"{base_name}2qtm" if output_format is not None else None
    return convert_to_output_format(gdf, output_format, output_name)


def raster2qtm_cli():
    """Command line interface for raster2qtm conversion"""
    parser = argparse.ArgumentParser(
        description="Convert Raster in Geographic CRS to QTM DGGS"
    )
    parser.add_argument("-raster", type=str, required=True, help="Raster file path")
    parser.add_argument(
        "-r",
        "--resolution",
        type=int,
        required=False,
        default=None,
        help=f"QTM resolution [{min_res}..{max_res}]",
    )
    parser.add_argument(
        "-f",
        "--output_format",
        type=str,
        choices=OUTPUT_FORMATS,
        default="gpd",
    )

    args = parser.parse_args()
    raster = args.raster
    resolution = args.resolution
    output_format = args.output_format

    if not os.path.exists(raster):
        print(f"Error: The file {raster} does not exist.")
        return

    result = raster2qtm(raster, resolution, output_format)
    if output_format in STRUCTURED_FORMATS:
        print(result)


if __name__ == "__main__":
    raster2qtm_cli()
