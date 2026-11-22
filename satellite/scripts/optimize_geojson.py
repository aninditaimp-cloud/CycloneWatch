
import geopandas as gpd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

INPUT_FILE = BASE_DIR / "flood_zones.geojson"
OUTPUT_FILE = BASE_DIR / "flood_zones_light.geojson"

print("Loading original flood-zone data...")
data = gpd.read_file(INPUT_FILE)

print("Original features:", len(data))

# Simplify polygon boundaries to reduce file size.
# Tolerance is in degrees because the data uses EPSG:4326.
print("\nSimplifying geometries...")

data["geometry"] = data.geometry.simplify(
    tolerance=0.00005,
    preserve_topology=True
)

# Remove any empty geometries
data = data[~data.geometry.is_empty].copy()

print("\nSaving lightweight GeoJSON...")

data.to_file(
    OUTPUT_FILE,
    driver="GeoJSON",
    index=False
)

print("\nOPTIMIZATION COMPLETED")
print("----------------------")
print("Features:", len(data))
print("Original size:", round(INPUT_FILE.stat().st_size / (1024 * 1024), 2), "MB")
print("Optimized size:", round(OUTPUT_FILE.stat().st_size / (1024 * 1024), 2), "MB")
print("Remaining invalid geometries:", (~data.geometry.is_valid).sum())
