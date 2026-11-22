
import geopandas as gpd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

INPUT_FILE = BASE_DIR / "flood_zones.geojson"
OUTPUT_FILE = BASE_DIR / "flood_zones_mobile.geojson"

print("Loading original flood data...")
data = gpd.read_file(INPUT_FILE)

print("Original features:", len(data))

# Merge connected flood polygons with the same VALUE
print("\nMerging neighbouring flood polygons...")

merged = data.dissolve(
    by="value",
    as_index=False
)

print("Features after merging:", len(merged))

# Simplify the merged boundaries
print("\nSimplifying merged boundaries...")

merged["geometry"] = merged.geometry.simplify(
    tolerance=0.0001,
    preserve_topology=True
)

# Save the mobile version
print("\nExporting mobile GeoJSON...")

merged.to_file(
    OUTPUT_FILE,
    driver="GeoJSON",
    index=False
)

print("\nMOBILE DATA EXPORT")
print("------------------")
print("Features:", len(merged))
print("File size:", round(OUTPUT_FILE.stat().st_size / (1024 * 1024), 2), "MB")
print("Invalid geometries:", (~merged.geometry.is_valid).sum())
print("Output:", OUTPUT_FILE)
