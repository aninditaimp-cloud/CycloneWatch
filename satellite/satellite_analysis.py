from functools import lru_cache
import json
import math
from pathlib import Path

# Always locate data files relative to this Python file
BASE_DIR = Path(__file__).resolve().parent

METADATA_FILE = BASE_DIR / "impact_data.json"
GEOJSON_FILE = BASE_DIR / "flood_zones.geojson"
TILES_FOLDER = BASE_DIR / "tiles"
TILE_INDEX_FILE = BASE_DIR / "tile_index.json"


def load_impact_metadata():
    """Load information about the satellite event."""

    if not METADATA_FILE.exists():
        raise FileNotFoundError("impact_data.json was not found.")

    with open(METADATA_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def load_flood_zones():
    """Load flood-zone boundaries from a GeoJSON file."""

    if not GEOJSON_FILE.exists():
        raise FileNotFoundError("flood_zones.geojson was not found.")

    with open(GEOJSON_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)

    if data.get("type") != "FeatureCollection":
        raise ValueError("GeoJSON must be a FeatureCollection.")

    if not isinstance(data.get("features"), list):
        raise ValueError("GeoJSON features must be a list.")

    return data["features"]

@lru_cache(maxsize=24)
def load_tile_features(tile_path):
    """Load and cache one satellite tile."""

    with open(tile_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    if data.get("type") != "FeatureCollection":
        raise ValueError(f"Invalid GeoJSON tile: {tile_path}")

    return data["features"]


def find_relevant_tiles(latitude, longitude):
    """Find every tile containing the given point, including boundaries."""

    if not TILE_INDEX_FILE.exists():
        raise FileNotFoundError("tile_index.json was not found.")

    with open(TILE_INDEX_FILE, "r", encoding="utf-8") as file:
        grid = json.load(file)

    min_x = grid["min_longitude"]
    min_y = grid["min_latitude"]
    tile_width = grid["tile_width"]
    tile_height = grid["tile_height"]

    columns = grid["grid_columns"]
    rows = grid["grid_rows"]

    tolerance = 1e-10
    relevant_tiles = []

    # Check all grid cells. There are only 24, so this is inexpensive.
    for row in range(rows):
        for column in range(columns):

            left = min_x + column * tile_width
            right = left + tile_width
            bottom = min_y + row * tile_height
            top = bottom + tile_height

            inside_longitude = (
                left - tolerance <= longitude <= right + tolerance
            )

            inside_latitude = (
                bottom - tolerance <= latitude <= top + tolerance
            )

            if inside_longitude and inside_latitude:

                filename = f"tile_{row + 1}_{column + 1}.geojson"
                tile_path = TILES_FOLDER / filename

                if tile_path.exists():
                    relevant_tiles.append(tile_path)

    return relevant_tiles

def is_valid_location(latitude, longitude):
    """Check whether latitude and longitude are valid."""

    return (
        isinstance(latitude, (int, float))
        and isinstance(longitude, (int, float))
        and math.isfinite(latitude)
        and math.isfinite(longitude)
        and -90 <= latitude <= 90
        and -180 <= longitude <= 180
    )


def point_on_segment(point, start, end):
    """Check whether a point lies on a polygon boundary."""

    x, y = point
    x1, y1 = start
    x2, y2 = end

    cross = (x - x1) * (y2 - y1) - (y - y1) * (x2 - x1)

    if abs(cross) > 1e-10:
        return False

    return (
        min(x1, x2) - 1e-10 <= x <= max(x1, x2) + 1e-10
        and min(y1, y2) - 1e-10 <= y <= max(y1, y2) + 1e-10
    )


def point_in_ring(point, ring):
    """Check whether a point lies inside a polygon ring."""

    inside = False
    x, y = point

    for i in range(len(ring) - 1):
        x1, y1 = ring[i]
        x2, y2 = ring[i + 1]

        if point_on_segment(point, (x1, y1), (x2, y2)):
            return True

        intersects = (
            (y1 > y) != (y2 > y)
            and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1
        )

        if intersects:
            inside = not inside

    return inside


def point_in_polygon(point, rings):
    """
    Check whether a point lies inside a GeoJSON Polygon.

    The first ring is the outer boundary.
    Remaining rings represent holes.
    """

    if not rings or not point_in_ring(point, rings[0]):
        return False

    for hole in rings[1:]:
        if point_in_ring(point, hole):
            return False

    return True


def point_in_geometry(latitude, longitude, geometry):
    """
    Check a location against Polygon or MultiPolygon geometry.

    GeoJSON coordinates use [longitude, latitude].
    """

    if not geometry:
        return False

    geometry_type = geometry.get("type")
    coordinates = geometry.get("coordinates")

    point = (longitude, latitude)

    if geometry_type == "Polygon":
        return point_in_polygon(point, coordinates)

    if geometry_type == "MultiPolygon":
        return any(
            point_in_polygon(point, polygon)
            for polygon in coordinates
        )

    return False


print("Mapped flood tiles:", len(list(TILES_FOLDER.glob("tile_*.geojson"))))

def assess_location(latitude, longitude):
    """
    Assess whether an SOS location intersects a mapped flood zone.
    Uses relevant satellite tiles instead of loading the full dataset.
    """

    if not is_valid_location(latitude, longitude):
        raise ValueError("Invalid latitude or longitude.")

    metadata = load_impact_metadata()

    if not TILE_INDEX_FILE.exists() or not TILES_FOLDER.exists():
        return {
            "assessment_status": "data_unavailable",
            "message": "Satellite tile data is unavailable.",
            "latitude": latitude,
            "longitude": longitude,
            "matched_zones": [],
            "event": metadata.get("event_name")
        }

    relevant_tiles = find_relevant_tiles(latitude, longitude)
    matched_zones = []

    for tile_path in relevant_tiles:
        features = load_tile_features(str(tile_path))

        for feature in features:
            geometry = feature.get("geometry")
            properties = feature.get("properties") or {}

            if point_in_geometry(latitude, longitude, geometry):
                matched_zones.append({
                    "zone_id": properties.get("zone_id"),
                    "zone_name": properties.get("zone_name"),
                    "impact_level": properties.get("impact_level"),
                    "source": properties.get(
                        "source",
                        properties.get("source_dataset")
                    )
                })

    if matched_zones:
        status = "impact_detected"
        message = "SOS location intersects a mapped impact zone."
    else:
        status = "outside_mapped_zones"
        message = (
            "SOS location does not intersect the currently mapped "
            "impact zones. This does not confirm that the location is safe."
        )

    return {
        "assessment_status": status,
        "message": message,
        "latitude": latitude,
        "longitude": longitude,
        "matched_zones": matched_zones,
        "event": metadata.get("event_name")
    }


if __name__ == "__main__":
    print("CYCLONEWATCH - SATELLITE IMPACT MODULE")
    print("--------------------------------------")

    metadata = load_impact_metadata()
    features = None

    print("Event:", metadata.get("event_name"))
    print("Region:", metadata.get("region"))
    print("Reference date:", metadata.get("event_date"))
    print("Mapped flood tiles:", len(list(TILES_FOLDER.glob("tile_*.geojson"))))

    print("\nSatellite impact module loaded successfully.")

    # Sample SOS coordinates (illustrative only)
    sos_latitude = 20.2961
    sos_longitude = 85.8245

    print("\nChecking sample SOS location...")

    result = assess_location(sos_latitude, sos_longitude)

    print("\nSOS IMPACT ASSESSMENT")
    print("--------------------")

    for key, value in result.items():
        print(f"{key}: {value}")
