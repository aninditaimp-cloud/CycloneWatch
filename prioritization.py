"""Rescue prioritization: gives every open SOS a score from 0 to 100.

  hazard zone   0-40  how close the SOS is to the cyclone (buffers in cyclone_data.json)
  flood zone    0-25  is the SOS inside a flood polygon (satellite/flood_zones.geojson)
  concentration 0-20  how many OTHER open SOS are within 2 km
  waiting       0-15  how long the SOS has been waiting

Population exposure (from the slides) is not scored yet: it needs population data.

The flood file can be huge (the real one has ~64,000 polygons), so it is read ONCE,
kept in memory, and searched through a grid index. It reloads by itself if the file changes.
"""
import json
import math
import threading
from array import array
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]  # the CycloneWatch folder
FLOOD_FILE = ROOT / "satellite" / "flood_zones.geojson"
CYCLONE_FILE = ROOT / "sample_data" / "cyclone_data.json"

# ---- Tunable numbers (change these to tune the ranking) ----
HAZARD_POINTS = {"high": 40, "moderate": 25, "low": 10}
FLOOD_POINTS = {"high": 25, "medium": 15, "low": 8}   # default 25 if a zone has no severity
CLUSTER_RADIUS_KM = 2.0
POINTS_PER_NEIGHBOUR = 5
MAX_CLUSTER_POINTS = 20
MAX_WAIT_POINTS = 15
MINUTES_PER_WAIT_POINT = 4     # 60 minutes of waiting = the full 15 points
LEVELS = [(60, "Critical"), (40, "High"), (20, "Medium"), (0, "Low")]

GRID_CELL_DEG = 0.02           # about 2 km; size of the search-index cells


# ---------------- geometry helpers ----------------
def haversine_km(lat1, lon1, lat2, lon2) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = p2 - p1
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _flat(ring) -> array:
    """[[lon, lat], ...] -> compact array [lon, lat, lon, lat, ...] (saves a lot of memory)."""
    a = array("d")
    for pt in ring:
        a.append(pt[0])
        a.append(pt[1])
    return a


