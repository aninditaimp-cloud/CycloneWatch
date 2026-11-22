
import geopandas as gpd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

original_file = BASE_DIR / "flood_zones.geojson"
tiles_folder = BASE_DIR / "tiles"

print("Checking original dataset...")
original = gpd.read_file(original_file)
original_count = len(original)

print("Original features:", original_count)

print("\nChecking tile files...")

tile_files = list(tiles_folder.glob("*.geojson"))
total_tile_features = 0

for file in tile_files:
    tile = gpd.read_file(file)
    count = len(tile)
    total_tile_features += count
    print(f"{file.name}: {count} features")

print("\nVERIFICATION RESULT")
print("-------------------")
print("Original features:", original_count)
print("Features in all tiles:", total_tile_features)
print("Number of tile files:", len(tile_files))

if original_count == total_tile_features:
    print("SUCCESS: All features are accounted for.")
else:
    print("WARNING: Feature count mismatch.")

