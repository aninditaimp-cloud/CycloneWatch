from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import Assignment, RescueTeam, SOSRequest
from prioritization import rank

router = APIRouter(prefix="/priority", tags=["Prioritization"])

OPEN_STATUSES = ["Pending", "Acknowledged", "Dispatched"]


@router.get("")
def priority_ranking(db: Session = Depends(get_db)):
    """Every open SOS ranked from most to least urgent, with the reasons.
    Closed SOS (Rescued / Cancelled) are not included."""
    rows = db.query(SOSRequest).filter(SOSRequest.status.in_(OPEN_STATUSES)).all()
    open_sos = [
        {
            "sos_id": r.sos_id,
            "user_id": r.user_id,
            "status": r.status,
            "latitude": r.latitude,
            "longitude": r.longitude,
            # received_at is the server's UTC time; fall back to the phone's timestamp
            "since": r.received_at or r.location_timestamp,
        }
        for r in rows
    ]

    team_names = {t.team_id: t.name for t in db.query(RescueTeam).all()}
    teams_by_sos = {
        a.sos_id: team_names.get(a.team_id, a.team_id) for a in db.query(Assignment).all()
    }
    return rank(open_sos, teams_by_sos)
