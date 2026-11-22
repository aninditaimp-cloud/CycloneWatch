import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/cyclone", tags=["Cyclone"])

# CycloneWatch/sample_data/cyclone_data.json (Member 1's file)
DATA_FILE = Path(__file__).resolve().parents[2] / "sample_data" / "cyclone_data.json"


def _load() -> dict:
    # Re-read on every request so edits to the JSON show up without a restart
    if not DATA_FILE.exists():
        raise HTTPException(status_code=404, detail="cyclone_data.json not found")
    with open(DATA_FILE, encoding="utf-8") as f:
        return json.load(f)


@router.get("/active")
def active_cyclone():
    """Used by CycloneAlert.jsx and SafetyCheckIn.jsx (they both take this object as `data`)."""
    return _load()


@router.get("/precautions")
def precautions():
    """Used by Preparedness.jsx (`items` prop)."""
    data = _load()
    return {
        "cyclone_name": data.get("cyclone_name"),
        "items": data.get("precautions", []),
    }
