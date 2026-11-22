
import geopandas as gpd
import matplotlib.pyplot as plt
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
geojson_file = BASE_DIR / "flood_zones.geojson"

print("Loading flood-zone data...")
data = gpd.read_file(geojson_file)

print("Creating preview...")

fig, ax = plt.subplots(figsize=(10, 10))

data.plot(
    ax=ax,
    color="deepskyblue",
    edgecolor="none"
)

ax.set_title("Detected Flood Water - 29 May 2021")
ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")
ax.set_aspect("equal")

plt.tight_layout()

output = BASE_DIR / "flood_preview.png"
plt.savefig(output, dpi=150)
plt.show()

print("Preview saved at:", output)
