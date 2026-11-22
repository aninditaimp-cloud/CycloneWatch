import uuid
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from notify import queue_family_notifications
from models import (
    CheckIn,
    CheckInCreate,
    CheckInOut,
    CheckInResponse,
    SOSRequest,
    SOSStatus,
)

router = APIRouter(prefix="/checkins", tags=["Check-ins"])


@router.post("", response_model=CheckInOut, status_code=201)
def submit_checkin(data: CheckInCreate, db: Session = Depends(get_db)):
    """One endpoint for all three outcomes of SafetyCheckIn.jsx:
       Safe          -> onConfirmSafe          (no SOS)
       NeedHelp      -> onSendManualSos        (SOS created)
       Unresponsive  -> onTimeoutUnresponsive  (SOS created automatically)
    """
    escalate = data.response in (CheckInResponse.NEED_HELP, CheckInResponse.UNRESPONSIVE)
    sos_id = None

    if escalate:
        sos_id = "SOS-" + uuid.uuid4().hex[:8].upper()
        db.add(
            SOSRequest(
                sos_id=sos_id,
                user_id=data.user_id,
                emergency_type="Cyclone",
                latitude=data.latitude,
                longitude=data.longitude,
                location_timestamp=datetime.utcnow(),
                status=SOSStatus.PENDING.value,
            )
        )
        queue_family_notifications(
            db, sos_id, data.user_id, data.latitude, data.longitude, "Cyclone"
        )

    row = CheckIn(
        user_id=data.user_id,
        scenario_id=data.scenario_id,
        response=data.response.value,
        latitude=data.latitude,
        longitude=data.longitude,
        escalated=escalate,
        sos_id=sos_id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
