"""
This module provides functions for generating statistics for rHEALPix DGGS cells.
"""

import math
import pandas as pd
import numpy as np
import argparse
import geopandas as gpd
from vgrid.utils.constants import (
    AUTHALIC_AREA,
    DGGS_TYPES,
    VMIN_QUAD,
    VMAX_QUAD,
    VCENTER_QUAD,
)
from vgrid.generator.rhealpixgrid import rhealpixgrid
from vgrid.utils.geometry import check_crossing_geom, characteristic_length_scale,geod
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
from matplotlib.colors import TwoSlopeNorm

min_res = DGGS_TYPES["rhealpix"]["min_res"]
max_res = DGGS_TYPES["rhealpix"]["max_res"]


def rhealpix_metrics(res, unit: str = "m"):  # length unit is km, area unit is km2
    """
    Calculate metrics for rHEALPix DGGS cells at a given resolution.

    Args:
        res: Resolution level (0-30)
        unit: 'm' or 'km' for length; area will be 'm^2' or 'km^2'

    Returns:
        tuple: (num_cells, edge_length_in_unit, cell_area_in_unit_squared)
    """
    # normalize and validate unit
    unit = unit.strip().lower()
    if unit not in {"m", "km"}:
        raise ValueError("unit must be one of {'m','km'}")

    num_cells = 6 * 9 ** (res)

    # Calculate area in km² first
    avg_cell_area = AUTHALIC_AREA / num_cells  # area in m2
    avg_edge_len = math.sqrt(avg_cell_area)
    cls = characteristic_length_scale(avg_cell_area, unit=unit)
    # Convert to requested unit
    if unit == "km":
        avg_cell_area = avg_cell_area / (10**6)  # Convert km² to m²
        avg_edge_len = avg_edge_len / (10**3)  # Convert km to m
        cls = cls / (10**3)  # Convert km to m
    return num_cells, avg_edge_len, avg_cell_area, cls


def rhealpixstats(unit: str = "m"):
    """
    Generate statistics for rHEALPix DGGS cells.

    Args:
        unit: 'm' or 'km' for length; area will be 'm^2' or 'km^2'

    Returns:
        pandas.DataFrame: DataFrame containing rHEALPix DGGS statistics with columns:
            - Resolution: Resolution level (0-30)
            - Number_of_Cells: Number of cells at each resolution
            - Avg_Edge_Length_{unit}: Average edge length in the given unit
            - Avg_Cell_Area_{unit}2: Average cell area in the squared unit
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
        num_cells, avg_edge_len, avg_cell_area, cls = rhealpix_metrics(
            res, unit=unit
        )  # length unit is km, area unit is km2
        resolutions.append(res)
        num_cells_list.append(num_cells)
        avg_edge_lens.append(avg_edge_len)
        avg_cell_areas.append(avg_cell_area)
        cls_list.append(cls)
    # Create DataFrame
    # Build column labels with unit awareness
    avg_edge_len = f"avg_edge_len_{unit}"
    unit_area_label = {"m": "m2", "km": "km2"}[unit]
    avg_cell_area = f"avg_cell_area_{unit_area_label}"
    cls_label = f"cls_{unit}"
    df = pd.DataFrame(
        {
            "resolution": resolutions,
            "number_of_cells": num_cells_list,
            avg_edge_len: avg_edge_lens,
            avg_cell_area: avg_cell_areas,
            cls_label: cls_list,
        }
    )

    return df


def rhealpixstats_cli():
    """
    Command-line interface for generating rHEALPix DGGS statistics.

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
    df = rhealpixstats(unit=unit)

    # Display the DataFrame
    print(df)


