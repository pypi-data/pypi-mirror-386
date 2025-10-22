"""
This module provides functions for generating statistics for EASE-DGGS cells.
"""

import pandas as pd
import numpy as np
import argparse
import geopandas as gpd
from ease_dggs.constants import levels_specs
from vgrid.utils.constants import DGGS_TYPES, VMIN_QUAD, VMAX_QUAD, VCENTER_QUAD
from vgrid.generator.easegrid import easegrid
from vgrid.utils.geometry import check_crossing_geom, characteristic_length_scale, geod
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
from matplotlib.colors import TwoSlopeNorm

min_res = DGGS_TYPES["ease"]["min_res"]
max_res = DGGS_TYPES["ease"]["max_res"]


def ease_metrics(res, unit: str = "m"):  # length unit is m, area unit is m2
    """
    Calculate metrics for EASE-DGGS cells at a given resolution.

    Args:
        res: Resolution level (0-6)
        unit: 'm' or 'km' for length; area will be 'm^2' or 'km^2'

    Returns:
        tuple: (num_cells, edge_length_in_unit, cell_area_in_unit_squared)
    """
    # normalize and validate unit
    unit = unit.strip().lower()
    if unit not in {"m", "km"}:
        raise ValueError("unit must be one of {'m','km'}")

    num_cells = levels_specs[res]["n_row"] * levels_specs[res]["n_col"]

    # Get edge lengths in meters from constants
    avg_edge_length = levels_specs[res][
        "x_length"
    ]  # Assuming x_length and y_length are equal
    cell_area = avg_edge_length * levels_specs[res]["y_length"]  # cell area in m²
    cls = characteristic_length_scale(
        cell_area, unit=unit
    )  # cell_area is in m², function handles conversion
    # Convert to requested unit
    if unit == "km":
        avg_edge_length = avg_edge_length / (10**3)  # edge length in m
        cell_area = cell_area / (10**6)  # cell area in km²

    return num_cells, avg_edge_length, cell_area, cls


def easestats(unit: str = "m"):  # length unit is m, area unit is m2
    """
    Generate statistics for EASE-DGGS cells.
    length unit is m, area unit is m2
    Args:
        unit: 'm' or 'km' for length; area will be 'm^2' or 'km^2'

    Returns:
        pandas.DataFrame: DataFrame containing EASE-DGGS statistics with columns:
            - Resolution: Resolution level (0-6)
            - Number_of_Cells: Number of cells at each resolution
            - Avg_Edge_Length_{unit}: Average edge length in the given unit
            - Avg_Cell_Area_{unit}2: Average cell area in the squared unit
            - CLS_{unit}: Characteristic Length Scale in the given unit
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
        num_cells_at_res, avg_edge_length, cell_area, cls = ease_metrics(res, unit)
        resolutions.append(res)
        num_cells_list.append(num_cells_at_res)
        avg_edge_lens.append(avg_edge_length)
        avg_cell_areas.append(cell_area)
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


def easestats_cli():
    """
    Command-line interface for generating EASE-DGGS statistics.

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
    df = easestats(unit=unit)

    # Display the DataFrame
    print(df)


def easeinspect(res):  # length unit is m, area unit is m2
    """
    Generate comprehensive inspection data for EASE-DGGS cells at a given resolution.

    This function creates a detailed analysis of EASE cells including area variations,
    compactness measures, and dateline crossing detection.

    Args:
        res: EASE-DGGS resolution level (0-6)

    Returns:
        geopandas.GeoDataFrame: DataFrame containing EASE cell inspection data with columns:
            - ease: EASE cell ID
            - resolution: Resolution level
            - geometry: Cell geometry
            - cell_area: Cell area in square meters
            - cell_perimeter: Cell perimeter in meters
            - crossed: Whether cell crosses the dateline
            - norm_area: Normalized area (cell_area / mean_area)
            - ipq: Isoperimetric Quotient compactness
            - zsc: Zonal Standardized Compactness
    """
    ease_gdf = easegrid(res, output_format="gpd")
    ease_gdf["crossed"] = ease_gdf["geometry"].apply(check_crossing_geom)
    mean_area = ease_gdf["cell_area"].mean()
    # Calculate normalized area
    ease_gdf["norm_area"] = ease_gdf["cell_area"] / mean_area
    # Calculate IPQ compactness using the standard formula: CI = 4πA/P²
    ease_gdf["ipq"] = (
        4 * np.pi * ease_gdf["cell_area"] / (ease_gdf["cell_perimeter"] ** 2)
    )
    # Calculate zonal standardized compactness
    ease_gdf["zsc"] = (
        np.sqrt(
            4 * np.pi * ease_gdf["cell_area"]
            - np.power(ease_gdf["cell_area"], 2) / np.power(6378137, 2)
        )
        / ease_gdf["cell_perimeter"]
    )

    convex_hull = ease_gdf["geometry"].convex_hull
    convex_hull_area = convex_hull.apply(
        lambda g: abs(geod.geometry_area_perimeter(g)[0])
    )
    # Compute CVH safely; set to NaN where convex hull area is non-positive or invalid
    ease_gdf["cvh"] = np.where(
        (convex_hull_area > 0) & np.isfinite(convex_hull_area),
        ease_gdf["cell_area"] / convex_hull_area,
        np.nan,
    )
      # Replace any accidental inf values with NaN
    ease_gdf["cvh"] = ease_gdf["cvh"].replace([np.inf, -np.inf], np.nan)
    return ease_gdf

