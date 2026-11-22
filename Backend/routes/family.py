import re

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Assignment, CheckIn, EmergencyContact, RescueTeam, SOSRequest, User

router = APIRouter(prefix="/family", tags=["Family"])

ACTIVE = {"Pending", "Acknowledged", "Dispatched"}


def _digits(phone: str) -> str:
    """Compare phone numbers by their last 10 digits (ignores +91, spaces, dashes)."""
    return re.sub(r"\D", "", phone or "")[-10:]


def _iso(dt):
    return dt.isoformat() if dt else None


@router.get("/{user_id}/status")
def family_status(user_id: str, phone: str, db: Session = Depends(get_db)):
    """What a family member sees about their person.

    The caller must give a phone number that is listed as one of the user's
    emergency contacts. (Prototype-level check only: a real app needs login.)
    """
    denied = HTTPException(
        status_code=403,
        detail="No access. Your phone number is not listed as an emergency contact for this person.",
    )
    user = db.query(User).filter_by(user_id=user_id).first()
    wanted = _digits(phone)
    contacts = db.query(EmergencyContact).filter_by(user_id=user_id).all()
    if not user or not wanted or not any(_digits(c.phone) == wanted for c in contacts):
        raise denied  # same answer whether the user exists or not

    sos = (
        db.query(SOSRequest)
        .filter_by(user_id=user_id)
        .order_by(SOSRequest.id.desc())
        .first()
    )
    checkin = (
        db.query(CheckIn)
        .filter_by(user_id=user_id)
        .order_by(CheckIn.id.desc())
        .first()
    )

    name = user.name
    overall, headline, detail = "NO_UPDATE", f"No update from {name} yet", "No check-in or SOS has been received."

    if sos and sos.status in ACTIVE:
        overall = "NEEDS_HELP"
        headline = f"{name} sent an SOS"
        detail = {
            "Pending": "Waiting for a rescue team to respond.",
            "Acknowledged": "Rescue coordinators have seen the SOS.",
            "Dispatched": "A rescue team has been sent.",
        }[sos.status]
    elif sos and sos.status == "Rescued":
        overall = "RESCUED"
        headline = f"{name} has been rescued"
        detail = "Marked safe by rescue coordinators."
    elif checkin and checkin.response == "Safe":
        overall = "SAFE"
        headline = f"{name} checked in as safe"
        detail = "Last safety check-in confirmed."

    # Last known location: the latest SOS if there is one, otherwise the latest check-in
    location = None
    if sos:
        location = {
            "latitude": sos.latitude,
            "longitude": sos.longitude,
            "source": "sos",
            "time": _iso(sos.location_timestamp),
        }
    elif checkin:
        location = {
            "latitude": checkin.latitude,
            "longitude": checkin.longitude,
            "source": "check_in",
            "time": _iso(checkin.created_at),
        }

    # Which rescue team is coming, and when (only while the SOS is still open)
    rescue = None
    if sos and sos.status in ACTIVE:
        a = db.query(Assignment).filter_by(sos_id=sos.sos_id).first()
        if a:
            team = db.query(RescueTeam).filter_by(team_id=a.team_id).first()
            rescue = {
                "team_name": team.name if team else a.team_id,
                "eta_minutes": a.eta_minutes,
                "eta_at": a.eta_at.isoformat() + "Z",   # UTC
            }

    return {
        "user_id": user_id,
        "name": name,
        "overall": overall,
        "headline": headline,
        "detail": detail,
        "sos": (
            {"sos_id": sos.sos_id, "status": sos.status, "received_at": _iso(sos.received_at)}
            if sos
            else None
        ),
        "last_check_in": (
            {"response": checkin.response, "time": _iso(checkin.created_at)}
            if checkin
            else None
        ),
        "rescue": rescue,
        "location": location,
        "map_link": (
            f"https://maps.google.com/?q={location['latitude']},{location['longitude']}"
            if location
            else None
        ),
    }
