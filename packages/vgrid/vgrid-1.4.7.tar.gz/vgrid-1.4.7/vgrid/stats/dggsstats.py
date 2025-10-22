"""
This module provides functions for generating comprehensive statistics across multiple DGGS types.
"""

import argparse
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import seaborn as sns

# Import all the individual inspect functions
from vgrid.stats.h3stats import h3inspect
from vgrid.stats.s2stats import s2inspect
from vgrid.stats.a5stats import a5inspect
from vgrid.stats.isea4tstats import isea4tinspect
from vgrid.stats.rhealpixstats import rhealpixinspect
from vgrid.stats.dggalstats import dggalinspect
from vgrid.stats.dggridstats import dggridinspect

# Import utilities
from vgrid.utils.constants import DGGS_INSPECT
from vgrid.utils.io import create_dggrid_instance
import warnings

warnings.filterwarnings(
    "ignore",
    message="driver ESRI Shapefile does not support open option DRIVER",
    category=RuntimeWarning,
)


def dggsinspect():
    """
    Multi-DGGS cell inspection using DGGS_INSPECT configuration.

    Returns:
        dict: Dictionary with DGGS types as keys and GeoDataFrames as values
    """

    # Define DGGS type configurations with their inspect functions and parameter mappings
    dggs_configs = {
        "h3": {"inspect_func": h3inspect, "param_name": "res", "cell_id_col": "h3"},
        "s2": {"inspect_func": s2inspect, "param_name": "res", "cell_id_col": "s2"},
        "a5": {"inspect_func": a5inspect, "param_name": "res", "cell_id_col": "a5"},
        "isea4t": {
            "inspect_func": isea4tinspect,
            "param_name": "res",
            "cell_id_col": "isea4t",
        },
        "rhealpix": {
            "inspect_func": rhealpixinspect,
            "param_name": "res",
            "cell_id_col": "rhealpix",
        },
        "dggrid_isea7h": {
            "inspect_func": dggridinspect,
            "param_name": "resolution",
            "cell_id_col": "global_id",
            "dggs_type": "ISEA7H",
        },
        "dggrid_fuller7h": {
            "inspect_func": dggridinspect,
            "param_name": "resolution",
            "cell_id_col": "global_id",
            "dggs_type": "FULLER7H",
        },
        "dggrid_isea4d": {
            "inspect_func": dggridinspect,
            "param_name": "resolution",
            "cell_id_col": "global_id",
            "dggs_type": "ISEA4D",
        },
        "dggrid_fuller4d": {
            "inspect_func": dggridinspect,
            "param_name": "resolution",
            "cell_id_col": "global_id",
            "dggs_type": "FULLER4D",
        },
        "dggrid_isea4t": {
            "inspect_func": dggridinspect,
            "param_name": "resolution",
            "cell_id_col": "global_id",
            "dggs_type": "ISEA4T",
        },
        "dggrid_fuller4t": {
            "inspect_func": dggridinspect,
            "param_name": "resolution",
            "cell_id_col": "global_id",
            "dggs_type": "FULLER4T",
        },
        "dggal_isea3h": {
            "inspect_func": dggalinspect,
            "param_name": "res",
            "cell_id_col": "dggal_isea3h",
            "dggs_type": "isea3h",
        },
        "dggal_isea9r": {
            "inspect_func": dggalinspect,
            "param_name": "res",
            "cell_id_col": "dggal_isea9r",
            "dggs_type": "isea9r",
        },
    }

    # Create dggrid instance once for all dggrid operations
    dggrid_instance = create_dggrid_instance()

    # Dictionary to store processed GeoDataFrames for return
    processed_gdfs = {}

    for dggs_type, config in dggs_configs.items():
        if dggs_type not in DGGS_INSPECT:
            print(f"Warning: {dggs_type} not found in DGGS_INSPECT configuration")
            continue

        inspect_config = DGGS_INSPECT[dggs_type]
        min_res = inspect_config["min_res"]
        max_res = inspect_config["max_res"]

        print(f"Processing {dggs_type} for resolutions {min_res}-{max_res}")

        dggs_type_gdfs = []

        for res in range(min_res, max_res + 1):
            try:
                # Call the specific inspect function with appropriate parameters
                if dggs_type.startswith("dggrid_"):
                    # For dggrid functions that need dggrid_instance and dggs_type parameters
                    gdf = config["inspect_func"](
                        dggrid_instance,
                        dggs_type=config["dggs_type"],
                        **{config["param_name"]: res},
                    )
                elif "dggs_type" in config:
                    # For dggal functions that need dggs_type parameter
                    gdf = config["inspect_func"](
                        dggs_type=config["dggs_type"], **{config["param_name"]: res}
                    )
                else:
                    # For standard inspect functions
                    gdf = config["inspect_func"](**{config["param_name"]: res})

                # Add dggs_type column
                gdf["dggs_type"] = dggs_type

                # Rename the cell ID column to a generic name
                cell_id_col = config["cell_id_col"]
                if cell_id_col in gdf.columns:
                    gdf = gdf.rename(columns={cell_id_col: "cell_id"})

                # Ensure all expected columns exist, add NaN for missing ones
                expected_columns = [
                    "dggs_type",
                    "resolution",
                    "cell_id",
                    "geometry",
                    "cell_area",
                    "cell_perimeter",
                    "crossed",
                    "norm_area",
                    "ipq",
                    "zsc",
                ]

                for col in expected_columns:
                    if col not in gdf.columns:
                        gdf[col] = None

                # Reorder columns to match expected format
                gdf = gdf[expected_columns]

                dggs_type_gdfs.append(gdf)

            except Exception as e:
                print(f"Error processing {dggs_type} at resolution {res}: {e}")
                continue

        # Process and save this DGGS type immediately after completing all resolutions
        if dggs_type_gdfs:
            # Combine GeoDataFrames for this DGGS type
            combined_gdf = pd.concat(dggs_type_gdfs, ignore_index=True)

            # Filter to keep only cells that do NOT cross the dateline
            combined_gdf = combined_gdf[~combined_gdf["crossed"]]

            # Ensure it's a GeoDataFrame
            if not isinstance(combined_gdf, gpd.GeoDataFrame):
                combined_gdf = gpd.GeoDataFrame(combined_gdf, geometry="geometry")

            # Save this DGGS type immediately as a geoparquet file
            output_file = f"{dggs_type}.parquet"
            print(f"✓ Completed {dggs_type}: {len(combined_gdf)} cells")
            print(f"  Saving to: {output_file}")
            combined_gdf.to_parquet(output_file, index=False)
            print(
                f"  ✓ Successfully saved {len(combined_gdf)} records to {output_file}"
            )

            # Store in processed_gdfs for return
            processed_gdfs[dggs_type] = combined_gdf
        else:
            print(f"Warning: No valid data generated for {dggs_type}")

    if not processed_gdfs:
        raise ValueError(
            "No valid DGGS data could be generated for the specified resolution range"
        )

    print("\n🎉 All DGGS types processed and saved!")
    print(f"Total DGGS types: {len(processed_gdfs)}")
    total_cells = sum(len(gdf) for gdf in processed_gdfs.values())
    print(f"Total cells across all types: {total_cells}")

    return processed_gdfs


