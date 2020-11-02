# coding: utf-8
import math

# libraries
import geopandas as gpd
import matplotlib as mpl
import matplotlib.gridspec as gridspec
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Paramètres
# Taille de l'image
figsize = (10, 10)
# Résolution de l'image
dpi = 200
# Taille des ronds bleus
markersize = 500
# Taille de police des noms des pays
fontsize = 12
# Paramètre de décalage des flèches
factormarker = 150
# Colormap des flèches
colormaparrows = mpl.cm.get_cmap("RdYlGn_r", 25)
# Courbure des flèches
radius_arrow = 0.05
# Activer ronds non concernés
enable_non_used_country_names = False
# Paramètres caractéristiques des flèches
param_arrows = "head_width=2, head_length=3"
arrowswidth = 2
# Angle offset
angle_offset = math.pi / 8
# IDs to replace in data
countries_id_to_replace = {"GR": "EL"}
# Input file
INPUT_FILE = "input_data"
OUTPUT_FILENAME = "test"


# Cartes
pays_europeens = gpd.read_file("cartes/pays.shp", encoding="utf-8")
centroids = gpd.read_file("cartes/pays_centroids.shp", encoding="utf-8")

# Données des échanges
df = pd.read_csv(f"data/{INPUT_FILE}.csv")
df.replace(to_replace=countries_id_to_replace, inplace=True)

# On calcule l'étendue de valeurs
data_extent = df["Value"].max() - df["Value"].min()

# On récupère juste les coordonnées des centroids (préalablement calculés)
centroids["coords"] = centroids["geometry"].apply(lambda x: x.coords[:])
centroids["coords"] = [coords[0] for coords in centroids["coords"]]


def plot_fond_de_carte(ax):
    """
    Affiche le fond de carte avec les contours des pays européens
    """
    pays_europeens.plot(color="white", linewidth=0.5, edgecolor="gray", ax=ax, zorder=1)


def plot_noms_pays(ax):
    """
    Affiche les noms des pays dans une bulle bleue. Calcule également les localisations
    des-dits pays.

    :return: dictionnaire des coordonnées selon l'ID (2 lettres) des pays
    :rtype: dict
    """
    # Pour chaque centroid on affiche un gros rond bleu
    if not enable_non_used_country_names:
        filtered_centroids = centroids.loc[
            (centroids["CNTR_ID"].isin(df["Export"]))
            | (centroids["CNTR_ID"].isin(df["Import"]))
        ]
    else:
        filtered_centroids = centroids

    filtered_centroids.plot(
        ax=ax, marker="o", color="#4897CA", markersize=markersize, zorder=4
    )

    countries_locations = {}
    # On affiche ensuite les initiales du pays sur chaque rond
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


def plot_map(filename="test"):
    """
    Dessine la carte avec les flèches

    :param filename: nom du fichier de sortie, dans dossier output, defaults to "test"
    :type filename: str, optional
    """
    plt.figure(figsize=figsize, dpi=dpi)

    # On crée la grille avec les ratios pour la colorbar de droite
    gs = gridspec.GridSpec(3, 2, width_ratios=[75, 1], height_ratios=[1, 3, 1])

    # Emplacement de la carte
    ax = plt.subplot(gs[:, 0], frameon=False)
    x_axis = ax.axes.get_xaxis()
    x_axis.set_visible(False)
    y_axis = ax.axes.get_yaxis()
    y_axis.set_visible(False)

    # Fond de carte
    plot_fond_de_carte(ax)

    # Ronds pays
    countries_locations = plot_noms_pays(ax)

    # Il faut maintenant calculer les flèches
    already_drawn = []
    for idx, row in df.iterrows():
        coords_export = countries_locations[row["Export"]]
        coords_import = countries_locations[row["Import"]]

        # On crée un identifiant unique pour la paire export/import
        # pour éviter de tracer la flèche deux fois au même endroit
        joint_name = "".join(sorted([row["Export"], row["Import"]]))
        # Si la flèche a déjà été tracée, on l'inverse
        if joint_name in already_drawn:
            inverse = -1.0
        else:
            inverse = 1.0

        # On récupère le point à gauche et celui à droite
        left_dot = (
            coords_export if coords_export[0] < coords_import[0] else coords_import
        )
        right_dot = (
            coords_export if coords_export[0] > coords_import[0] else coords_import
        )
        inverted_left_right = "->" if coords_export[0] < coords_import[0] else "<-"

        # On détermine lequel est le plus haut (change la valeur des signes de décalage)
        if left_dot[1] > right_dot[1]:
            left_upper = 1.0
        else:
            left_upper = -1.0

        # On calcule l'angle entre les deux points
        alpha = math.atan((left_dot[1] - right_dot[1]) / (left_dot[0] - right_dot[0]))

        # Si on a inversé la flèche, on la trace "au-dessus" du segment reliant les deux points
        # c'est-à-dire on ajoute un petit angle de décalage positif
        # Sinon, on trace "en-dessous" du segment
        if inverse > 0:
            betaleft = alpha - left_upper * angle_offset
            betaright = alpha + left_upper * angle_offset
        else:
            betaleft = alpha + left_upper * angle_offset
            betaright = alpha - left_upper * angle_offset

        # On calcule les nouvelles coordonnées des points
        new_left_dot = (
            left_dot[0] + markersize * factormarker * math.cos(betaleft),
            left_dot[1] + markersize * factormarker * math.sin(betaleft),
        )
        new_right_dot = (
            right_dot[0] - markersize * factormarker * math.cos(betaright),
            right_dot[1] - markersize * factormarker * math.sin(betaright),
        )

        # On crée la flèche
        arrow = patches.FancyArrowPatch(
            new_left_dot,
            new_right_dot,
            connectionstyle=patches.ConnectionStyle.Arc3(
                rad=inverse * left_upper * radius_arrow
            ),
            color=colormaparrows(row["Value"] / data_extent),
            linewidth=arrowswidth,
            arrowstyle=f"{inverted_left_right}, {param_arrows}",
            zorder=2,
        )
        plt.gca().add_patch(arrow)

        # On ajoute la paire Import/Export aux flèches déjà tracées
        already_drawn.append(joint_name)

    # On ajoute la colorbar à droite
    ax2 = plt.subplot(gs[1, 1])
    # On utilise le min - max des valeurs pour la tracer
    norm = mpl.colors.Normalize(vmin=df["Value"].min(), vmax=df["Value"].max())

    cb1 = mpl.colorbar.ColorbarBase(
        ax2, cmap=colormaparrows, norm=norm, orientation="vertical"
    )

    # On enregistre le fichier
    plt.tight_layout()
    plt.savefig(f"output/{filename}.png", dpi=dpi, bbox_inches="tight")
    plt.close()

    print("Plots succeeded...")


plot_map(OUTPUT_FILENAME)
