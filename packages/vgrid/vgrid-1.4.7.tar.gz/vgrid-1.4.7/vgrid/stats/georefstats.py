"""
This module provides functions for generating statistics for GEOREF DGGS cells.
"""

import math
import pandas as pd
import numpy as np
import argparse
import geopandas as gpd
from vgrid.utils.constants import (
    GEOREF_RESOLUTION_DEGREES,
    AUTHALIC_AREA,
    DGGS_TYPES,
    VMIN_QUAD,
    VMAX_QUAD,
    VCENTER_QUAD,
)
from vgrid.generator.georefgrid import georefgrid
from vgrid.utils.geometry import check_crossing_geom, characteristic_length_scale,geod
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
from matplotlib.colors import TwoSlopeNorm

min_res = DGGS_TYPES["georef"]["min_res"]
max_res = DGGS_TYPES["georef"]["max_res"]


def georef_metrics(res: int, unit: str = "m"):
    """
    Calculate metrics for GEOREF DGGS cells.

    Args:
        res: Resolution level (0-7)
        unit: 'm' or 'km' for length; area will be 'm^2' or 'km^2'

    Returns:
        tuple: (num_cells, avg_edge_len_in_unit, avg_cell_area_in_unit_squared)
    """
    # normalize and validate unit
    unit = unit.strip().lower()
    if unit not in {"m", "km"}:
        raise ValueError("unit must be one of {'m','km'}")

    # Compute grid size in degrees per your formula
    grid_size_deg = GEOREF_RESOLUTION_DEGREES.get(res)

    # Number of cells across longitude and latitude
    num_lon = int(round(360.0 / grid_size_deg))
    num_lat = int(round(180.0 / grid_size_deg))
    num_cells = num_lon * num_lat

    # Calculate area in km² first
    avg_cell_area = AUTHALIC_AREA / num_cells  # area in m2
    avg_edge_len = math.sqrt(avg_cell_area)
    cls = characteristic_length_scale(avg_cell_area, unit=unit)
    # Convert to requested unit
    if unit == "km":
        avg_cell_area = avg_cell_area / (10**6)  # Convert km² to m²
        avg_edge_len = avg_edge_len / (10**3)  # Convert km to m

    return num_cells, avg_edge_len, avg_cell_area, cls


def georefstats(unit: str = "m"):
    """
    Generate statistics for GEOREF DGGS cells.

    Args:
        unit: 'm' or 'km' for length; area will be 'm^2' or 'km^2'

    Returns:
        pandas.DataFrame: DataFrame containing GEOREF DGGS statistics with columns:
            - resolution: Resolution level (0-7)
            - number_of_cells: Number of cells at each resolution
            - avg_edge_len_{unit}: Average edge length in the given unit
            - avg_cell_area_{unit}2: Average cell area in the squared unit
    """
    # normalize and validate unit
    unit = unit.strip().lower()
    if unit not in {"m", "km"}:
        raise ValueError("unit must be one of {'m','km'}")

    # Initialize lists to store data
    resolutions = []
    num_cells_list = []
    avg_edge_lens = []
    avg_cell_areas = []
    cls_list = []
    for res in range(min_res, max_res + 1):
        num_cells, avg_edge_len, avg_cell_area, cls = georef_metrics(res, unit=unit)
        resolutions.append(res)
        num_cells_list.append(num_cells)
        avg_edge_lens.append(avg_edge_len)
        avg_cell_areas.append(avg_cell_area)
        cls_list.append(cls)
    # Create DataFrame
    # Build column labels with unit awareness (lower case)
    length_col = f"avg_edge_len_{unit}"
    unit_area_label = {"m": "m2", "km": "km2"}[unit]
    area_col = f"avg_cell_area_{unit_area_label}"
    cls_label = f"cls_{unit}"
    df = pd.DataFrame(
        {
            "resolution": resolutions,
            "number_of_cells": num_cells_list,
            length_col: avg_edge_lens,
            area_col: avg_cell_areas,
            cls_label: cls_list,
        }
    )

    return df


def georefstats_cli():
    """
    Command-line interface for generating GEOREF DGGS statistics.

    CLI options:
      -unit, --unit {m,km}
    """
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "-unit", "--unit", dest="unit", choices=["m", "km"], default="m"
    )
    args = parser.parse_args()  # type: ignore

    unit = args.unit

    # Get the DataFrame
    df = georefstats(unit=unit)

    # Display the DataFrame
    print(df)


