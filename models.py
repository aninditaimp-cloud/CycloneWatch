from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String

from database import Base


# ---------------------------------------------------------------
# Status values (matches the workflow in the project slides)
# ---------------------------------------------------------------
class SOSStatus(str, Enum):
    PENDING = "Pending"            # SOS received, nobody has looked yet
    ACKNOWLEDGED = "Acknowledged"  # coordinator has seen it
    DISPATCHED = "Dispatched"      # rescue team assigned
    RESCUED = "Rescued"            # person is safe
    CANCELLED = "Cancelled"        # user cancelled / false alarm


# ---------------------------------------------------------------
# Database table
# ---------------------------------------------------------------
class SOSRequest(Base):
    __tablename__ = "sos_requests"

    id = Column(Integer, primary_key=True, index=True)
    sos_id = Column(String, unique=True, index=True, nullable=False)  # e.g. SOS1001
    user_id = Column(String, index=True, nullable=False)              # e.g. USER001
    emergency_type = Column(String, nullable=False, default="Cyclone")
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    location_timestamp = Column(DateTime, nullable=False)  # when phone captured the GPS
    status = Column(String, nullable=False, default=SOSStatus.PENDING.value)
    received_at = Column(DateTime, default=datetime.utcnow)  # when server got it (offline sync gap)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ---------------------------------------------------------------
# API schemas (what the mobile app sends / receives)
# Field names match the agreed data format exactly.
# ---------------------------------------------------------------
class SOSCreate(BaseModel):
    user_id: str
    sos_id: str
    emergency_type: str = "Cyclone"
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    location_timestamp: datetime
    status: SOSStatus = SOSStatus.PENDING


class SOSOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    sos_id: str
    emergency_type: str
    latitude: float
    longitude: float
    location_timestamp: datetime
    status: str
    received_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class SOSStatusUpdate(BaseModel):
    status: SOSStatus


class SOSBatch(BaseModel):
    """Used by the app to upload SOS requests saved while offline."""
    requests: List[SOSCreate]


class SOSBatchResult(BaseModel):
    created: List[str]    # sos_ids newly stored
    duplicates: List[str]  # sos_ids already on server (safe to delete from phone)


# ---------------------------------------------------------------
# Safety check-ins (matches the 3 buttons / timeout in SafetyCheckIn.jsx)
# ---------------------------------------------------------------
class CheckInResponse(str, Enum):
    SAFE = "Safe"                  # "I Am Safe" button
    NEED_HELP = "NeedHelp"         # "Send SOS Now" button
    UNRESPONSIVE = "Unresponsive"  # countdown reached 0


class CheckIn(Base):
    __tablename__ = "checkins"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    scenario_id = Column(String, nullable=True)   # e.g. cyclone-yaas-2021
    response = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    escalated = Column(Boolean, default=False)    # True if an SOS was auto-created
    sos_id = Column(String, nullable=True)        # the SOS created, if any
    created_at = Column(DateTime, default=datetime.utcnow)


class CheckInCreate(BaseModel):
    user_id: str
    response: CheckInResponse
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    scenario_id: Optional[str] = None


class CheckInOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    response: str
    scenario_id: Optional[str] = None
    escalated: bool
    sos_id: Optional[str] = None
    created_at: Optional[datetime] = None


# ---------------------------------------------------------------
# Users and family (emergency contacts)
# ---------------------------------------------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True, nullable=False)  # e.g. USER001
    name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    push_token = Column(String, nullable=True)   # Expo push token of this phone
    created_at = Column(DateTime, default=datetime.utcnow)


class EmergencyContact(Base):
    __tablename__ = "emergency_contacts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)   # whose family this is
    name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    relation = Column(String, nullable=True)               # e.g. Mother, Brother
    contact_user_id = Column(String, nullable=True)        # set if the contact also uses the app


class Notification(Base):
    """One row per message the system wants to send to a family contact."""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    sos_id = Column(String, index=True, nullable=False)
    user_id = Column(String, index=True, nullable=False)   # the person in danger
    recipient_name = Column(String, nullable=False)
    recipient_phone = Column(String, nullable=True)
    recipient_user_id = Column(String, nullable=True)
    message = Column(String, nullable=False)
    channel = Column(String, default="queued")             # push / sms are added later
    status = Column(String, default="Queued")
    created_at = Column(DateTime, default=datetime.utcnow)


class UserCreate(BaseModel):
    user_id: str
    name: str
    phone: Optional[str] = None
    push_token: Optional[str] = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    name: str
    phone: Optional[str] = None
    created_at: Optional[datetime] = None


class PushTokenUpdate(BaseModel):
    push_token: str


class ContactCreate(BaseModel):
    name: str
    phone: Optional[str] = None
    relation: Optional[str] = None
    contact_user_id: Optional[str] = None


class ContactOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: str
    name: str
    phone: Optional[str] = None
    relation: Optional[str] = None
    contact_user_id: Optional[str] = None


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sos_id: str
    user_id: str
    recipient_name: str
    recipient_phone: Optional[str] = None
    message: str
    channel: str
    status: str
    created_at: Optional[datetime] = None


# ---------------------------------------------------------------
# Rescue teams and assignments (new tables, so no changes to old ones)
# ---------------------------------------------------------------
class RescueTeam(Base):
    __tablename__ = "rescue_teams"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(String, unique=True, index=True, nullable=False)  # e.g. TEAM-A
    name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Assignment(Base):
    """Which team is going to which SOS, and when they expect to arrive."""
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, index=True)
    sos_id = Column(String, unique=True, index=True, nullable=False)
    team_id = Column(String, nullable=False)
    eta_minutes = Column(Integer, nullable=False)   # estimate given when assigned/updated
    eta_at = Column(DateTime, nullable=False)       # UTC time of expected arrival
    assigned_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TeamCreate(BaseModel):
    team_id: str
    name: str
    phone: Optional[str] = None


class TeamOut(BaseModel):
    team_id: str
    name: str
    phone: Optional[str] = None
    active_assignments: int = 0   # how many open SOS this team is handling


class AssignRequest(BaseModel):
    team_id: str
    eta_minutes: int = Field(ge=1, le=1440)


class AssignmentOut(BaseModel):
    sos_id: str
    team_id: str
    team_name: Optional[str] = None
    eta_minutes: int
    eta_at: str            # ISO time in UTC, ends with Z
    assigned_at: str