def dggsinspect_cli():
    """
    Command-line interface for multi-DGGS cell inspection using DGGS_INSPECT configuration.
    """
    try:
        results = dggsinspect()
        return results
    except Exception as e:
        print(f"Error: {e}")
        return None


def dggsboxplot(
    parquet_file: str, y_column: str = "norm_area", y_lim: tuple = (0.5, 1.3)
) -> pd.DataFrame:
    """
    Create a seaborn boxplot from an existing DGGS inspection parquet file.

    Args:
        parquet_file (str): Path to the input parquet file containing DGGS inspection data
        y_column (str): Column name to plot on y-axis (default: "norm_area")
        y_lim (tuple): Y-axis limits as (min, max) tuple (default: (0.5, 1.3))

    Returns:
        pd.DataFrame: Summary statistics dataframe grouped by DGGS type
    """

    # Read the existing parquet file
    gdf = gpd.read_parquet(parquet_file)

    # Convert to regular DataFrame (drop geometry column for plotting)
    df = pd.DataFrame(gdf.drop(columns=["geometry"]))

    # Convert dggs_type to uppercase for display
    df["dggs_type"] = df["dggs_type"].str.upper()

    print(
        f"Loaded data with {len(df)} cells across DGGS types: {df['dggs_type'].unique()}"
    )
    print(f"Resolution range: {df['resolution'].min()}-{df['resolution'].max()}")

    # Create the boxplot
    plt.figure(figsize=(9, 9))

    # Use modern seaborn style
    plt.style.use("default")
    sns.set_style("whitegrid")

    # Define design of the outliers
    outlier_design = dict(
        marker="o",
        markerfacecolor="black",
        markersize=1,
        linestyle="none",
        markeredgecolor="black",
    )

    # Plot the boxplots
    chart = sns.boxplot(
        x="dggs_type",
        y=y_column,
        data=df,
        palette="viridis",
        saturation=0.9,
        showfliers=True,
        flierprops=outlier_design,
    )

    plt.xticks(
        rotation=90,
        horizontalalignment="center",
        fontweight="light",
        fontsize="xx-large",
    )

    plt.xlabel("", fontsize="x-large")

    plt.yticks(
        rotation=0,
        horizontalalignment="right",
        fontweight="light",
        fontsize="xx-large",
    )

    plt.ylabel(y_column, fontsize="xx-large")

    # Set min and max values for y-axis
    plt.ylim(y_lim)

    plt.tight_layout()

    # Save to current directory with predefined filename
    output_file = "box_plot_area.png"
    plt.savefig(output_file, bbox_inches="tight", dpi=300)

    plt.show()

    print("Boxplot created successfully!")
    print(
        f"Data contains {len(df)} cells across DGGS types: {df['dggs_type'].unique()}"
    )
    print(f"Resolution range: {df['resolution'].min()}-{df['resolution'].max()}")

    # Print some summary statistics
    print("\nSummary statistics by DGGS type:")
    summary = df.groupby("dggs_type")[y_column].agg(
        ["count", "mean", "std", "min", "max"]
    )
    print(summary)

    return summary