def _ring_contains(flat: array, lon, lat) -> bool:
    """Ray casting on a flat ring."""
    n = len(flat) // 2
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = flat[2 * i], flat[2 * i + 1]
        xj, yj = flat[2 * j], flat[2 * j + 1]
        if (yi > lat) != (yj > lat) and lon < (xj - xi) * (lat - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def _polygon_contains(rings, lon, lat) -> bool:
    """rings = [outer_ring, hole1, hole2, ...] (each a flat array)."""
    if not rings or not _ring_contains(rings[0], lon, lat):
        return False
    return not any(_ring_contains(hole, lon, lat) for hole in rings[1:])


# ---------------- flood layer loading (cached) ----------------
_cache = {"key": None, "layer": None, "note": ""}
_lock = threading.Lock()


def _build_layer(path: Path):
    with open(path, encoding="utf-8") as f:
        gj = json.load(f)

    if gj.get("type") == "FeatureCollection":
        features = gj.get("features", [])
    elif gj.get("type") == "Feature":
        features = [gj]
    else:
        features = [{"type": "Feature", "geometry": gj, "properties": {}}]

    zones = []            # one per feature: {"severity", "name", "polys": [{"bbox", "rings"}]}
    index = {}            # (cell_x, cell_y) -> [(zone_i, poly_i), ...]
    n_polys = 0
    for feat in features:
        geom = (feat or {}).get("geometry") or {}
        props = (feat or {}).get("properties") or {}
        if geom.get("type") == "Polygon":
            raw_polys = [geom.get("coordinates", [])]
        elif geom.get("type") == "MultiPolygon":
            raw_polys = geom.get("coordinates", [])
        else:
            continue

        sev = props.get("severity")
        zone = {
            "severity": str(sev).lower() if sev else None,
            "name": props.get("name"),
            "polys": [],
        }
        zi = len(zones)
        for rp in raw_polys:
            if not rp or not rp[0]:
                continue
            rings = [_flat(r) for r in rp]
            outer = rings[0]
            xs, ys = outer[0::2], outer[1::2]
            bbox = (min(xs), min(ys), max(xs), max(ys))
            pi = len(zone["polys"])
            zone["polys"].append({"bbox": bbox, "rings": rings})
            n_polys += 1
            # register this polygon in every grid cell its bounding box touches
            cx0, cx1 = math.floor(bbox[0] / GRID_CELL_DEG), math.floor(bbox[2] / GRID_CELL_DEG)
            cy0, cy1 = math.floor(bbox[1] / GRID_CELL_DEG), math.floor(bbox[3] / GRID_CELL_DEG)
            for cx in range(cx0, cx1 + 1):
                for cy in range(cy0, cy1 + 1):
                    index.setdefault((cx, cy), []).append((zi, pi))
        if zone["polys"]:
            zones.append(zone)

    if not zones:
        return None, "flood_zones.geojson has no polygons yet (flood factor scores 0)."
    layer = {"zones": zones, "index": index, "polygons": n_polys}
    return layer, f"{len(zones)} flood zone(s) loaded ({n_polys} polygons)."


def load_flood_zones() -> Tuple[Optional[dict], str]:
    """Returns (layer, note). layer is None when there is nothing usable.
    Cached: the file is only re-read when it changes (size or modified time)."""
    try:
        st = FLOOD_FILE.stat()
        key = (str(FLOOD_FILE), st.st_mtime_ns, st.st_size)
    except FileNotFoundError:
        return None, "satellite/flood_zones.geojson not found yet (flood factor scores 0)."

    with _lock:
        if _cache["key"] == key:
            return _cache["layer"], _cache["note"]
        try:
            layer, note = _build_layer(FLOOD_FILE)
        except Exception as e:  # bad JSON must never crash the dashboard
            layer, note = None, f"flood_zones.geojson could not be read ({e}). Flood factor scores 0."
        _cache.update(key=key, layer=layer, note=note)   # failures are cached too (no re-parsing every 5 s)
        return layer, note


def load_cyclone() -> Optional[dict]:
    try:
        with open(CYCLONE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _flood_hit(layer, lat, lon):
    """Best (highest-points) flood zone containing the point, or None.
    Only polygons registered in the point's grid cell are tested."""
    if not layer:
        return None
    best = None
    cell = (math.floor(lon / GRID_CELL_DEG), math.floor(lat / GRID_CELL_DEG))
    for zi, pi in layer["index"].get(cell, ()):
        zone = layer["zones"][zi]
        poly = zone["polys"][pi]
        x0, y0, x1, y1 = poly["bbox"]
        if not (x0 <= lon <= x1 and y0 <= lat <= y1):
            continue
        if _polygon_contains(poly["rings"], lon, lat):
            pts = FLOOD_POINTS.get(zone["severity"], 25)
            if best is None or pts > best[0]:
                best = (pts, zone)
    return best


def _level(score: float) -> str:
    for threshold, name in LEVELS:
        if score >= threshold:
            return name
    return "Low"


# ---------------- main scoring ----------------
def rank(open_sos: List[dict], teams_by_sos: Dict[str, str], now: Optional[datetime] = None) -> dict:
    """open_sos items need: sos_id, user_id, status, latitude, longitude, since (datetime, UTC).
    teams_by_sos maps sos_id -> team name for SOS that already have a team."""
    now = now or datetime.utcnow()
    layer, flood_note = load_flood_zones()
    cyclone = load_cyclone()

    buffers = (cyclone or {}).get("buffer_zones", {})
    high_km = buffers.get("high_impact_km", 5)
    mod_km = buffers.get("moderate_impact_km", 15)
    low_km = buffers.get("low_impact_km", 25)
    center = (cyclone or {}).get("coordinates")

    results = []
    for s in open_sos:
        lat, lon = s["latitude"], s["longitude"]
        reasons = []

        # 1) hazard zone
        if center:
            d = haversine_km(lat, lon, center["lat"], center["lon"])
            if d <= high_km:
                hz, label = HAZARD_POINTS["high"], f"{d:.1f} km from cyclone centre (high-impact zone, within {high_km} km)"
            elif d <= mod_km:
                hz, label = HAZARD_POINTS["moderate"], f"{d:.1f} km from cyclone centre (moderate-impact zone, within {mod_km} km)"
            elif d <= low_km:
                hz, label = HAZARD_POINTS["low"], f"{d:.1f} km from cyclone centre (low-impact zone, within {low_km} km)"
            else:
                hz, label = 0, f"{d:.1f} km from cyclone centre (outside impact zones)"
            if hz:
                reasons.append(label)
        else:
            hz, label = 0, "cyclone data not available"

        # 2) flood zone
        hit = _flood_hit(layer, lat, lon) if layer else None
        if hit:
            fl = hit[0]
            fl_label = "inside flood zone" + (f" ({hit[1]['name']})" if hit[1].get("name") else "")
            reasons.append(fl_label)
        else:
            fl = 0
            fl_label = "not inside a flood zone" if layer else "flood layer not loaded"

        # 3) concentration of other open SOS
        neighbours = sum(
            1
            for o in open_sos
            if o["sos_id"] != s["sos_id"]
            and haversine_km(lat, lon, o["latitude"], o["longitude"]) <= CLUSTER_RADIUS_KM
        )
        cl = min(MAX_CLUSTER_POINTS, neighbours * POINTS_PER_NEIGHBOUR)
        if neighbours:
            reasons.append(f"{neighbours} other open SOS within {CLUSTER_RADIUS_KM:g} km")

        # 4) waiting time
        minutes = max(0.0, (now - s["since"]).total_seconds() / 60)
        wt = round(min(MAX_WAIT_POINTS, minutes / MINUTES_PER_WAIT_POINT), 1)
        if minutes >= 1:
            reasons.append(f"waiting {int(minutes)} min")

        score = round(hz + fl + cl + wt, 1)
        results.append(
            {
                "sos_id": s["sos_id"],
                "user_id": s["user_id"],
                "status": s["status"],
                "latitude": lat,
                "longitude": lon,
                "score": score,
                "level": _level(score),
                "assigned": s["sos_id"] in teams_by_sos,
                "team_name": teams_by_sos.get(s["sos_id"]),
                "reasons": reasons or ["no risk factors found yet"],
                "breakdown": {
                    "hazard_zone": {"points": hz, "max": HAZARD_POINTS["high"], "detail": label},
                    "flood_zone": {"points": fl, "max": max(FLOOD_POINTS.values()), "detail": fl_label},
                    "concentration": {"points": cl, "max": MAX_CLUSTER_POINTS, "detail": f"{neighbours} neighbour(s) within {CLUSTER_RADIUS_KM:g} km"},
                    "waiting": {"points": wt, "max": MAX_WAIT_POINTS, "detail": f"{int(minutes)} min"},
                },
            }
        )

    results.sort(key=lambda r: (-r["score"], r["sos_id"]))
    for i, r in enumerate(results, start=1):
        r["rank"] = i

    return {
        "generated_at": now.isoformat() + "Z",
        "flood_layer": {
            "loaded": bool(layer),
            "zones": len(layer["zones"]) if layer else 0,
            "polygons": layer["polygons"] if layer else 0,
            "note": flood_note,
        },
        "cyclone": {
            "name": (cyclone or {}).get("cyclone_name"),
            "center": center,
            "buffers_km": {"high": high_km, "moderate": mod_km, "low": low_km},
        },
        "not_scored": ["population exposure (no population data yet)"],
        "ranking": results,
    }
