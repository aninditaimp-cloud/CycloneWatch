
import geopandas as gpd
from collections import Counter
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
TILES_FOLDER = BASE_DIR / "tiles"

counts = Counter()

print("CHECKING GEOMETRY TYPES")
print("-----------------------")

for tile_file in sorted(TILES_FOLDER.glob("tile_*.geojson")):
    tile = gpd.read_file(tile_file)

    for geometry in tile.geometry:
        if geometry is None:
            counts["None"] += 1
        else:
            counts[geometry.geom_type] += 1

    print("Checked:", tile_file.name)

print("\nFINAL GEOMETRY COUNTS")
print("---------------------")

for geometry_type, count in counts.items():
    print(f"{geometry_type}: {count}")

print("\nTotal:", sum(counts.values()))
