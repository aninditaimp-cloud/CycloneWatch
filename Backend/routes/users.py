from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import (
    ContactCreate,
    ContactOut,
    EmergencyContact,
    PushTokenUpdate,
    User,
    UserCreate,
    UserOut,
)

router = APIRouter(prefix="/users", tags=["Users & Family"])


def _get_user(db: Session, user_id: str) -> User:
    user = db.query(User).filter_by(user_id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("", response_model=UserOut, status_code=201)
def register_user(data: UserCreate, db: Session = Depends(get_db)):
    """Register a user. Calling it again with the same user_id updates the details."""
    user = db.query(User).filter_by(user_id=data.user_id).first()
    if user:
        user.name = data.name
        if data.phone is not None:
            user.phone = data.phone
        if data.push_token is not None:
            user.push_token = data.push_token
    else:
        user = User(
            user_id=data.user_id,
            name=data.name,
            phone=data.phone,
            push_token=data.push_token,
        )
        db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: str, db: Session = Depends(get_db)):
    return _get_user(db, user_id)


@router.put("/{user_id}/push-token", response_model=UserOut)
def save_push_token(user_id: str, body: PushTokenUpdate, db: Session = Depends(get_db)):
    """The phone sends its Expo push token here (used later for push notifications)."""
    user = _get_user(db, user_id)
    user.push_token = body.push_token
    db.commit()
    db.refresh(user)
    return user


@router.post("/{user_id}/contacts", response_model=ContactOut, status_code=201)
def add_contact(user_id: str, data: ContactCreate, db: Session = Depends(get_db)):
    _get_user(db, user_id)
    contact = EmergencyContact(
        user_id=user_id,
        name=data.name,
        phone=data.phone,
        relation=data.relation,
        contact_user_id=data.contact_user_id,
    )
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


@router.get("/{user_id}/contacts", response_model=List[ContactOut])
def list_contacts(user_id: str, db: Session = Depends(get_db)):
    _get_user(db, user_id)
    return db.query(EmergencyContact).filter_by(user_id=user_id).all()


@router.delete("/{user_id}/contacts/{contact_id}")
def delete_contact(user_id: str, contact_id: int, db: Session = Depends(get_db)):
    contact = (
        db.query(EmergencyContact).filter_by(id=contact_id, user_id=user_id).first()
    )
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    db.delete(contact)
    db.commit()
    return {"deleted": contact_id}
