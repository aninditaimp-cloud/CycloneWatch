from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import (
    AssignmentOut,
    AssignRequest,
    Assignment,
    RescueTeam,
    SOSRequest,
    TeamCreate,
    TeamOut,
)
from notify import queue_family_message

router = APIRouter(tags=["Rescue teams"])

OPEN_STATUSES = ["Pending", "Acknowledged", "Dispatched"]


def _z(dt: datetime) -> str:
    return dt.isoformat() + "Z"   # stored as UTC, so mark it as UTC for browsers


def _assignment_out(a: Assignment, team_name) -> AssignmentOut:
    return AssignmentOut(
        sos_id=a.sos_id,
        team_id=a.team_id,
        team_name=team_name,
        eta_minutes=a.eta_minutes,
        eta_at=_z(a.eta_at),
        assigned_at=_z(a.assigned_at),
    )


def _team_names(db: Session) -> dict:
    return {t.team_id: t.name for t in db.query(RescueTeam).all()}


# ---------------- Teams ----------------
@router.post("/teams", response_model=TeamOut, status_code=201)
def create_team(data: TeamCreate, db: Session = Depends(get_db)):
    """Create a rescue team. Same team_id again updates its name/phone."""
    team = db.query(RescueTeam).filter_by(team_id=data.team_id).first()
    if team:
        team.name = data.name
        if data.phone is not None:
            team.phone = data.phone
    else:
        team = RescueTeam(team_id=data.team_id, name=data.name, phone=data.phone)
        db.add(team)
    db.commit()
    db.refresh(team)
    return TeamOut(team_id=team.team_id, name=team.name, phone=team.phone, active_assignments=0)


@router.get("/teams", response_model=List[TeamOut])
def list_teams(db: Session = Depends(get_db)):
    out = []
    for t in db.query(RescueTeam).order_by(RescueTeam.id).all():
        active = (
            db.query(Assignment)
            .join(SOSRequest, SOSRequest.sos_id == Assignment.sos_id)
            .filter(Assignment.team_id == t.team_id, SOSRequest.status.in_(OPEN_STATUSES))
            .count()
        )
        out.append(
            TeamOut(team_id=t.team_id, name=t.name, phone=t.phone, active_assignments=active)
        )
    return out


# ---------------- Assignments ----------------
@router.post("/sos/{sos_id}/assign", response_model=AssignmentOut)
def assign_team(sos_id: str, body: AssignRequest, db: Session = Depends(get_db)):
    """Send a team to an SOS with an ETA (in minutes from now).
    Calling it again for the same SOS changes the team and/or the ETA.
    The SOS becomes 'Dispatched' and the family is told."""
    sos = db.query(SOSRequest).filter_by(sos_id=sos_id).first()
    if not sos:
        raise HTTPException(status_code=404, detail="SOS not found")
    if sos.status in ("Rescued", "Cancelled"):
        raise HTTPException(status_code=409, detail=f"SOS is already {sos.status}")
    team = db.query(RescueTeam).filter_by(team_id=body.team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Rescue team not found")

    now = datetime.utcnow()
    a = db.query(Assignment).filter_by(sos_id=sos_id).first()
    if a:
        a.team_id = team.team_id
        a.eta_minutes = body.eta_minutes
        a.eta_at = now + timedelta(minutes=body.eta_minutes)
    else:
        a = Assignment(
            sos_id=sos_id,
            team_id=team.team_id,
            eta_minutes=body.eta_minutes,
            eta_at=now + timedelta(minutes=body.eta_minutes),
            assigned_at=now,
        )
        db.add(a)

    sos.status = "Dispatched"
    queue_family_message(
        db,
        sos_id,
        sos.user_id,
        "A rescue team ({team}) is on the way to {{person}}. "
        "Estimated arrival: about {eta} minutes.".format(team=team.name, eta=body.eta_minutes),
    )
    db.commit()
    db.refresh(a)
    return _assignment_out(a, team.name)


@router.get("/sos/{sos_id}/assignment", response_model=AssignmentOut)
def get_assignment(sos_id: str, db: Session = Depends(get_db)):
    a = db.query(Assignment).filter_by(sos_id=sos_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="No team assigned yet")
    return _assignment_out(a, _team_names(db).get(a.team_id))


@router.get("/assignments", response_model=List[AssignmentOut])
def list_assignments(db: Session = Depends(get_db)):
    """All assignments (the dashboard uses this to show team + ETA on each SOS)."""
    names = _team_names(db)
    return [_assignment_out(a, names.get(a.team_id)) for a in db.query(Assignment).all()]
