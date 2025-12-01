"""
Feuerwehr Anwesenheits-App - Hauptanwendung
=============================================

Eine digitale Anwesenheitserfassungs-Anwendung für Feuerwachen.

Autor: Feuerwehr Anwesenheit Team
Version: 1.0.0
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from apscheduler.schedulers.background import BackgroundScheduler

from app.database import init_db, create_demo_data, SessionLocal
from app.services.session_manager import SessionManager
from app.routes import personnel, sessions, attendance, admin, export


# Background Scheduler für Session-Timeouts
scheduler = BackgroundScheduler()


def check_session_timeouts():
    """Background-Job zum Prüfen abgelaufener Sessions"""
    db = SessionLocal()
    try:
        ended_sessions = SessionManager.check_expired_sessions(db)
        if ended_sessions:
            print(f"[Scheduler] {len(ended_sessions)} Session(s) automatisch beendet")
    except Exception as e:
        print(f"[Scheduler] Fehler beim Prüfen der Sessions: {e}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle-Management für die Anwendung"""
    # Startup
    print("Initialisiere Datenbank...")
    init_db()
    
    # Demo-Daten erstellen (falls gewünscht)
    if os.getenv("CREATE_DEMO_DATA", "true").lower() == "true":
        print("Erstelle Demo-Daten...")
        create_demo_data()
    
    # Background Scheduler starten
    check_interval = int(os.getenv("SESSION_CHECK_INTERVAL", "60"))
    scheduler.add_job(
        check_session_timeouts,
        'interval',
        seconds=check_interval,
        id='session_timeout_checker'
    )
    scheduler.start()
    print(f"Background-Scheduler gestartet (Intervall: {check_interval}s)")
    
    yield
    
    # Shutdown
    print("Beende Background-Scheduler...")
    scheduler.shutdown()
    print("Anwendung beendet")


# FastAPI App erstellen
app = FastAPI(
    title="Feuerwehr Anwesenheits-App",
    description="Digitale Anwesenheitserfassung für Feuerwachen",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In Produktion einschränken
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routes einbinden
app.include_router(personnel.router)
app.include_router(sessions.router)
app.include_router(attendance.router)
app.include_router(admin.router)
app.include_router(export.router)


# Health Check Endpoint
@app.get("/api/health")
def health_check():
    """Health Check Endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "app": "Feuerwehr Anwesenheits-App"
    }


# Statische Dateien (Frontend) - wird in Produktion verwendet
STATIC_PATH = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(STATIC_PATH):
    app.mount("/assets", StaticFiles(directory=os.path.join(STATIC_PATH, "assets")), name="assets")
    
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """Serve Frontend für alle nicht-API Routen"""
        if full_path.startswith("api/"):
            return {"error": "Not Found"}
        
        # Versuche die angeforderte Datei zu finden
        file_path = os.path.join(STATIC_PATH, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        
        # Fallback auf index.html (für SPA-Routing)
        index_path = os.path.join(STATIC_PATH, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        
        return {"error": "Not Found"}


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    print(f"Starte Feuerwehr Anwesenheits-App auf {host}:{port}")
    uvicorn.run(app, host=host, port=port)