def dggsboxplot_cli():
    """
    Command-line interface for creating DGGS boxplots from inspection data.

    CLI options:
      --input: Input parquet file path (required)
      --y-column: Column name to plot on y-axis (default: norm_area)
      --y-min: Minimum y-axis value (default: 0.5)
      --y-max: Maximum y-axis value (default: 1.3)
    """

    parser = argparse.ArgumentParser(
        description="Create boxplots from DGGS inspection data"
    )
    parser.add_argument(
        "-input",
        "--input",
        type=str,
        required=True,
        help="Input parquet file path containing DGGS inspection data",
    )
    parser.add_argument(
        "-y",
        "--y-column",
        type=str,
        default="norm_area",
        help="Column name to plot on y-axis (default: norm_area)",
    )
    parser.add_argument(
        "-ymin",
        "--ymin",
        type=float,
        default=0.5,
        help="Minimum y-axis value (default: 0.5)",
    )
    parser.add_argument(
        "-ymax",
        "--ymax",
        type=float,
        default=1.3,
        help="Maximum y-axis value (default: 1.3)",
    )

    args = parser.parse_args()

    try:
        dggsboxplot(
            parquet_file=args.input,
            y_column=args.y_column,
            y_lim=(args.ymin, args.ymax),
        )
    except Exception as e:
        print(f"Error: {e}")
        return None