def georefinspect(res):
    """
    Generate comprehensive inspection data for GEOREF DGGS cells at a given resolution.

    This function creates a detailed analysis of GEOREF cells including area variations,
    compactness measures, and dateline crossing detection.

    Args:
        res: GEOREF resolution level (0-10)

    Returns:
        geopandas.GeoDataFrame: DataFrame containing GEOREF cell inspection data with columns:
            - georef: GEOREF cell ID
            - resolution: Resolution level
            - geometry: Cell geometry
            - cell_area: Cell area in square meters
            - cell_perimeter: Cell perimeter in meters
            - crossed: Whether cell crosses the dateline
            - norm_area: Normalized area (cell_area / mean_area)
            - ipq: Isoperimetric Quotient compactness
            - zsc: Zonal Standardized Compactness
    """
    georef_gdf = georefgrid(res, output_format="gpd")
    georef_gdf["crossed"] = georef_gdf["geometry"].apply(check_crossing_geom)
    mean_area = georef_gdf["cell_area"].mean()
    # Calculate normalized area
    georef_gdf["norm_area"] = georef_gdf["cell_area"] / mean_area
    # Calculate IPQ compactness using the standard formula: CI = 4πA/P²
    georef_gdf["ipq"] = (
        4 * np.pi * georef_gdf["cell_area"] / (georef_gdf["cell_perimeter"] ** 2)
    )
    # Calculate zonal standardized compactness
    georef_gdf["zsc"] = (
        np.sqrt(
            4 * np.pi * georef_gdf["cell_area"]
            - np.power(georef_gdf["cell_area"], 2) / np.power(6378137, 2)
        )
        / georef_gdf["cell_perimeter"]
    )
    
    convex_hull = georef_gdf["geometry"].convex_hull
    convex_hull_area = convex_hull.apply(
        lambda g: abs(geod.geometry_area_perimeter(g)[0])
    )
    # Compute CVH safely; set to NaN where convex hull area is non-positive or invalid
    georef_gdf["cvh"] = np.where(
        (convex_hull_area > 0) & np.isfinite(convex_hull_area),
        georef_gdf["cell_area"] / convex_hull_area,
        np.nan,
    )
      # Replace any accidental inf values with NaN
    georef_gdf["cvh"] = georef_gdf["cvh"].replace([np.inf, -np.inf], np.nan)

    return georef_gdf

def georef_norm_area(georef_gdf: gpd.GeoDataFrame, crs: str | None = 'proj=moll'):
    """
    Plot normalized area map for GEOREF cells.

    This function creates a visualization showing how GEOREF cell areas vary relative
    to the mean area across the globe, highlighting areas of distortion.

    Args:
        georef_gdf: GeoDataFrame from georefinspect function
    """
    fig, ax = plt.subplots(figsize=(10, 5))
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("bottom", size="5%", pad=0.1)
    vmin, vcenter, vmax = ( 
        georef_gdf["norm_area"].min(),
        1.0,
        georef_gdf["norm_area"].max(),
    )
    norm = TwoSlopeNorm(vmin=vmin, vcenter=vcenter, vmax=vmax)
    georef_gdf = georef_gdf[
        ~georef_gdf["crossed"]
    ]  # remove cells that cross the dateline
    georef_gdf.to_crs(crs).plot(
        column="norm_area",
        ax=ax,
        norm=norm,
        legend=True,
        cax=cax,
        cmap="RdYlBu_r",
        legend_kwds={"label": "cell area/mean cell area", "orientation": "horizontal"},
    )
    world_countries = gpd.read_file(
        "https://raw.githubusercontent.com/opengeoshub/vopendata/refs/heads/main/shape/world_countries.geojson"
    )
    world_countries.boundary.to_crs(crs).plot(
        color=None, edgecolor="black", linewidth=0.2, ax=ax
    )
    ax.axis("off")
    cb_ax = fig.axes[1]
    cb_ax.tick_params(labelsize=14)
    cb_ax.set_xlabel(xlabel="GEOREF Normalized Area", fontsize=14)
    ax.margins(0)
    ax.tick_params(left=False, labelleft=False, bottom=False, labelbottom=False)
    plt.tight_layout()


