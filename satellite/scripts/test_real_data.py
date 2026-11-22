
import geopandas as gpd
import sys
from pathlib import Path
from shapely.geometry import mapping

# Locate project folders
BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent

sys.path.insert(0, str(BASE_DIR))

from satellite_analysis import point_in_geometry

TILES_FOLDER = BASE_DIR / "tiles"

print("CYCLONEWATCH REAL SATELLITE DATA TEST")
print("-------------------------------------")

# Load one actual tile
tile_files = sorted(TILES_FOLDER.glob("*.geojson"))

if not tile_files:
    raise FileNotFoundError("No GeoJSON tiles found.")

tile = gpd.read_file(tile_files[0])

if tile.empty:
    raise ValueError("The selected tile contains no features.")

# Select an actual flood polygon
flood_polygon = tile.geometry.iloc[0]

# Generate a point guaranteed to lie within that polygon
test_point = flood_polygon.representative_point()

latitude = test_point.y
longitude = test_point.x

# Convert the actual polygon into GeoJSON geometry
geometry = mapping(flood_polygon)

print("\nSource tile:", tile_files[0].name)
print("Test latitude:", latitude)
print("Test longitude:", longitude)

# Test the existing point-in-polygon function
result = point_in_geometry(
    latitude,
    longitude,
    geometry
)

print("\nREAL FLOOD POLYGON TEST")
print("-----------------------")
print("Location inside polygon:", result)

if result:
    print("SUCCESS: Actual satellite geometry was detected.")
else:
    print("ERROR: Expected the point to be inside the polygon.")