def dggs_dggridinspect(dggs_type: str = None) -> gpd.GeoDataFrame:
    """
    Generate comprehensive inspection data for DGGS types using DGGS_INSPECT configuration.

    This function calls dggridinspect directly for specified DGGS type(s) defined in DGGS_INSPECT
    and combines them into a single unique GeoDataFrame with a dggs_type column
    to distinguish between different DGGS implementations.

    Args:
        dggs_type (str, optional): Specific DGGS type to process. If None, processes all DGGS types.

    Returns:
        geopandas.GeoDataFrame: Combined DataFrame containing inspection data from DGGS type(s)
            with columns:
            - dggs_type: Type of DGGS (dggrid_isea7h, dggrid_fuller7h, etc.)
            - resolution: Resolution level
            - cell_id: Cell identifier
            - geometry: Cell geometry
            - cell_area: Cell area in square meters
            - cell_perimeter: Cell perimeter in meters
            - crossed: Whether cell crosses the dateline
            - norm_area: Normalized area (cell_area / mean_area)
            - ipq: Isoperimetric Quotient compactness
            - zsc: Zonal Standardized Compactness

    Raises:
        ValueError: If no valid DGGS data could be generated
    """

    # Define DGGS types and their corresponding DGGRID types
    dggs_types = {
        "dggrid_isea4t": "ISEA4T",
        "dggrid_fuller4t": "FULLER4T",
        "dggrid_isea4d": "ISEA4D",
        "dggrid_fuller4d": "FULLER4D",
        "dggrid_isea7h": "ISEA7H",
        "dggrid_fuller7h": "FULLER7H",
    }

    # Filter dggs_types if specific type is requested
    if dggs_type is not None:
        if dggs_type not in dggs_types:
            raise ValueError(
                f"Invalid dggs_type: {dggs_type}. Valid types: {list(dggs_types.keys())}"
            )
        dggs_types = {dggs_type: dggs_types[dggs_type]}

    all_gdfs = []

    # Create dggrid instance once for all dggrid operations
    dggrid_instance = create_dggrid_instance()

    for dggs_type_key, dggrid_type in dggs_types.items():
        if dggs_type_key not in DGGS_INSPECT:
            print(f"Warning: {dggs_type_key} not found in DGGS_INSPECT configuration")
            continue

        inspect_config = DGGS_INSPECT[dggs_type_key]
        min_res = inspect_config["min_res"]
        max_res = inspect_config["max_res"]

        print(f"Processing {dggs_type_key} for resolutions {min_res}-{max_res}")

        for res in range(min_res, max_res + 1):
            try:
                # Call dggridinspect directly
                gdf = dggridinspect(dggrid_instance, dggrid_type, res)

                # Check if the result is empty or has issues
                if gdf is None or len(gdf) == 0:
                    print(
                        f"Warning: dggridinspect returned empty result for {dggs_type_key} at resolution {res}"
                    )
                    continue

                # Add dggs_type column
                gdf["dggs_type"] = dggs_type_key

                # Rename the cell ID column to a generic name
                if "global_id" in gdf.columns:
                    gdf = gdf.rename(columns={"global_id": "cell_id"})
                elif "name" in gdf.columns:
                    gdf = gdf.rename(columns={"name": "cell_id"})
                else:
                    # If neither column exists, create a cell_id column with None values
                    gdf["cell_id"] = None

                # Ensure all expected columns exist, add NaN for missing ones
                expected_columns = [
                    "dggs_type",
                    "resolution",
                    "cell_id",
                    "geometry",
                    "cell_area",
                    "cell_perimeter",
                    "crossed",
                    "norm_area",
                    "ipq",
                    "zsc",
                ]

                for col in expected_columns:
                    if col not in gdf.columns:
                        gdf[col] = None

                # Reorder columns to match expected format
                gdf = gdf[expected_columns]

                all_gdfs.append(gdf)

                # Notify completion for this specific resolution
                print(
                    f"✓ Completed dggridinspect for {dggs_type_key} at resolution {res}"
                )

            except Exception as e:
                print(f"Error processing {dggs_type_key} at resolution {res}: {e}")
                continue

    if not all_gdfs:
        raise ValueError(
            "No valid DGGS data could be generated for the specified resolution range"
        )

    # Combine all GeoDataFrames
    combined_gdf = pd.concat(all_gdfs, ignore_index=True)

    # Ensure it's a GeoDataFrame
    if not isinstance(combined_gdf, gpd.GeoDataFrame):
        combined_gdf = gpd.GeoDataFrame(combined_gdf, geometry="geometry")

    return combined_gdf