def georef_compactness_ipq(georef_gdf: gpd.GeoDataFrame, crs: str | None = 'proj=moll'):
    """
    Plot IPQ compactness map for GEOREF cells.

    This function creates a visualization showing the Isoperimetric Quotient (IPQ)
    compactness of GEOREF cells across the globe. IPQ measures how close each cell
    is to being circular, with values closer to 0.785 indicating more regular squares.

    Args:
        georef_gdf: GeoDataFrame from georefinspect function
    """
    fig, ax = plt.subplots(figsize=(10, 5))
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("bottom", size="5%", pad=0.1)
    # vmin, vmax, vcenter = georef_gdf['ipq'].min(), georef_gdf['ipq'].max(), np.mean([georef_gdf['ipq'].min(), georef_gdf['ipq'].max()])
    vmin, vcenter, vmax = VMIN_QUAD, VCENTER_QUAD, VMAX_QUAD
    norm = TwoSlopeNorm(vmin=vmin, vcenter=vcenter, vmax=vmax)
    georef_gdf = georef_gdf[
        ~georef_gdf["crossed"]
    ]  # remove cells that cross the dateline
    georef_gdf.to_crs(crs).plot(
        column="ipq",
        ax=ax,
        norm=norm,
        legend=True,
        cax=cax,
        cmap="viridis",
        legend_kwds={"orientation": "horizontal"},
    )
    world_countries = gpd.read_file(
        "https://raw.githubusercontent.com/opengeoshub/vopendata/refs/heads/main/shape/world_countries.geojson"
    )
    world_countries.boundary.to_crs(crs).plot(
        color=None, edgecolor="black", linewidth=0.2, ax=ax
    )
    ax.axis("off")
    cb_ax = fig.axes[1]
    cb_ax.tick_params(labelsize=14)
    cb_ax.set_xlabel(xlabel="GEOREF IPQ Compactness", fontsize=14)
    ax.margins(0)
    ax.tick_params(left=False, labelleft=False, bottom=False, labelbottom=False)
    plt.tight_layout()


def georef_norm_area_hist(georef_gdf: gpd.GeoDataFrame):
    """
    Plot histogram of normalized area for GEOREF cells.

    This function creates a histogram visualization showing the distribution
    of normalized areas for GEOREF cells, helping to understand area variations
    and identify patterns in area distortion.

    Args:
        georef_gdf: GeoDataFrame from georefinspect function
    """
    # Filter out cells that cross the dateline
    georef_gdf = georef_gdf[~georef_gdf["crossed"]]

    # Create the histogram with color ramp
    fig, ax = plt.subplots(figsize=(10, 6))

    # Get histogram data
    counts, bins, patches = ax.hist(
        georef_gdf["norm_area"], bins=50, alpha=0.7, edgecolor="black"
    )

    # Create color ramp using the same normalization as the map function
    vmin, vcenter, vmax = (
        georef_gdf["norm_area"].min(),
        1.0,
        georef_gdf["norm_area"].max()  
    )
    norm = TwoSlopeNorm(vmin=vmin, vcenter=vcenter, vmax=vmax)

    # Apply colors to histogram bars using the same color mapping as the map
    for i, patch in enumerate(patches):
        # Use the center of each bin for color mapping
        bin_center = (bins[i] + bins[i + 1]) / 2
        color = plt.cm.RdYlBu_r(norm(bin_center))
        patch.set_facecolor(color)

    # Add reference line at mean area (norm_area = 1)
    ax.axvline(
        x=1, color="red", linestyle="--", linewidth=2, label="Mean Area (norm_area = 1)"
    )

    # Add statistics text box
    stats_text = f"Mean: {georef_gdf['norm_area'].mean():.3f}\nStd: {georef_gdf['norm_area'].std():.3f}\nMin: {georef_gdf['norm_area'].min():.3f}\nMax: {georef_gdf['norm_area'].max():.3f}"
    ax.text(
        0.02,
        0.98,
        stats_text,
        transform=ax.transAxes,
        fontsize=12,
        verticalalignment="top",
        bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8),
    )

    # Customize the plot
    ax.set_xlabel("GEOREF normalized area", fontsize=14)
    ax.set_ylabel("Number of cells", fontsize=14)
    ax.legend(fontsize=12)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()


def georef_compactness_ipq_hist(georef_gdf: gpd.GeoDataFrame):
    """
    Plot histogram of IPQ compactness for GEOREF cells.

    This function creates a histogram visualization showing the distribution
    of Isoperimetric Quotient (IPQ) compactness values for GEOREF cells, helping
    to understand how close cells are to being regular squares.

    Args:
        georef_gdf: GeoDataFrame from georefinspect function
    """
    # Filter out cells that cross the dateline
    georef_gdf = georef_gdf[~georef_gdf["crossed"]]

    # Create the histogram with color ramp
    fig, ax = plt.subplots(figsize=(10, 6))

    # Get histogram data
    counts, bins, patches = ax.hist(
        georef_gdf["ipq"], bins=50, alpha=0.7, edgecolor="black"
    )

    # Create color ramp using the same normalization as the map function
    vmin, vcenter, vmax = VMIN_QUAD, VCENTER_QUAD, VMAX_QUAD
    norm = TwoSlopeNorm(vmin=vmin, vcenter=vcenter, vmax=vmax)

    # Apply colors to histogram bars using the same color mapping as the map
    for i, patch in enumerate(patches):
        # Use the center of each bin for color mapping
        bin_center = (bins[i] + bins[i + 1]) / 2
        color = plt.cm.viridis(norm(bin_center))
        patch.set_facecolor(color)

    # Add reference line at ideal square IPQ value (0.785)
    ax.axvline(
        x=0.785,
        color="red",
        linestyle="--",
        linewidth=2,
        label="Ideal Square (IPQ = 0.785)",
    )

    # Add statistics text box
    stats_text = f"Mean: {georef_gdf['ipq'].mean():.3f}\nStd: {georef_gdf['ipq'].std():.3f}\nMin: {georef_gdf['ipq'].min():.3f}\nMax: {georef_gdf['ipq'].max():.3f}"
    ax.text(
        0.02,
        0.98,
        stats_text,
        transform=ax.transAxes,
        fontsize=12,
        verticalalignment="top",
        bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8),
    )

    # Customize the plot
    ax.set_xlabel("GEOREF IPQ Compactness", fontsize=14)
    ax.set_ylabel("Number of cells", fontsize=14)
    ax.legend(fontsize=12)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

