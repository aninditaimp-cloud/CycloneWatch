from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from notify import queue_family_notifications
from models import (
    SOSBatch,
    SOSBatchResult,
    SOSCreate,
    SOSOut,
    SOSRequest,
    SOSStatus,
    SOSStatusUpdate,
)

router = APIRouter(prefix="/sos", tags=["SOS"])


def _to_row(data: SOSCreate) -> SOSRequest:
    return SOSRequest(
        sos_id=data.sos_id,
        user_id=data.user_id,
        emergency_type=data.emergency_type,
        latitude=data.latitude,
        longitude=data.longitude,
        location_timestamp=data.location_timestamp,
        status=data.status.value,
    )


@router.post("", response_model=SOSOut, status_code=201)
def create_sos(data: SOSCreate, db: Session = Depends(get_db)):
    """Member 2's SOS screen calls this when the user presses SOS (or escalation fires)."""
    existing = db.query(SOSRequest).filter_by(sos_id=data.sos_id).first()
    if existing:
        # Idempotent: retrying the same SOS must never create a duplicate
        return existing
    row = _to_row(data)
    db.add(row)
    # Tell the user's family (only for a brand-new SOS, never on a retry)
    queue_family_notifications(
        db, data.sos_id, data.user_id, data.latitude, data.longitude, data.emergency_type
    )
    db.commit()
    db.refresh(row)
    return row


@router.post("/sync", response_model=SOSBatchResult)
def sync_offline_sos(batch: SOSBatch, db: Session = Depends(get_db)):
    """Offline-first: the app stores SOS locally, then uploads them all here
    once connectivity returns. Safe to call repeatedly."""
    created, duplicates = [], []
    for item in batch.requests:
        if db.query(SOSRequest).filter_by(sos_id=item.sos_id).first():
            duplicates.append(item.sos_id)
            continue
        db.add(_to_row(item))
        queue_family_notifications(
            db, item.sos_id, item.user_id, item.latitude, item.longitude, item.emergency_type
        )
        created.append(item.sos_id)
    db.commit()
    return SOSBatchResult(created=created, duplicates=duplicates)


@router.get("", response_model=List[SOSOut])
def list_sos(
    status: Optional[SOSStatus] = None,
    user_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Rescuer dashboard list. Optional filters: ?status=Pending&user_id=USER001"""
    q = db.query(SOSRequest)
    if status:
        q = q.filter(SOSRequest.status == status.value)
    if user_id:
        q = q.filter(SOSRequest.user_id == user_id)
    return q.order_by(SOSRequest.location_timestamp.desc()).all()


@router.get("/{sos_id}", response_model=SOSOut)
def get_sos(sos_id: str, db: Session = Depends(get_db)):
    row = db.query(SOSRequest).filter_by(sos_id=sos_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="SOS not found")
    return row


@router.patch("/{sos_id}/status", response_model=SOSOut)
def update_status(sos_id: str, body: SOSStatusUpdate, db: Session = Depends(get_db)):
    """Rescuer dashboard (or the user cancelling) changes the status."""
    row = db.query(SOSRequest).filter_by(sos_id=sos_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="SOS not found")
    row.status = body.status.value
    db.commit()
    db.refresh(row)
    return row
