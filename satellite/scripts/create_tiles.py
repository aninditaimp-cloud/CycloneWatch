
import geopandas as gpd
import json
from pathlib import Path
from shapely.geometry import box, Polygon, MultiPolygon
from shapely.ops import unary_union

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_FILE = BASE_DIR / "flood_zones.geojson"
OUTPUT_FOLDER = BASE_DIR / "tiles"
INDEX_FILE = BASE_DIR / "tile_index.json"

GRID_COLUMNS = 4
GRID_ROWS = 6


def extract_polygons(geometry):
    """Keep polygon components and discard lines and points."""

    if geometry is None or geometry.is_empty:
        return None

    if isinstance(geometry, (Polygon, MultiPolygon)):
        return geometry

    if geometry.geom_type == "GeometryCollection":
        polygons = []

        for part in geometry.geoms:
            result = extract_polygons(part)

            if result is not None:
                if isinstance(result, Polygon):
                    polygons.append(result)
                elif isinstance(result, MultiPolygon):
                    polygons.extend(result.geoms)

        if polygons:
            return unary_union(polygons)

    return None


print("Loading satellite flood data...")
data = gpd.read_file(INPUT_FILE)

if data.crs is None:
    raise ValueError("Dataset has no CRS.")

if data.crs.to_epsg() != 4326:
    data = data.to_crs("EPSG:4326")

data = data[data.geometry.notna() & ~data.geometry.is_empty].copy()

print("Original features:", len(data))

min_x, min_y, max_x, max_y = data.total_bounds

tile_width = (max_x - min_x) / GRID_COLUMNS
tile_height = (max_y - min_y) / GRID_ROWS

grid_info = {
    "crs": "EPSG:4326",
    "min_longitude": float(min_x),
    "min_latitude": float(min_y),
    "max_longitude": float(max_x),
    "max_latitude": float(max_y),
    "grid_columns": GRID_COLUMNS,
    "grid_rows": GRID_ROWS,
    "tile_width": float(tile_width),
    "tile_height": float(tile_height)
}

OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

for old_file in OUTPUT_FOLDER.glob("tile_*.geojson"):
    old_file.unlink()

print("\nCreating clean clipped tiles...")

spatial_index = data.sindex

tile_count = 0
exported_features = 0
discarded_geometries = 0

for row in range(GRID_ROWS):
    for column in range(GRID_COLUMNS):

        left = min_x + column * tile_width
        right = min_x + (column + 1) * tile_width
        bottom = min_y + row * tile_height
        top = min_y + (row + 1) * tile_height

        tile_bounds = box(left, bottom, right, top)

        candidate_indices = spatial_index.query(
            tile_bounds,
            predicate="intersects"
        )

        if len(candidate_indices) == 0:
            continue

        tile = data.iloc[candidate_indices].copy()

        clipped_geometries = []
        keep_indices = []

        for index, geometry in zip(tile.index, tile.geometry):
            clipped = geometry.intersection(tile_bounds)
            polygonal = extract_polygons(clipped)

            if polygonal is not None and not polygonal.is_empty:
                clipped_geometries.append(polygonal)
                keep_indices.append(index)
            else:
                discarded_geometries += 1

        tile = tile.loc[keep_indices].copy()
        tile.geometry = clipped_geometries

        if tile.empty:
            continue

        filename = f"tile_{row + 1}_{column + 1}.geojson"
        output_path = OUTPUT_FOLDER / filename

        tile.to_file(
            output_path,
            driver="GeoJSON",
            index=False
        )

        tile_count += 1
        exported_features += len(tile)

        print(f"{filename}: {len(tile)} polygon features")

with open(INDEX_FILE, "w", encoding="utf-8") as file:
    json.dump(grid_info, file, indent=4)

print("\nTILING COMPLETED")
print("----------------")
print("Tiles created:", tile_count)
print("Original features:", len(data))
print("Exported polygon features:", exported_features)
print("Empty/non-polygon results discarded:", discarded_geometries)
print("Grid metadata:", INDEX_FILE)
print("SUCCESS: Only polygonal flood geometries were retained.")
