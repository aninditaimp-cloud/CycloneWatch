"""Adds demo SOS requests near Balasore/Bhadrak (Cyclone Yaas area).
Run from the backend folder:  python seed.py
Safe to run more than once: existing sos_ids are skipped.
"""
from datetime import datetime, timedelta

from database import Base, SessionLocal, engine
from models import Assignment, EmergencyContact, RescueTeam, SOSRequest, User

Base.metadata.create_all(bind=engine)

DEMO = [
    ("USER101", "DEMO-SOS-1", 21.3450, 86.9120, "Pending"),
    ("USER102", "DEMO-SOS-2", 21.3120, 86.8650, "Pending"),
    ("USER103", "DEMO-SOS-3", 21.4010, 86.9480, "Acknowledged"),
    ("USER104", "DEMO-SOS-4", 21.2780, 86.9900, "Dispatched"),
    ("USER105", "DEMO-SOS-5", 21.5030, 86.9300, "Rescued"),
    # These 4 sit inside REAL flood-water polygons (Bhuvan, 29 May 2021), so the flood
    # factor shows up in the ranking. FLOOD-DEMO-1 and -4 are ~1.6 km apart (a cluster).
    ("USER106", "FLOOD-DEMO-1", 21.37385, 86.92032, "Pending"),   # 3.3 km from centre (high zone)
    ("USER107", "FLOOD-DEMO-2", 21.35866, 86.82183, "Pending"),   # 9.5 km (moderate zone)
    ("USER108", "FLOOD-DEMO-3", 21.20599, 86.76947, "Pending"),   # 21.4 km (low zone)
    ("USER109", "FLOOD-DEMO-4", 21.37105, 86.93482, "Pending"),   # 3.7 km (high zone)
]

db = SessionLocal()
added = 0
for user_id, sos_id, lat, lon, status in DEMO:
    if db.query(SOSRequest).filter_by(sos_id=sos_id).first():
        continue
    db.add(
        SOSRequest(
            sos_id=sos_id,
            user_id=user_id,
            emergency_type="Cyclone",
            latitude=lat,
            longitude=lon,
            location_timestamp=datetime.utcnow(),
            status=status,
        )
    )
    added += 1
# Demo users, each with one family contact (for the family view page)
# Try: /family?user=USER101&phone=9000000201
PEOPLE = [
    ("USER101", "Ravi Das", "9000000101", "Meena Das", "9000000201", "Mother"),
    ("USER102", "Sita Nayak", "9000000102", "Hari Nayak", "9000000202", "Brother"),
    ("USER103", "Amit Behera", "9000000103", "Rina Behera", "9000000203", "Wife"),
    ("USER104", "Pooja Sahoo", "9000000104", "Kiran Sahoo", "9000000204", "Father"),
    ("USER105", "Manoj Jena", "9000000105", "Lata Jena", "9000000205", "Mother"),
    ("USER106", "Anita Mohanty", "9000000106", "Biswa Mohanty", "9000000206", "Husband"),
    ("USER107", "Rakesh Panda", "9000000107", "Sunita Panda", "9000000207", "Wife"),
    ("USER108", "Deepa Swain", "9000000108", "Gopal Swain", "9000000208", "Father"),
    ("USER109", "Tapan Rout", "9000000109", "Nila Rout", "9000000209", "Mother"),
]
users_added = 0
for uid, name, phone, c_name, c_phone, relation in PEOPLE:
    if db.query(User).filter_by(user_id=uid).first():
        continue
    db.add(User(user_id=uid, name=name, phone=phone))
    db.add(EmergencyContact(user_id=uid, name=c_name, phone=c_phone, relation=relation))
    users_added += 1

# Demo rescue teams, and one team already on its way to DEMO-SOS-4
TEAMS = [
    ("TEAM-A", "NDRF Team Alpha", "9000000301"),
    ("TEAM-B", "NDRF Team Bravo", "9000000302"),
    ("TEAM-C", "State Fire & Rescue", "9000000303"),
]
teams_added = 0
for tid, tname, tphone in TEAMS:
    if db.query(RescueTeam).filter_by(team_id=tid).first():
        continue
    db.add(RescueTeam(team_id=tid, name=tname, phone=tphone))
    teams_added += 1

if not db.query(Assignment).filter_by(sos_id="DEMO-SOS-4").first():
    now = datetime.utcnow()
    db.add(
        Assignment(
            sos_id="DEMO-SOS-4",
            team_id="TEAM-A",
            eta_minutes=25,
            eta_at=now + timedelta(minutes=25),
            assigned_at=now,
        )
    )

db.commit()
db.close()
print(f"Added {teams_added} demo rescue teams.")
print(f"Added {added} demo SOS requests and {users_added} demo users with family contacts.")
