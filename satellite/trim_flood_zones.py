"""Shrinks a huge flood GeoJSON so it is easy to share (GitHub, WhatsApp) and quick to load.

What it does:
  1. rounds every coordinate to 5 decimals (about 1 metre, invisible for this project)
  2. removes repeated points and extra spaces
  3. keeps only flood areas within --radius-km of the cyclone centre (default 80 km)

Run it from the CycloneWatch folder:
    python satellite/trim_flood_zones.py "C:\\path\\to\\big_flood_file.geojson"

The result is written to satellite/flood_zones.geojson (that is the file the backend reads).
Your original file is never changed.
"""
import argparse
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CYCLONE_FILE = os.path.join(HERE, "..", "sample_data", "cyclone_data.json")


def haversine_km(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(a))


def round_ring(ring):
    out = []
    for pt in ring:
        p = [round(pt[0], 5), round(pt[1], 5)]
        if not out or out[-1] != p:
            out.append(p)
    return out


def main():
    ap = argparse.ArgumentParser(description="Shrink a big flood GeoJSON file.")
    ap.add_argument("input", help="path to the big .geojson file")
    ap.add_argument("--out", default=os.path.join(HERE, "flood_zones.geojson"))
    ap.add_argument("--radius-km", type=float, default=80.0, help="keep flood areas within this distance of the cyclone centre (0 = keep everything)")
    args = ap.parse_args()

    try:
        with open(CYCLONE_FILE, encoding="utf-8") as f:
            c = json.load(f)["coordinates"]
        clat, clon = c["lat"], c["lon"]
    except Exception:
        clat, clon = 21.345, 86.912
        print("Could not read cyclone_data.json, using 21.345, 86.912")

    print("Reading", args.input, "...")
    with open(args.input, encoding="utf-8") as f:
        gj = json.load(f)

    kept = []
    for feat in gj.get("features", []):
        g = feat.get("geometry") or {}
        if g.get("type") == "Polygon":
            polys = [g["coordinates"]]
        elif g.get("type") == "MultiPolygon":
            polys = g["coordinates"]
        else:
            continue
        polys = [[round_ring(r) for r in p] for p in polys if p and p[0]]
        polys = [p for p in polys if len(p[0]) >= 4]   # a ring needs at least 4 points
        if not polys:
            continue

        if args.radius_km > 0:
            xs = [pt[0] for p in polys for pt in p[0]]
            ys = [pt[1] for p in polys for pt in p[0]]
            if haversine_km((min(ys) + max(ys)) / 2, (min(xs) + max(xs)) / 2, clat, clon) > args.radius_km:
                continue

        geom = {"type": "Polygon", "coordinates": polys[0]} if g["type"] == "Polygon" else {"type": "MultiPolygon", "coordinates": polys}
        kept.append({"type": "Feature", "properties": feat.get("properties", {}), "geometry": geom})

    out = {"type": "FeatureCollection", "features": kept}
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, separators=(",", ":"))

    print(f"Kept {len(kept)} of {len(gj.get('features', []))} flood areas.")
    print(f"Size: {os.path.getsize(args.input) / 1e6:.1f} MB  ->  {os.path.getsize(args.out) / 1e6:.1f} MB")
    print("Written to", os.path.abspath(args.out))


if __name__ == "__main__":
    sys.exit(main())