def rhealpixinspect(res):
    """
    Generate comprehensive inspection data for rHEALPix DGGS cells at a given resolution.

    This function creates a detailed analysis of rHEALPix cells including area variations,
    compactness measures, and dateline crossing detection.

    Args:
        res: rHEALPix resolution level (0-15)

    Returns:
        geopandas.GeoDataFrame: DataFrame containing rHEALPix cell inspection data with columns:
            - rhealpix: rHEALPix cell ID
            - resolution: Resolution level
            - geometry: Cell geometry
            - cell_area: Cell area in square meters
            - cell_perimeter: Cell perimeter in meters
            - crossed: Whether cell crosses the dateline
            - norm_area: Normalized area (cell_area / mean_area)
            - ipq: Isoperimetric Quotient compactness
            - zsc: Zonal Standardized Compactness
            - cvh: Convex Hull Compactness
    """
    rhealpix_gdf = rhealpixgrid(res, output_format="gpd")
    rhealpix_gdf["crossed"] = rhealpix_gdf["geometry"].apply(check_crossing_geom)
    mean_area = rhealpix_gdf["cell_area"].mean()
    # Calculate normalized area
    rhealpix_gdf["norm_area"] = rhealpix_gdf["cell_area"] / mean_area
    # Calculate IPQ compactness using the standard formula: CI = 4πA/P²
    rhealpix_gdf["ipq"] = (
        4 * np.pi * rhealpix_gdf["cell_area"] / (rhealpix_gdf["cell_perimeter"] ** 2)
    )
    # Calculate zonal standardized compactness
    rhealpix_gdf["zsc"] = (
        np.sqrt(
            4 * np.pi * rhealpix_gdf["cell_area"]
            - np.power(rhealpix_gdf["cell_area"], 2) / np.power(6378137, 2)
        )
        / rhealpix_gdf["cell_perimeter"]
    )
    convex_hull = rhealpix_gdf["geometry"].convex_hull
    convex_hull_area = convex_hull.apply(
        lambda g: abs(geod.geometry_area_perimeter(g)[0])
    )
    # Compute CVH safely; set to NaN where convex hull area is non-positive or invalid
    rhealpix_gdf["cvh"] = np.where(
        (convex_hull_area > 0) & np.isfinite(convex_hull_area),
        rhealpix_gdf["cell_area"] / convex_hull_area,
        np.nan,
    )
    # Replace any accidental inf values with NaN
    rhealpix_gdf["cvh"] = rhealpix_gdf["cvh"].replace([np.inf, -np.inf], np.nan)    
    return rhealpix_gdf

    return rhealpix_gdf


