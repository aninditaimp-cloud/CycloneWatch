from sqlalchemy.orm import Session

from models import EmergencyContact, Notification, User


def queue_family_notifications(
    db: Session,
    sos_id: str,
    user_id: str,
    latitude: float,
    longitude: float,
    emergency_type: str = "Cyclone",
) -> int:
    """Create one Notification row for every emergency contact of `user_id`.

    Call this right after a NEW SOS is added. It does not commit; the caller commits.
    Returns how many contacts were notified (0 if the user has no contacts).
    """
    user = db.query(User).filter_by(user_id=user_id).first()
    person = user.name if user else user_id
    contacts = db.query(EmergencyContact).filter_by(user_id=user_id).all()

    map_link = f"https://maps.google.com/?q={latitude},{longitude}"
    message = (
        f"{person} needs help ({emergency_type} emergency). "
        f"Last known location: {latitude:.4f}, {longitude:.4f}. {map_link}"
    )

    for c in contacts:
        db.add(
            Notification(
                sos_id=sos_id,
                user_id=user_id,
                recipient_name=c.name,
                recipient_phone=c.phone,
                recipient_user_id=c.contact_user_id,
                message=message,
            )
        )
    return len(contacts)


def queue_family_message(db: Session, sos_id: str, user_id: str, message: str) -> int:
    """Send a custom message to every emergency contact of `user_id`.
    Put {person} in the message and it is replaced with the user's name.
    Does not commit; the caller commits."""
    user = db.query(User).filter_by(user_id=user_id).first()
    person = user.name if user else user_id
    text = message.replace("{person}", person)
    contacts = db.query(EmergencyContact).filter_by(user_id=user_id).all()
    for c in contacts:
        db.add(
            Notification(
                sos_id=sos_id,
                user_id=user_id,
                recipient_name=c.name,
                recipient_phone=c.phone,
                recipient_user_id=c.contact_user_id,
                message=text,
            )
        )
    return len(contacts)
