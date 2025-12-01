"""
Settings API Routes für die Feuerwehr Anwesenheits-App
Verwaltung der Feuerwehr-Daten und Einstellungen
"""

import os
import shutil
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import FireStation
from ..utils.auth import get_current_user

router = APIRouter(prefix="/api/settings", tags=["Settings"])

# Upload-Verzeichnis für Logo
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads", "logo")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "svg"}
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2 MB


# Pydantic Modelle
class FireStationUpdate(BaseModel):
    name: str
    street: Optional[str] = None
    city: str
    postal_code: str


class FireStationResponse(BaseModel):
    id: int
    name: str
    logo_path: Optional[str]
    has_logo: bool
    street: Optional[str]
    city: str
    postal_code: str
    created_at: str
    updated_at: str


def ensure_upload_dir():
    """Stellt sicher, dass das Upload-Verzeichnis existiert"""
    os.makedirs(UPLOAD_DIR, exist_ok=True)


def get_fire_station(db: Session) -> FireStation:
    """Gibt die Feuerwehr-Daten zurück oder erstellt Standard-Daten"""
    fire_station = db.query(FireStation).first()
    if not fire_station:
        # Standard-Daten erstellen
        fire_station = FireStation(
            name="Freiwillige Feuerwehr",
            city="Musterstadt",
            postal_code="12345"
        )
        db.add(fire_station)
        db.commit()
        db.refresh(fire_station)
    return fire_station


def allowed_file(filename: str) -> bool:
    """Prüft ob die Dateiendung erlaubt ist"""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@router.get("/firestation", response_model=FireStationResponse)
def get_firestation_settings(
    db: Session = Depends(get_db)
):
    """Gibt die Feuerwehr-Daten zurück (öffentlich für PDF-Header)"""
    fire_station = get_fire_station(db)
    
    has_logo = fire_station.logo_path is not None and os.path.exists(
        os.path.join(UPLOAD_DIR, fire_station.logo_path)
    ) if fire_station.logo_path else False
    
    return FireStationResponse(
        id=fire_station.id,
        name=fire_station.name,
        logo_path=fire_station.logo_path,
        has_logo=has_logo,
        street=fire_station.street,
        city=fire_station.city,
        postal_code=fire_station.postal_code,
        created_at=fire_station.created_at.isoformat(),
        updated_at=fire_station.updated_at.isoformat()
    )


@router.put("/firestation", response_model=FireStationResponse)
def update_firestation_settings(
    data: FireStationUpdate,
    db: Session = Depends(get_db),
    _: any = Depends(get_current_user)
):
    """Aktualisiert die Feuerwehr-Daten (Admin-geschützt)"""
    fire_station = get_fire_station(db)
    
    fire_station.name = data.name
    fire_station.street = data.street
    fire_station.city = data.city
    fire_station.postal_code = data.postal_code
    fire_station.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(fire_station)
    
    has_logo = fire_station.logo_path is not None and os.path.exists(
        os.path.join(UPLOAD_DIR, fire_station.logo_path)
    ) if fire_station.logo_path else False
    
    return FireStationResponse(
        id=fire_station.id,
        name=fire_station.name,
        logo_path=fire_station.logo_path,
        has_logo=has_logo,
        street=fire_station.street,
        city=fire_station.city,
        postal_code=fire_station.postal_code,
        created_at=fire_station.created_at.isoformat(),
        updated_at=fire_station.updated_at.isoformat()
    )


@router.post("/firestation/logo")
async def upload_logo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: any = Depends(get_current_user)
):
    """Lädt ein Logo hoch (Admin-geschützt)"""
    ensure_upload_dir()
    
    # Dateiname und Größe prüfen
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Keine Datei ausgewählt"
        )
    
    if not allowed_file(file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Nur folgende Dateitypen erlaubt: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Datei lesen und Größe prüfen
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Datei zu groß. Maximale Größe: {MAX_FILE_SIZE // (1024 * 1024)} MB"
        )
    
    # Dateiendung extrahieren
    ext = file.filename.rsplit(".", 1)[1].lower()
    filename = f"logo.{ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    # Alte Logos löschen (mit Existenzprüfung)
    if os.path.exists(UPLOAD_DIR):
        for old_file in os.listdir(UPLOAD_DIR):
            if old_file.startswith("logo."):
                os.remove(os.path.join(UPLOAD_DIR, old_file))
    
    # Neue Datei speichern
    with open(file_path, "wb") as f:
        f.write(contents)
    
    # Pfad in Datenbank aktualisieren
    fire_station = get_fire_station(db)
    fire_station.logo_path = filename
    fire_station.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Logo erfolgreich hochgeladen", "filename": filename}


@router.get("/firestation/logo")
def get_logo(db: Session = Depends(get_db)):
    """Gibt das Logo zurück (öffentlich für PDF und Anzeige)"""
    fire_station = get_fire_station(db)
    
    if not fire_station.logo_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kein Logo vorhanden"
        )
    
    file_path = os.path.join(UPLOAD_DIR, fire_station.logo_path)
    
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Logo-Datei nicht gefunden"
        )
    
    # MIME-Type bestimmen
    ext = fire_station.logo_path.rsplit(".", 1)[1].lower()
    media_types = {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "svg": "image/svg+xml"
    }
    media_type = media_types.get(ext, "application/octet-stream")
    
    return FileResponse(file_path, media_type=media_type)


@router.delete("/firestation/logo")
def delete_logo(
    db: Session = Depends(get_db),
    _: any = Depends(get_current_user)
):
    """Löscht das Logo (Admin-geschützt)"""
    fire_station = get_fire_station(db)
    
    if fire_station.logo_path:
        file_path = os.path.join(UPLOAD_DIR, fire_station.logo_path)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        fire_station.logo_path = None
        fire_station.updated_at = datetime.utcnow()
        db.commit()
    
    return {"message": "Logo erfolgreich gelöscht"}
