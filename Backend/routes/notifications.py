from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import Notification, NotificationOut

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=List[NotificationOut])
def list_notifications(
    sos_id: Optional[str] = None,
    user_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Who was told about which SOS. Filters: ?sos_id=...&user_id=..."""
    q = db.query(Notification)
    if sos_id:
        q = q.filter(Notification.sos_id == sos_id)
    if user_id:
        q = q.filter(Notification.user_id == user_id)
    return q.order_by(Notification.id.desc()).all()