def dggs_dggridinspect_cli():
    """
    Command-line interface for multi-DGGS cell inspection using DGGS_INSPECT configuration.
    """

    parser = argparse.ArgumentParser(
        description="Multi-DGGS inspection tool using DGGS_INSPECT configuration"
    )
    parser.add_argument(
        "-dggs",
        "--dggs_type",
        dest="dggs_type",
        type=str,
        default=None,
        help="Specific DGGS type to process. If not provided, processes all DGGS types.",
    )

    args = parser.parse_args()

    try:
        result = dggs_dggridinspect(dggs_type=args.dggs_type)

        if args.dggs_type:
            print(
                f"Generated inspection data for {len(result)} cells for DGGS type: {args.dggs_type}"
            )
            output_file = f"dggs_dggrid_inspect_{args.dggs_type}.parquet"
        else:
            print(
                f"Generated inspection data for {len(result)} cells across multiple DGGS types"
            )
            print(f"DGGS types included: {result['dggs_type'].unique()}")
            output_file = "dggs_dggrid_inspect.parquet"

        print(
            f"Resolution range: {result['resolution'].min()}-{result['resolution'].max()}"
        )

        # Save to current directory with predefined filename
        print(f"Saving GeoDataFrame to: {output_file}")
        result.to_parquet(output_file, index=False)
        print(f"Successfully saved {len(result)} records to {output_file}")

        return result
    except Exception as e:
        print(f"Error: {e}")
        return None


def dggsboxplot_folder(
    folder: str = ".", y_column: str = "norm_area", y_lim: tuple = (0.5, 1.3)
) -> pd.DataFrame:
    """
    Create a seaborn boxplot from DGGS inspection parquet files in a folder.

    Args:
        folder (str): Path to folder containing parquet files (default: current folder ".")
        y_column (str): Column name to plot on y-axis (default: "norm_area")
        y_lim (tuple): Y-axis limits as (min, max) tuple (default: (0.5, 1.3))

    Returns:
        pd.DataFrame: Summary statistics dataframe grouped by DGGS type
    """

    import os
    import glob

    all_gdfs = []

    # Find all parquet files in the specified folder
    parquet_pattern = os.path.join(folder, "*.parquet")
    parquet_files = glob.glob(parquet_pattern)

    if not parquet_files:
        raise ValueError(f"No parquet files found in folder: {folder}")

    print(f"Found {len(parquet_files)} parquet files in {folder}")

    # Read all parquet files
    for parquet_file in parquet_files:
        try:
            gdf = gpd.read_parquet(parquet_file)
            all_gdfs.append(gdf)
            print(f"Loaded {parquet_file} with {len(gdf)} cells")
        except Exception as e:
            print(f"Error reading {parquet_file}: {e}")
            continue

    if not all_gdfs:
        raise ValueError("No valid parquet files could be read")

    # Combine all GeoDataFrames
    combined_gdf = pd.concat(all_gdfs, ignore_index=True)

    # Convert to regular DataFrame (drop geometry column for plotting)
    df = pd.DataFrame(combined_gdf.drop(columns=["geometry"]))

    # Convert dggs_type to uppercase for display
    df["dggs_type"] = df["dggs_type"].str.upper()

    print(
        f"Combined data with {len(df)} cells across DGGS types: {df['dggs_type'].unique()}"
    )
    print(f"Resolution range: {df['resolution'].min()}-{df['resolution'].max()}")

    # Create the boxplot
    plt.figure(figsize=(9, 9))

    # Use modern seaborn style
    plt.style.use("default")
    sns.set_style("whitegrid")

    # Define design of the outliers
    outlier_design = dict(
        marker="o",
        markerfacecolor="black",
        markersize=1,
        linestyle="none",
        markeredgecolor="black",
    )

    # Plot the boxplots
    chart = sns.boxplot(
        x="dggs_type",
        y=y_column,
        data=df,
        palette="viridis",
        saturation=0.9,
        showfliers=True,
        flierprops=outlier_design,
    )

    plt.xticks(
        rotation=90,
        horizontalalignment="center",
        fontweight="light",
        fontsize="xx-large",
    )

    plt.xlabel("", fontsize="x-large")

    plt.yticks(
        rotation=0,
        horizontalalignment="right",
        fontweight="light",
        fontsize="xx-large",
    )

    plt.ylabel(y_column, fontsize="xx-large")

    # Set min and max values for y-axis
    plt.ylim(y_lim)

    plt.tight_layout()

    # Save to current directory with predefined filename
    output_file = "box_plot_area_folder.png"
    plt.savefig(output_file, bbox_inches="tight", dpi=300)

    plt.show()

    print("Boxplot created successfully!")
    print(
        f"Data contains {len(df)} cells across DGGS types: {df['dggs_type'].unique()}"
    )
    print(f"Resolution range: {df['resolution'].min()}-{df['resolution'].max()}")

    # Print some summary statistics
    print("\nSummary statistics by DGGS type:")
    summary = df.groupby("dggs_type")[y_column].agg(
        ["count", "mean", "std", "min", "max"]
    )
    print(summary)

    return summary