def rhealpix_norm_area(rhealpix_gdf: gpd.GeoDataFrame, crs: str | None = 'proj=moll'):
    """
    Plot normalized area map for rHEALPix cells.

    This function creates a visualization showing how rHEALPix cell areas vary relative
    to the mean area across the globe, highlighting areas of distortion.

    Args:
        rhealpix_gdf: GeoDataFrame from rhealpixinspect function
    """
    fig, ax = plt.subplots(figsize=(10, 5))
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("bottom", size="5%", pad=0.1)
    vmin, vcenter, vmax = (
        rhealpix_gdf["norm_area"].min(),
        1.0,
        rhealpix_gdf["norm_area"].max() 
    )
    norm = TwoSlopeNorm(vmin=vmin, vcenter=vcenter, vmax=vmax)
    rhealpix_gdf = rhealpix_gdf[
        ~rhealpix_gdf["crossed"]
    ]  # remove cells that cross the dateline
    rhealpix_gdf.to_crs(crs).plot(
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
    cb_ax.set_xlabel(xlabel="rHEALPix Normalized Area", fontsize=14)
    ax.margins(0)
    ax.tick_params(left=False, labelleft=False, bottom=False, labelbottom=False)
    plt.tight_layout()


def rhealpix_compactness_ipq(rhealpix_gdf: gpd.GeoDataFrame, crs: str | None = 'proj=moll'):
    """
    Plot IPQ compactness map for rHEALPix cells.

    This function creates a visualization showing the Isoperimetric Quotient (IPQ)
    compactness of rHEALPix cells across the globe. IPQ measures how close each cell
    is to being circular, with values closer to 0.907 indicating more regular hexagons.

    Args:
        rhealpix_gdf: GeoDataFrame from rhealpixinspect function
    """
    fig, ax = plt.subplots(figsize=(10, 5))
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("bottom", size="5%", pad=0.1)
    # vmin, vmax, vcenter = rhealpix_gdf['ipq'].min(), rhealpix_gdf['ipq'].max(), np.mean([rhealpix_gdf['ipq'].min(), rhealpix_gdf['ipq'].max()])
    norm = TwoSlopeNorm(vmin=VMIN_QUAD, vcenter=VCENTER_QUAD, vmax=VMAX_QUAD)
    rhealpix_gdf = rhealpix_gdf[
        ~rhealpix_gdf["crossed"]
    ]  # remove cells that cross the dateline
    rhealpix_gdf.to_crs(crs).plot(  # type: ignore
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
    cb_ax.set_xlabel(xlabel="rHEALPix IPQ Compactness", fontsize=14)
    ax.margins(0)
    ax.tick_params(left=False, labelleft=False, bottom=False, labelbottom=False)
    plt.tight_layout()


def rhealpix_norm_area_hist(rhealpix_gdf: gpd.GeoDataFrame):
    """
    Plot histogram of normalized area for rHEALPix cells.

    This function creates a histogram visualization showing the distribution
    of normalized areas for rHEALPix cells, helping to understand area variations
    and identify patterns in area distortion.

    Args:
        rhealpix_gdf: GeoDataFrame from rhealpixinspect function
    """
    # Filter out cells that cross the dateline
    rhealpix_gdf = rhealpix_gdf[~rhealpix_gdf["crossed"]]

    # Create the histogram with color ramp
    fig, ax = plt.subplots(figsize=(10, 6))

    # Get histogram data
    counts, bins, patches = ax.hist(
        rhealpix_gdf["norm_area"], bins=50, alpha=0.7, edgecolor="black"
    )

    # Create color ramp using the same normalization as the map function
    vmin, vcenter, vmax = (
        rhealpix_gdf["norm_area"].min(),
        1.0,
        rhealpix_gdf["norm_area"].max()
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
    stats_text = f"Mean: {rhealpix_gdf['norm_area'].mean():.3f}\nStd: {rhealpix_gdf['norm_area'].std():.3f}\nMin: {rhealpix_gdf['norm_area'].min():.3f}\nMax: {rhealpix_gdf['norm_area'].max():.3f}"
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
    ax.set_xlabel("rHEALPix normalized area", fontsize=14)
    ax.set_ylabel("Number of cells", fontsize=14)
    ax.legend(fontsize=12)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()


def rhealpix_compactness_ipq_hist(rhealpix_gdf: gpd.GeoDataFrame):
    """
    Plot histogram of IPQ compactness for rHEALPix cells.

    This function creates a histogram visualization showing the distribution
    of Isoperimetric Quotient (IPQ) compactness values for rHEALPix cells, helping
    to understand how close cells are to being regular quadrilaterals.

    Args:
        rhealpix_gdf: GeoDataFrame from rhealpixinspect function
    """
    # Filter out cells that cross the dateline
    rhealpix_gdf = rhealpix_gdf[~rhealpix_gdf["crossed"]]

    # Create the histogram with color ramp
    fig, ax = plt.subplots(figsize=(10, 6))

    # Get histogram data
    counts, bins, patches = ax.hist(
        rhealpix_gdf["ipq"], bins=50, alpha=0.7, edgecolor="black"
    )

    # Create color ramp using the same normalization as the map function
    norm = TwoSlopeNorm(vmin=VMIN_QUAD, vcenter=VCENTER_QUAD, vmax=VMAX_QUAD)

    # Apply colors to histogram bars using the same color mapping as the map
    for i, patch in enumerate(patches):
        # Use the center of each bin for color mapping
        bin_center = (bins[i] + bins[i + 1]) / 2
        color = plt.cm.viridis(norm(bin_center))
        patch.set_facecolor(color)

    # Add reference line at ideal quadrilateral IPQ value (1.0)
    ax.axvline(
        x=1.0,
        color="red",
        linestyle="--",
        linewidth=2,
        label="Ideal Quadrilateral (IPQ = 1.0)",
    )

    # Add statistics text box
    stats_text = f"Mean: {rhealpix_gdf['ipq'].mean():.3f}\nStd: {rhealpix_gdf['ipq'].std():.3f}\nMin: {rhealpix_gdf['ipq'].min():.3f}\nMax: {rhealpix_gdf['ipq'].max():.3f}"
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
    ax.set_xlabel("rHEALPix IPQ Compactness", fontsize=14)
    ax.set_ylabel("Number of cells", fontsize=14)
    ax.legend(fontsize=12)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()


def rhealpix_compactness_cvh(rhealpix_gdf: gpd.GeoDataFrame, crs: str | None = 'proj=moll'):
    """
    Plot CVH (cell area / convex hull area) compactness map for A5 cells.

    Values are in (0, 1], with 1 indicating the most compact (convex) shape.
    """
    fig, ax = plt.subplots(figsize=(10, 5))
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("bottom", size="5%", pad=0.1)   
    rhealpix_gdf = rhealpix_gdf[~rhealpix_gdf["crossed"]]  # remove cells that cross the dateline 
    rhealpix_gdf = rhealpix_gdf[np.isfinite(rhealpix_gdf["cvh"])]
    rhealpix_gdf = rhealpix_gdf[rhealpix_gdf["cvh"] <= 1.1]
    vmin, vcenter, vmax = 0.90,1.00, 1.10
    norm = TwoSlopeNorm(vmin=vmin, vcenter=vcenter, vmax=vmax)
    rhealpix_gdf.to_crs(crs).plot(
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
    cb_ax.set_xlabel(xlabel="rHEALPix CVH Compactness", fontsize=14)
    ax.margins(0)
    ax.tick_params(left=False, labelleft=False, bottom=False, labelbottom=False)
    plt.tight_layout()


def rhealpix_compactness_cvh_hist(rhealpix_gdf: gpd.GeoDataFrame):
    """
    Plot histogram of CVH (cell area / convex hull area) for rHEALPix cells.
    """
    # Filter out cells that cross the dateline
    rhealpix_gdf = rhealpix_gdf[~rhealpix_gdf["crossed"]]
    rhealpix_gdf = rhealpix_gdf[np.isfinite(rhealpix_gdf["cvh"])]
    rhealpix_gdf = rhealpix_gdf[rhealpix_gdf["cvh"] <= 1.1]

    # Create the histogram with color ramp
    fig, ax = plt.subplots(figsize=(10, 6))

    counts, bins, patches = ax.hist(
        rhealpix_gdf["cvh"], bins=50, alpha=0.7, edgecolor="black"
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
        f"Mean: {rhealpix_gdf['cvh'].mean():.6f}\n"
        f"Std: {rhealpix_gdf['cvh'].std():.6f}\n"
        f"Min: {rhealpix_gdf['cvh'].min():.6f}\n"
        f"Max: {rhealpix_gdf['cvh'].max():.6f}"
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

    ax.set_xlabel("rHEALPix CVH Compactness", fontsize=14)
    ax.set_ylabel("Number of cells", fontsize=14)
    ax.legend(fontsize=12)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()



def rhealpixinspect_cli():
    """
    Command-line interface for rHEALPix cell inspection.

    CLI options:
      -r, --resolution: rHEALPix resolution level (0-15)
    """
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("-r", "--resolution", dest="resolution", type=int, default=0)
    args = parser.parse_args()  # type: ignore
    resolution = args.resolution
    print(rhealpixinspect(resolution))


if __name__ == "__main__":
    rhealpixstats_cli()