def ease_norm_area(ease_gdf: gpd.GeoDataFrame, crs: str | None = 'proj=moll'):
    """
    Plot normalized area map for EASE cells.

    This function creates a visualization showing how EASE cell areas vary relative
    to the mean area across the globe, highlighting areas of distortion.

    Args:
        ease_gdf: GeoDataFrame from easeinspect function
    """
    fig, ax = plt.subplots(figsize=(10, 5))
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("bottom", size="5%", pad=0.1)
    vmin, vcenter, vmax = ease_gdf["norm_area"].min(), 1.0, ease_gdf["norm_area"].max()
    norm = TwoSlopeNorm(vmin=vmin, vcenter=vcenter, vmax=vmax)
    ease_gdf = ease_gdf[~ease_gdf["crossed"]]  # remove cells that cross the dateline
    ease_gdf.to_crs(crs).plot(
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
    cb_ax.set_xlabel(xlabel="EASE Normalized Area", fontsize=14)
    ax.margins(0)
    ax.tick_params(left=False, labelleft=False, bottom=False, labelbottom=False)
    plt.tight_layout()


def ease_compactness_ipq(ease_gdf: gpd.GeoDataFrame, crs: str | None = 'proj=moll'):
    """
    Plot IPQ compactness map for EASE cells.

    This function creates a visualization showing the Isoperimetric Quotient (IPQ)
    compactness of EASE cells across the globe. IPQ measures how close each cell
    is to being circular, with values closer to 0.785 indicating more regular squares.

    Args:
        ease_gdf: GeoDataFrame from easeinspect function
    """
    fig, ax = plt.subplots(figsize=(10, 5))
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("bottom", size="5%", pad=0.1)
    # For EASE (square cells), ideal IPQ is π/4 ≈ 0.785
    vmin, vcenter, vmax = VMIN_QUAD, VCENTER_QUAD, VMAX_QUAD
    norm = TwoSlopeNorm(vmin=vmin, vcenter=vcenter, vmax=vmax)
    ease_gdf = ease_gdf[~ease_gdf["crossed"]]  # remove cells that cross the dateline
    ease_gdf.to_crs(crs).plot(
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
    cb_ax.set_xlabel(xlabel="EASE IPQ Compactness", fontsize=14)
    ax.margins(0)
    ax.tick_params(left=False, labelleft=False, bottom=False, labelbottom=False)
    plt.tight_layout()


def ease_norm_area_hist(ease_gdf: gpd.GeoDataFrame):
    """
    Plot histogram of normalized area for EASE cells.

    This function creates a histogram visualization showing the distribution
    of normalized areas for EASE cells, helping to understand area variations
    and identify patterns in area distortion.

    Args:
        ease_gdf: GeoDataFrame from easeinspect function
    """
    # Filter out cells that cross the dateline
    ease_gdf = ease_gdf[~ease_gdf["crossed"]]

    # Create the histogram with color ramp
    fig, ax = plt.subplots(figsize=(10, 6))

    # Get histogram data
    counts, bins, patches = ax.hist(
        ease_gdf["norm_area"], bins=50, alpha=0.7, edgecolor="black"
    )

    # Create color ramp using the same normalization as the map function
    vmin, vcenter, vmax = (
        ease_gdf["norm_area"].min(),
        1.0,
        ease_gdf["norm_area"].max()
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
    stats_text = f"Mean: {ease_gdf['norm_area'].mean():.3f}\nStd: {ease_gdf['norm_area'].std():.3f}\nMin: {ease_gdf['norm_area'].min():.3f}\nMax: {ease_gdf['norm_area'].max():.3f}"
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
    ax.set_xlabel("EASE normalized area", fontsize=14)
    ax.set_ylabel("Number of cells", fontsize=14)
    ax.legend(fontsize=12)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()


def ease_compactness_ipq_hist(ease_gdf: gpd.GeoDataFrame):
    """
    Plot histogram of IPQ compactness for EASE cells.

    This function creates a histogram visualization showing the distribution
    of Isoperimetric Quotient (IPQ) compactness values for EASE cells, helping
    to understand how close cells are to being regular squares.

    Args:
        ease_gdf: GeoDataFrame from easeinspect function
    """
    # Filter out cells that cross the dateline
    ease_gdf = ease_gdf[~ease_gdf["crossed"]]

    # Create the histogram with color ramp
    fig, ax = plt.subplots(figsize=(10, 6))

    # Get histogram data
    counts, bins, patches = ax.hist(
        ease_gdf["ipq"], bins=50, alpha=0.7, edgecolor="black"
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
    stats_text = f"Mean: {ease_gdf['ipq'].mean():.3f}\nStd: {ease_gdf['ipq'].std():.3f}\nMin: {ease_gdf['ipq'].min():.3f}\nMax: {ease_gdf['ipq'].max():.3f}"
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
    ax.set_xlabel("EASE IPQ Compactness", fontsize=14)
    ax.set_ylabel("Number of cells", fontsize=14)
    ax.legend(fontsize=12)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()


def ease_compactness_cvh(ease_gdf: gpd.GeoDataFrame, crs: str | None = 'proj=moll'):
    """
    Plot CVH (cell area / convex hull area) compactness map for EASE cells.

    Values are in (0, 1], with 1 indicating the most compact (convex) shape.
    """
    fig, ax = plt.subplots(figsize=(10, 5))
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("bottom", size="5%", pad=0.1)   
    ease_gdf = ease_gdf[~ease_gdf["crossed"]]  # remove cells that cross the dateline 
    ease_gdf = ease_gdf[np.isfinite(ease_gdf["cvh"])]
    ease_gdf = ease_gdf[ease_gdf["cvh"] <= 1.1]
    vmin, vcenter, vmax = 0.90, 1.00, 1.10
    norm = TwoSlopeNorm(vmin=vmin, vcenter=vcenter, vmax=vmax)
    ease_gdf.to_crs(crs).plot(
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
    cb_ax.set_xlabel(xlabel="EASE CVH Compactness", fontsize=14)
    ax.margins(0)
    ax.tick_params(left=False, labelleft=False, bottom=False, labelbottom=False)
    plt.tight_layout()


def ease_compactness_cvh_hist(ease_gdf: gpd.GeoDataFrame):
    """
        Plot histogram of CVH (cell area / convex hull area) for EASE cells.
    """
    # Filter out cells that cross the dateline
    ease_gdf = ease_gdf[~ease_gdf["crossed"]]
    ease_gdf = ease_gdf[np.isfinite(ease_gdf["cvh"])]
    ease_gdf = ease_gdf[ease_gdf["cvh"] <= 1.1]

    # Create the histogram with color ramp
    fig, ax = plt.subplots(figsize=(10, 6))

    counts, bins, patches = ax.hist(
        ease_gdf["cvh"], bins=50, alpha=0.7, edgecolor="black"
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
        f"Mean: {ease_gdf['cvh'].mean():.6f}\n"
        f"Std: {ease_gdf['cvh'].std():.6f}\n"
        f"Min: {ease_gdf['cvh'].min():.6f}\n"
        f"Max: {ease_gdf['cvh'].max():.6f}"
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

    ax.set_xlabel("EASE CVH Compactness", fontsize=14)
    ax.set_ylabel("Number of cells", fontsize=14)
    ax.legend(fontsize=12)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()


def easeinspect_cli():
    """
    Command-line interface for EASE cell inspection.

    CLI options:
      -r, --resolution: EASE resolution level (0-6)
    """
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("-r", "--resolution", dest="resolution", type=int, default=0)
    args = parser.parse_args()  # type: ignore
    resolution = args.resolution
    print(easeinspect(resolution))


if __name__ == "__main__":
    easestats_cli()