def dggsboxplot_folder_cli():
    """
    Command-line interface for creating DGGS boxplots from inspection data files in a folder.

    CLI options:
      --folder: Folder path containing parquet files (default: current folder)
      --y-column: Column name to plot on y-axis (default: norm_area)
      --y-min: Minimum y-axis value (default: 0.5)
      --y-max: Maximum y-axis value (default: 1.3)
    """

    parser = argparse.ArgumentParser(
        description="Create boxplots from DGGS inspection data files in a folder"
    )
    parser.add_argument(
        "-folder",
        "--folder",
        type=str,
        default=".",
        help="Folder path containing parquet files (default: current folder)",
    )
    parser.add_argument(
        "-y",
        "--y-column",
        type=str,
        default="norm_area",
        help="Column name to plot on y-axis (default: norm_area)",
    )
    parser.add_argument(
        "-ymin",
        "--ymin",
        type=float,
        default=0.5,
        help="Minimum y-axis value (default: 0.5)",
    )
    parser.add_argument(
        "-ymax",
        "--ymax",
        type=float,
        default=1.3,
        help="Maximum y-axis value (default: 1.3)",
    )

    args = parser.parse_args()

    try:
        dggsboxplot_folder(
            folder=args.folder, y_column=args.y_column, y_lim=(args.ymin, args.ymax)
        )
    except Exception as e:
        print(f"Error: {e}")