def georef_compactness_cvh(georef_gdf: gpd.GeoDataFrame, crs: str | None = 'proj=moll'):
    """
    Plot CVH (cell area / convex hull area) compactness map for GEOREF cells.

    Values are in (0, 1], with 1 indicating the most compact (convex) shape.
    """
    fig, ax = plt.subplots(figsize=(10, 5))
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("bottom", size="5%", pad=0.1)   
    georef_gdf = georef_gdf[~georef_gdf["crossed"]]  # remove cells that cross the dateline 
    georef_gdf = georef_gdf[np.isfinite(georef_gdf["cvh"])]
    georef_gdf = georef_gdf[georef_gdf["cvh"] <= 1.1]
    vmin, vcenter, vmax = 0.90, 1.00, 1.10
    norm = TwoSlopeNorm(vmin=vmin, vcenter=vcenter, vmax=vmax)
    georef_gdf.to_crs(crs).plot(
        column="cvh",
        ax=ax,
        norm=norm,
        legend=True,
        cax=cax,
        cmap="viridis",
        legend_kwds={"orientation": "horizontal"},
    )
    world_countries = gpd.read_file(
        "https://raw.githubusercontent.com/opengeoshub/vopendata/refs/heads/main/shape/world_countries.geojson"
    )
    world_countries.boundary.to_crs(crs).plot(
        color=None, edgecolor="black", linewidth=0.2, ax=ax
    )
    ax.axis("off")
    cb_ax = fig.axes[1]
    cb_ax.tick_params(labelsize=14)
    cb_ax.set_xlabel(xlabel="GEOREF CVH Compactness", fontsize=14)
    ax.margins(0)
    ax.tick_params(left=False, labelleft=False, bottom=False, labelbottom=False)
    plt.tight_layout()


def georef_compactness_cvh_hist(georef_gdf: gpd.GeoDataFrame):    
    """
    Plot histogram of CVH (cell area / convex hull area) for GEOREF cells.
    """
    # Filter out cells that cross the dateline
    georef_gdf = georef_gdf[~georef_gdf["crossed"]]
    georef_gdf = georef_gdf[np.isfinite(georef_gdf["cvh"])]
    georef_gdf = georef_gdf[georef_gdf["cvh"] <= 1.1]

    # Create the histogram with color ramp
    fig, ax = plt.subplots(figsize=(10, 6))

    counts, bins, patches = ax.hist(
        georef_gdf["cvh"], bins=50, alpha=0.7, edgecolor="black"
    )

    # Color mapping centered at 1
    vmin, vcenter, vmax = 0.90,1.00, 1.10
    norm = TwoSlopeNorm(vmin=vmin, vcenter=vcenter, vmax=vmax)

    for i, patch in enumerate(patches):
        bin_center = (bins[i] + bins[i + 1]) / 2
        color = plt.cm.viridis(norm(bin_center))
        patch.set_facecolor(color)

    # Reference line at ideal compactness
    ax.axvline(x=1, color="red", linestyle="--", linewidth=2, label="Ideal (cvh = 1)")

    stats_text = (
        f"Mean: {georef_gdf['cvh'].mean():.6f}\n"
        f"Std: {georef_gdf['cvh'].std():.6f}\n"
        f"Min: {georef_gdf['cvh'].min():.6f}\n"
        f"Max: {georef_gdf['cvh'].max():.6f}"
    )
    ax.text(
        0.02,
        0.98,
        stats_text,
        transform=ax.transAxes,
        fontsize=12,
        verticalalignment="top",
        bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8),
    )

    ax.set_xlabel("GEOREF CVH Compactness", fontsize=14)
    ax.set_ylabel("Number of cells", fontsize=14)
    ax.legend(fontsize=12)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()


def georefinspect_cli():
    """
    Command-line interface for GEOREF cell inspection.

    CLI options:
      -r, --resolution: GEOREF resolution level (0-10)
    """
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("-r", "--resolution", dest="resolution", type=int, default=0)
    args = parser.parse_args()  # type: ignore
    resolution = args.resolution
    print(georefinspect(resolution))


if __name__ == "__main__":
    georefstats_cli()
