from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from database import Base, engine
from routes import checkins, cyclone, family, notifications, priority, rescue, sos, users

# Create tables on startup (SQLite file: cyclonewatch.db)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="CycloneWatch API", version="0.1.0")

# Allow the Expo mobile app and a web dashboard to call the API during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sos.router)
app.include_router(cyclone.router)
app.include_router(checkins.router)
app.include_router(users.router)
app.include_router(notifications.router)
app.include_router(family.router)
app.include_router(rescue.router)
app.include_router(priority.router)


@app.get("/dashboard", include_in_schema=False)
def dashboard():
    """Rescuer dashboard web page (open http://localhost:8000/dashboard)."""
    return FileResponse(Path(__file__).parent / "static" / "dashboard.html")


@app.get("/family", include_in_schema=False)
def family_page():
    """Family view web page (open http://localhost:8000/family)."""
    return FileResponse(Path(__file__).parent / "static" / "family.html")


@app.get("/")
def health():
    return {"app": "CycloneWatch", "status": "running"}