def hilbert_curve(
    dggs_type,
    resolution,
    bbox=None,
    output_format="gpd",
    figsize=(12, 8),
    save_plot=True,
):
    """
    Visualize the Hilbert curve based on the grid returned by calling grid generation functions.

    This function generates a grid using the specified DGGS type and resolution,
    then creates a visualization showing how the cells are ordered along a Hilbert curve.
    The Hilbert curve provides a space-filling curve that preserves spatial locality.

    Args:
        dggs_type (str): Type of DGGS grid to generate (e.g., 'h3', 's2', 'a5', etc.)
        resolution (int): Resolution level for the grid
        bbox (list, optional): Bounding box [min_lon, min_lat, max_lon, max_lat]. Defaults to None (whole world).
        output_format (str, optional): Output format for the grid. Defaults to "gpd".
        figsize (tuple, optional): Figure size for the plot. Defaults to (12, 8).
        save_plot (bool, optional): Whether to save the plot to file. Defaults to True.

    Returns:
        tuple: (GeoDataFrame, matplotlib.figure.Figure) - The generated grid and the plot figure

    Raises:
        ValueError: If the DGGS type is not supported or resolution is invalid
        ImportError: If required visualization libraries are not available

    Example:
        >>> from vgrid.stats.dggsstats import hilbert_curve
        >>> grid, fig = hilbert_curve('h3', 3)
        >>> fig.show()
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        raise ImportError(
            "matplotlib and numpy are required for hilbert curve visualization"
        )

    # Map DGGS types to their grid generation functions
    dggs_grid_functions = {
        "h3": lambda res, bbox=None, output_format="gpd": __import__(
            "vgrid.generator.h3grid", fromlist=["h3grid"]
        ).h3grid(res, bbox, output_format),
        "s2": lambda res, bbox=None, output_format="gpd": __import__(
            "vgrid.generator.s2grid", fromlist=["s2grid"]
        ).s2grid(res, bbox, output_format),
        "a5": lambda res, bbox=None, output_format="gpd": __import__(
            "vgrid.generator.a5grid", fromlist=["a5grid"]
        ).a5grid(res, bbox, output_format),
        "rhealpix": lambda res, bbox=None, output_format="gpd": __import__(
            "vgrid.generator.rhealpixgrid", fromlist=["rhealpixgrid"]
        ).rhealpixgrid(res, bbox, output_format),
        "isea4t": lambda res, bbox=None, output_format="gpd": __import__(
            "vgrid.generator.isea4tgrid", fromlist=["isea4tgrid"]
        ).isea4tgrid(res, bbox, output_format),
        "isea3h": lambda res, bbox=None, output_format="gpd": __import__(
            "vgrid.generator.isea3hgrid", fromlist=["isea3hgrid"]
        ).isea3hgrid(res, bbox, output_format),
        "ease": lambda res, bbox=None, output_format="gpd": __import__(
            "vgrid.generator.easegrid", fromlist=["easegrid"]
        ).easegrid(res, bbox, output_format),
        "qtm": lambda res, bbox=None, output_format="gpd": __import__(
            "vgrid.generator.qtmgrid", fromlist=["qtmgrid"]
        ).qtmgrid(res, bbox, output_format),
        "olc": lambda res, bbox=None, output_format="gpd": __import__(
            "vgrid.generator.olcgrid", fromlist=["olcgrid"]
        ).olcgrid(res, bbox, output_format),
        "geohash": lambda res, bbox=None, output_format="gpd": __import__(
            "vgrid.generator.geohashgrid", fromlist=["geohashgrid"]
        ).geohashgrid(res, bbox, output_format),
        "georef": lambda res, bbox=None, output_format="gpd": __import__(
            "vgrid.generator.georefgrid", fromlist=["georefgrid"]
        ).georefgrid(res, bbox, output_format),
        "mgrs": lambda res, bbox=None, output_format="gpd": __import__(
            "vgrid.generator.mgrsgrid", fromlist=["mgrsgrid"]
        ).mgrsgrid(res, bbox, output_format),
        "tilecode": lambda res, bbox=None, output_format="gpd": __import__(
            "vgrid.generator.tilecodegrid", fromlist=["tilecodegrid"]
        ).tilecodegrid(res, bbox, output_format),
        "quadkey": lambda res, bbox=None, output_format="gpd": __import__(
            "vgrid.generator.quadkeygrid", fromlist=["quadkeygrid"]
        ).quadkeygrid(res, bbox, output_format),
        "maidenhead": lambda res, bbox=None, output_format="gpd": __import__(
            "vgrid.generator.maidenheadgrid", fromlist=["maidenheadgrid"]
        ).maidenheadgrid(res, bbox, output_format),
        "gars": lambda res, bbox=None, output_format="gpd": __import__(
            "vgrid.generator.garsgrid", fromlist=["garsgrid"]
        ).garsgrid(res, bbox, output_format),
    }

    dggs_type = dggs_type.lower()
    if dggs_type not in dggs_grid_functions:
        raise ValueError(
            f"Unsupported DGGS type: {dggs_type}. Supported types: {list(dggs_grid_functions.keys())}"
        )

    # Generate the grid
    print(f"Generating {dggs_type.upper()} grid at resolution {resolution}...")
    grid_gdf = dggs_grid_functions[dggs_type](resolution, bbox, output_format)

    if grid_gdf is None or len(grid_gdf) == 0:
        raise ValueError(
            f"No grid cells generated for {dggs_type} at resolution {resolution}"
        )

    print(f"Generated {len(grid_gdf)} cells. Creating Hilbert curve visualization...")

    # Create the visualization
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)

    # Plot 1: Geographic view with cell ordering
    grid_gdf.plot(
        ax=ax1,
        column=f"{dggs_type}",
        cmap="viridis",
        legend=True,
        legend_kwds={"orientation": "horizontal", "shrink": 0.8},
    )
    ax1.set_title(
        f"{dggs_type.upper()} Grid - Resolution {resolution}\nCell Ordering by ID"
    )
    ax1.set_xlabel("Longitude")
    ax1.set_ylabel("Latitude")
    ax1.grid(True, alpha=0.3)

    # Plot 2: Hilbert curve visualization
    # Extract cell centroids and create a 2D representation
    centroids = grid_gdf.geometry.centroid
    lons = centroids.x.values
    lats = centroids.y.values

    # Normalize coordinates to [0, 1] range for better visualization
    lon_norm = (lons - lons.min()) / (lons.max() - lons.min())
    lat_norm = (lats - lats.min()) / (lats.max() - lats.min())

    # Create a scatter plot showing the spatial distribution
    scatter = ax2.scatter(
        lon_norm, lat_norm, c=range(len(grid_gdf)), cmap="plasma", s=20, alpha=0.7
    )

    # Add colorbar
    cbar = plt.colorbar(scatter, ax=ax2, orientation="horizontal", shrink=0.8)
    cbar.set_label("Cell Order")

    ax2.set_title(
        f"Hilbert Curve Visualization\n{dggs_type.upper()} Resolution {resolution}"
    )
    ax2.set_xlabel("Normalized Longitude")
    ax2.set_ylabel("Normalized Latitude")
    ax2.grid(True, alpha=0.3)
    ax2.set_aspect("equal")

    # Add statistics text
    stats_text = f"Total Cells: {len(grid_gdf)}\nResolution: {resolution}\nDGGS Type: {dggs_type.upper()}"
    if bbox:
        stats_text += f"\nBBox: {bbox}"

    fig.text(
        0.02,
        0.02,
        stats_text,
        fontsize=10,
        verticalalignment="bottom",
        bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8),
    )

    plt.tight_layout()

    # Save the plot if requested
    if save_plot:
        output_filename = f"{dggs_type}_hilbert_curve_res_{resolution}.png"
        plt.savefig(output_filename, dpi=300, bbox_inches="tight")
        print(f"Hilbert curve visualization saved as: {output_filename}")

    return grid_gdf, fig


def hilbert_curve_cli():
    """CLI interface for visualizing Hilbert curves."""
    parser = argparse.ArgumentParser(
        description="Visualize Hilbert curve for DGGS grids."
    )
    parser.add_argument(
        "dggs_type", type=str, help="DGGS type (e.g., h3, s2, a5, rhealpix, etc.)"
    )
    parser.add_argument(
        "-r", "--resolution", type=int, required=True, help="Resolution level"
    )
    parser.add_argument(
        "-b",
        "--bbox",
        type=float,
        nargs=4,
        help="Bounding box: <min_lon> <min_lat> <max_lon> <max_lat> (default is the whole world)",
    )
    parser.add_argument(
        "-f",
        "--output_format",
        type=str,
        choices=["gpd", "geojson", "shp", "gpkg", "parquet"],
        default="gpd",
        help="Output format for the grid",
    )
    parser.add_argument(
        "--no-save", action="store_true", help="Don't save the plot to file"
    )

    args = parser.parse_args()

    try:
        result, fig = hilbert_curve(
            args.dggs_type,
            args.resolution,
            args.bbox,
            args.output_format,
            save_plot=not args.no_save,
        )

        print(f"Grid generated with {len(result)} cells")
        print("Hilbert curve visualization created successfully!")
        plt.show()

    except Exception as e:
        print(f"Error: {str(e)}")
        return


if __name__ == "__main__":
    dggsinspect_cli()
