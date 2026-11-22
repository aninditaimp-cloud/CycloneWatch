
import geopandas as gpd
from pathlib import Path

data_folder = Path(__file__).resolve().parent / "data"
shapefile = next(data_folder.rglob("*.shp"))

data = gpd.read_file(shapefile)

print("DATASET QUALITY CHECK")
print("---------------------")

print("\nVALUE categories:")
print(data["VALUE"].value_counts(dropna=False))

print("\nValid geometries:", data.geometry.is_valid.sum())
print("Invalid geometries:", (~data.geometry.is_valid).sum())

print("\nEmpty geometries:", data.geometry.is_empty.sum())

print("\nMissing geometries:", data.geometry.isna().sum())

print("\nDataset file size:")
print(round(shapefile.stat().st_size / (1024 * 1024), 2), "MB")

print("\nGeometry bounds:")
print(data.total_bounds)

print("\nCheck completed.")
