import matplotlib.pyplot as plt
import geopandas as gpd
import pandas as pd

df = pd.read_csv("data/indicateur.csv")
gdf = gpd.read_file("maps/pays.shp")
df.set_index("ID", inplace=True)
gdf.set_index("CNTR_ID", inplace=True)
gdf = gdf.join(df).fillna(0)


ax = plt.axes(frameon=False)
x_axis = ax.axes.get_xaxis()
x_axis.set_visible(False)
y_axis = ax.axes.get_yaxis()
y_axis.set_visible(False)
gdf.plot(column="intensity", legend=True, cmap="RdYlGn_r", figsize=(10, 10), legend_kwds={"shrink":0.4, "label": "CO$_2$ intensity (kCO2/MWh)"}, ax=ax)
plt.title("Intensity")
plt.savefig("output/intensite_co2.png", dpi=300, bbox_inches="tight")
plt.show()
plt.close()