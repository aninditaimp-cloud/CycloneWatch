
import geopandas as gpd
from pathlib import Path

DATA_FOLDER = Path(__file__).resolve().parent / "data"

# Search inside all subfolders as well
shapefiles = list(DATA_FOLDER.rglob("*.shp"))

if not shapefiles:
    print("ERROR: No shapefile found inside the data folder.")

elif len(shapefiles) > 1:
    print("Multiple shapefiles found:")
    for file in shapefiles:
        print(file)

else:
    shapefile = shapefiles[0]

    print("SATELLITE DATASET INSPECTION")
    print("----------------------------")
    print("File:", shapefile.name)
    print("Location:", shapefile.parent)

    data = gpd.read_file(shapefile)

    print("\nCoordinate Reference System:")
    print(data.crs)

    print("\nGeometry types:")
    print(data.geom_type.value_counts())

    print("\nNumber of features:")
    print(len(data))

    print("\nAvailable attributes:")
    print(data.columns.tolist())

    print("\nGeographical bounds:")
    print(data.total_bounds)

    print("\nFirst five records:")
    print(data.head().to_string())

    print("\nDataset inspection completed.")
