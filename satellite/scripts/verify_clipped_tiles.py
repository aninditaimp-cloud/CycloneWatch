
import geopandas as gpd
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
TILES_FOLDER = BASE_DIR / "tiles"
INDEX_FILE = BASE_DIR / "tile_index.json"

with open(INDEX_FILE, "r", encoding="utf-8") as file:
    grid = json.load(file)

min_x = grid["min_longitude"]
min_y = grid["min_latitude"]
tile_width = grid["tile_width"]
tile_height = grid["tile_height"]

checked = 0
invalid = 0
outside = 0
non_polygon = 0

print("CYCLONEWATCH CLIPPED TILE VERIFICATION")
print("--------------------------------------")

for tile_file in sorted(TILES_FOLDER.glob("tile_*.geojson")):
    parts = tile_file.stem.split("_")
    row = int(parts[1]) - 1
    column = int(parts[2]) - 1

    left = min_x + column * tile_width
    right = min_x + (column + 1) * tile_width
    bottom = min_y + row * tile_height
    top = min_y + (row + 1) * tile_height

    tile = gpd.read_file(tile_file)

    for geom in tile.geometry:
        checked += 1

        if geom is None or geom.is_empty:
            invalid += 1
            continue

        if geom.geom_type not in ("Polygon", "MultiPolygon"):
            non_polygon += 1
            continue

        if not geom.is_valid:
            invalid += 1

        tolerance = 1e-9

        if (
            geom.bounds[0] < left - tolerance
            or geom.bounds[1] < bottom - tolerance
            or geom.bounds[2] > right + tolerance
            or geom.bounds[3] > top + tolerance
        ):
            outside += 1

    print(f"{tile_file.name}: {len(tile)} features checked")

print("\nVERIFICATION SUMMARY")
print("--------------------")
print("Total features checked:", checked)
print("Invalid geometries:", invalid)
print("Non-polygon geometries:", non_polygon)
print("Features outside tile boundaries:", outside)

if invalid == 0 and non_polygon == 0 and outside == 0:
    print("\nSUCCESS: All clipped tile geometries passed.")
else:
    print("\nWARNING: Some geometries need correction.")
