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
from app.services.backup_service import BackupService, BackupConfig
from app.routes import personnel, sessions, attendance, admin, export
from app.routes import preferences, announcements, groups, trainings, roles, audit, backup


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


def scheduled_backup():
    """Background-Job für automatische Backups"""
    try:
        config = BackupConfig.get_config()
        if not config.get("enabled", False):
            return
        
        result = BackupService.create_backup()
        print(f"[Scheduler] Automatisches Backup erstellt: {result['filename']}")
        
        # Alte Backups aufräumen
        deleted = BackupService.cleanup_old_backups(
            max_age_days=config.get("retention_days", 30),
            keep_minimum=config.get("keep_minimum", 5)
        )
        if deleted:
            print(f"[Scheduler] {len(deleted)} alte Backup(s) gelöscht")
            
    except Exception as e:
        print(f"[Scheduler] Fehler beim automatischen Backup: {e}")


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
    
    # Automatisches Backup (täglich um 03:00)
    backup_config = BackupConfig.get_config()
    if backup_config.get("enabled", True):
        scheduler.add_job(
            scheduled_backup,
            'cron',
            hour=3,
            minute=0,
            id='scheduled_backup'
        )
        print("Automatisches Backup geplant (täglich um 03:00)")
    
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
app.include_router(settings.router)

# Feature 12: Personalisierung
app.include_router(preferences.router)

# Feature 15: Team-Features
app.include_router(announcements.router)
app.include_router(groups.router)
app.include_router(trainings.router)

# Feature 9: Sicherheit
app.include_router(roles.router)
app.include_router(audit.router)
app.include_router(backup.router)


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
