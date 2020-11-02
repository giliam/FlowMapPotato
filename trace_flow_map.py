# coding: utf-8
import math
import logging

# libraries
import geopandas as gpd
import matplotlib as mpl
import matplotlib.gridspec as gridspec
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Enables logging
logging.basicConfig(level=logging.INFO)

# Parameters
# Picture size
figsize = (10, 10)
# Image resolution
dpi = 200
# Size of countries circles
markersize = 500
# Country color
country_bubblecolor = "#4897CA"
# Country name font size
fontsize = 12
# Arrow offset from circle
factormarker = 150
# Arrows color map
colormaparrows = mpl.cm.get_cmap("RdYlGn_r", 25)
# Arrows radius of curvature
radius_arrow = 0.05
# Enable countries non used
enable_non_used_country_names = False
# Additional arrows parameters
param_arrows = "head_width=2, head_length=3"
arrowswidth = 2
# Angle offset
angle_offset = math.pi / 8
# IDs to replace in data
countries_id_to_replace = {"GR": "EL"}
# Input file
INPUT_FILE = "input_data"
OUTPUT_FILENAME = "test"


# Maps
logging.info("Imports maps")
pays_europeens = gpd.read_file("maps/pays.shp", encoding="utf-8")
centroids = gpd.read_file("maps/pays_centroids.shp", encoding="utf-8")

# Exchange data
logging.info("Imports input data in data/%s.csv", INPUT_FILE)
df = pd.read_csv(f"data/{INPUT_FILE}.csv")
df.replace(to_replace=countries_id_to_replace, inplace=True)

# We get centroids coordinates
centroids["coords"] = centroids["geometry"].apply(lambda x: x.coords[:])
centroids["coords"] = [coords[0] for coords in centroids["coords"]]


def plot_countries_layer(ax):
    """
    Display the countries layer
    """
    pays_europeens.plot(color="white", linewidth=0.5, edgecolor="gray", ax=ax, zorder=1)


def plot_countries_names(ax):
    """
    Display the countries IDs in colored bubble.

    :return: countries bubbles coordinates dict by ID (2 letters)
    :rtype: dict
    """
    # For each centroid, we add a bubble if used in flows
    if not enable_non_used_country_names:
        filtered_centroids = centroids.loc[
            (centroids["CNTR_ID"].isin(df["Export"]))
            | (centroids["CNTR_ID"].isin(df["Import"]))
        ]
    else:
        filtered_centroids = centroids
    filtered_centroids.plot(
        ax=ax, marker="o", color=country_bubblecolor, markersize=markersize, zorder=4
    )

    countries_locations = {}
    # We then display ID on each bubble
    for idx, row in filtered_centroids.iterrows():
        row["coords"] = (row["coords"][0], row["coords"][1])
        plt.text(
            x=row["coords"][0],
            y=row["coords"][1],
            s=row["CNTR_ID"],
            horizontalalignment="center",
            verticalalignment="center",
            size=fontsize,
            color="white",
            zorder=4,
        )
        countries_locations[row["CNTR_ID"]] = row["coords"]
    return countries_locations


def plot_map(filename="test", title=None):
    """
    Draws flow map

    :param filename: output file name in folder outputs (default: test)
    :type filename: str, optional
    """
    plt.figure(figsize=figsize, dpi=dpi)

    # We create the grid for map and colorbar
    gs = gridspec.GridSpec(3, 2, width_ratios=[75, 1], height_ratios=[1, 3, 1])

    # Removes axis and frame
    ax = plt.subplot(gs[:, 0], frameon=False)
    x_axis = ax.axes.get_xaxis()
    x_axis.set_visible(False)
    y_axis = ax.axes.get_yaxis()
    y_axis.set_visible(False)

    # Countries boundaries
    logging.info("Plots countries")
    plot_countries_layer(ax)

    # Bubbles
    logging.info("Plots names")
    countries_locations = plot_countries_names(ax)

    # We compute data extent of flows (for colorbar)
    data_extent = df["Value"].max() - df["Value"].min()

    # Arrows
    logging.info("Computes arrows")
    already_drawn = []
    for idx, row in df.iterrows():
        coords_export = countries_locations[row["Export"]]
        coords_import = countries_locations[row["Import"]]

        # Unique ID for export/import couple to avoid plotting the two sides
        # arrows at the same spot
        joint_name = "".join(sorted([row["Export"], row["Import"]]))

        # If the couple has already been involved, we have to revert the arrow
        if joint_name in already_drawn:
            revert_arrow = -1.0
        else:
            revert_arrow = 1.0

        # We get left and right dot
        left_dot = (
            coords_export if coords_export[0] < coords_import[0] else coords_import
        )
        right_dot = (
            coords_export if coords_export[0] > coords_import[0] else coords_import
        )
        inverted_left_right = "->" if coords_export[0] < coords_import[0] else "<-"

        # We determine which one is higher
        if left_dot[1] > right_dot[1]:
            left_upper = 1.0
        else:
            left_upper = -1.0

        # We compute angle between both points
        alpha = math.atan((left_dot[1] - right_dot[1]) / (left_dot[0] - right_dot[0]))

        # If we reverted the arrow, we plot it "above" the line between the points
        # i.e. with a small angle offset
        # otherwise, we plot it "below"
        if revert_arrow > 0:
            betaleft = alpha - left_upper * angle_offset
            betaright = alpha + left_upper * angle_offset
        else:
            betaleft = alpha + left_upper * angle_offset
            betaright = alpha - left_upper * angle_offset

        # We compute the new coordinates
        new_left_dot = (
            left_dot[0] + markersize * factormarker * math.cos(betaleft),
            left_dot[1] + markersize * factormarker * math.sin(betaleft),
        )
        new_right_dot = (
            right_dot[0] - markersize * factormarker * math.cos(betaright),
            right_dot[1] - markersize * factormarker * math.sin(betaright),
        )

        # On create the arrow
        arrow = patches.FancyArrowPatch(
            new_left_dot,
            new_right_dot,
            connectionstyle=patches.ConnectionStyle.Arc3(
                rad=revert_arrow * left_upper * radius_arrow
            ),
            color=colormaparrows(row["Value"] / data_extent),
            linewidth=arrowswidth,
            arrowstyle=f"{inverted_left_right}, {param_arrows}",
            zorder=2,
        )
        plt.gca().add_patch(arrow)

        # We add the couple to already drawn couples
        already_drawn.append(joint_name)

    # Colorbar
    logging.info("Adds colorbar")
    ax2 = plt.subplot(gs[1, 1])
    # We use max - min values for normalization
    norm = mpl.colors.Normalize(vmin=df["Value"].min(), vmax=df["Value"].max())

    cb1 = mpl.colorbar.ColorbarBase(
        ax2, cmap=colormaparrows, norm=norm, orientation="vertical"
    )

    # We add suptitle
    plt.suptitle(title)
    # Saving file
    logging.info("Saves output!")
    plt.tight_layout()
    plt.savefig(f"output/{filename}.png", dpi=dpi, bbox_inches="tight")
    plt.close()

    logging.info("Plots succeeded!")


plot_map(OUTPUT_FILENAME)
