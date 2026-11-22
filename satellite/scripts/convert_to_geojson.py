
import geopandas as gpd
from pathlib import Path

# Locate the original shapefile
BASE_DIR = Path(__file__).resolve().parent
DATA_FOLDER = BASE_DIR / "data"
OUTPUT_FILE = BASE_DIR / "flood_zones.geojson"

shapefiles = list(DATA_FOLDER.rglob("*.shp"))

if len(shapefiles) != 1:
    raise RuntimeError(
        f"Expected one shapefile, but found {len(shapefiles)}"
    )

shapefile = shapefiles[0]

print("Reading satellite dataset...")
data = gpd.read_file(shapefile)

print("Original features:", len(data))

# Repair invalid geometries
print("\nRepairing invalid geometries...")
data["geometry"] = data.geometry.make_valid()

# Keep only polygon-based geometries
data = data[
    data.geometry.geom_type.isin(["Polygon", "MultiPolygon"])
].copy()

# Remove empty geometries
data = data[~data.geometry.is_empty].copy()

# Prepare useful properties for CycloneWatch
data = data.rename(columns={
    "FID_1": "zone_id",
    "VALUE": "value"
})

data["source_dataset"] = shapefile.name
data["observation_date"] = "2021-05-29"

# Export to GeoJSON
print("\nExporting GeoJSON...")
data.to_file(
    OUTPUT_FILE,
    driver="GeoJSON",
    index=False
)

print("\nEXPORT COMPLETED")
print("----------------")
print("Output:", OUTPUT_FILE)
print("Features exported:", len(data))
print("Remaining invalid geometries:", (~data.geometry.is_valid).sum())
print("Output size:", round(OUTPUT_FILE.stat().st_size / (1024 * 1024), 2), "MB")
