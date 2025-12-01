"""
Backup API Routes für die Feuerwehr Anwesenheits-App
"""

import os
import shutil
import tempfile
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import SystemSettings
from ..services.backup_manager import BackupManager
from ..utils.auth import get_current_user

router = APIRouter(prefix="/api/backup", tags=["Backup"])


# Pydantic Modelle
class BackupSettingsResponse(BaseModel):
    backup_enabled: bool
    backup_path: str
    backup_schedule_time: str
    backup_retention_days: int
    last_backup_time: Optional[str]
    last_backup_size: Optional[int]


class BackupSettingsUpdate(BaseModel):
    backup_enabled: Optional[bool] = None
    backup_path: Optional[str] = None
    backup_schedule_time: Optional[str] = None
    backup_retention_days: Optional[int] = None


class PathValidationRequest(BaseModel):
    path: str


class PathValidationResponse(BaseModel):
    valid: bool
    message: str


class BackupResponse(BaseModel):
    success: bool
    message: str
    filename: Optional[str] = None


class BackupListItem(BaseModel):
    filename: str
    size_bytes: int
    size_mb: float
    created: str


class BackupListResponse(BaseModel):
    backups: list
    total_count: int
    total_size_mb: float


# Routen
@router.get("/settings", response_model=BackupSettingsResponse)
def get_backup_settings(
    db: Session = Depends(get_db),
    _: any = Depends(get_current_user)
):
    """Gibt die aktuellen Backup-Einstellungen zurück"""
    settings = BackupManager.get_settings(db)
    return BackupSettingsResponse(
        backup_enabled=settings.backup_enabled,
        backup_path=settings.backup_path,
        backup_schedule_time=settings.backup_schedule_time,
        backup_retention_days=settings.backup_retention_days,
        last_backup_time=settings.last_backup_time.isoformat() if settings.last_backup_time else None,
        last_backup_size=settings.last_backup_size
    )


@router.put("/settings", response_model=BackupSettingsResponse)
def update_backup_settings(
    settings_data: BackupSettingsUpdate,
    db: Session = Depends(get_db),
    _: any = Depends(get_current_user)
):
    """Aktualisiert die Backup-Einstellungen"""
    settings = BackupManager.get_settings(db)
    
    # Validiere Pfad, falls er geändert wird
    if settings_data.backup_path is not None:
        valid, error_msg = BackupManager.validate_backup_path(settings_data.backup_path)
        if not valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ungültiger Backup-Pfad: {error_msg}"
            )
        settings.backup_path = settings_data.backup_path
    
    # Validiere Aufbewahrungszeit
    if settings_data.backup_retention_days is not None:
        if settings_data.backup_retention_days < 7 or settings_data.backup_retention_days > 90:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Aufbewahrungszeit muss zwischen 7 und 90 Tagen liegen"
            )
        settings.backup_retention_days = settings_data.backup_retention_days
    
    # Validiere Backup-Zeit
    if settings_data.backup_schedule_time is not None:
        try:
            parts = settings_data.backup_schedule_time.split(":")
            hour = int(parts[0])
            minute = int(parts[1]) if len(parts) > 1 else 0
            if hour < 0 or hour > 23 or minute < 0 or minute > 59:
                raise ValueError()
            settings.backup_schedule_time = f"{hour:02d}:{minute:02d}"
        except (ValueError, IndexError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ungültige Backup-Zeit. Format: HH:MM"
            )
    
    if settings_data.backup_enabled is not None:
        settings.backup_enabled = settings_data.backup_enabled
    
    db.commit()
    db.refresh(settings)
    
    return BackupSettingsResponse(
        backup_enabled=settings.backup_enabled,
        backup_path=settings.backup_path,
        backup_schedule_time=settings.backup_schedule_time,
        backup_retention_days=settings.backup_retention_days,
        last_backup_time=settings.last_backup_time.isoformat() if settings.last_backup_time else None,
        last_backup_size=settings.last_backup_size
    )


@router.post("/validate-path", response_model=PathValidationResponse)
def validate_path(
    validation_data: PathValidationRequest,
    _: any = Depends(get_current_user)
):
    """Validiert einen Backup-Pfad ohne ihn zu speichern"""
    valid, error_msg = BackupManager.validate_backup_path(validation_data.path)
    return PathValidationResponse(
        valid=valid,
        message="" if valid else error_msg
    )


@router.post("/create", response_model=BackupResponse)
def create_backup(
    db: Session = Depends(get_db),
    _: any = Depends(get_current_user)
):
    """Erstellt ein manuelles Backup"""
    success, message, filename = BackupManager.create_backup(db)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=message
        )
    
    return BackupResponse(
        success=True,
        message=message,
        filename=filename
    )


@router.get("/list", response_model=BackupListResponse)
def list_backups(
    db: Session = Depends(get_db),
    _: any = Depends(get_current_user)
):
    """Listet alle vorhandenen Backups auf"""
    backups = BackupManager.list_backups(db)
    
    total_size = sum(b["size_bytes"] for b in backups)
    
    return BackupListResponse(
        backups=[
            BackupListItem(
                filename=b["filename"],
                size_bytes=b["size_bytes"],
                size_mb=b["size_mb"],
                created=b["created"]
            ) for b in backups
        ],
        total_count=len(backups),
        total_size_mb=round(total_size / (1024 * 1024), 2)
    )


@router.get("/download/{filename}")
def download_backup(
    filename: str,
    db: Session = Depends(get_db),
    _: any = Depends(get_current_user)
):
    """Lädt ein Backup herunter"""
    filepath = BackupManager.get_backup_filepath(db, filename)
    
    if not filepath:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backup nicht gefunden"
        )
    
    return FileResponse(
        path=filepath,
        filename=filename,
        media_type="application/zip"
    )


@router.post("/restore")
async def restore_backup(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: any = Depends(get_current_user)
):
    """
    Stellt ein Backup aus einer hochgeladenen Datei wieder her.
    ACHTUNG: Alle aktuellen Daten werden überschrieben!
    """
    # Prüfe Dateiname
    if not file.filename or not file.filename.endswith(".zip"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nur ZIP-Dateien sind erlaubt"
        )
    
    # Speichere hochgeladene Datei temporär (cross-platform)
    temp_path = os.path.join(tempfile.gettempdir(), f"restore_{file.filename}")
    try:
        with open(temp_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Führe Wiederherstellung durch
        success, message = BackupManager.restore_backup(db, temp_path, create_safety_backup=True)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=message
            )
        
        return {"success": True, "message": message}
        
    finally:
        # Lösche temporäre Datei
        if os.path.exists(temp_path):
            os.remove(temp_path)


@router.post("/restore/{filename}")
def restore_existing_backup(
    filename: str,
    db: Session = Depends(get_db),
    _: any = Depends(get_current_user)
):
    """
    Stellt ein vorhandenes Backup wieder her.
    ACHTUNG: Alle aktuellen Daten werden überschrieben!
    """
    filepath = BackupManager.get_backup_filepath(db, filename)
    
    if not filepath:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backup nicht gefunden"
        )
    
    success, message = BackupManager.restore_backup(db, filepath, create_safety_backup=True)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=message
        )
    
    return {"success": True, "message": message}


@router.delete("/{filename}", response_model=BackupResponse)
def delete_backup(
    filename: str,
    db: Session = Depends(get_db),
    _: any = Depends(get_current_user)
):
    """Löscht ein einzelnes Backup"""
    success, message = BackupManager.delete_backup(db, filename)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return BackupResponse(
        success=True,
        message=message,
        filename=filename
    )


@router.post("/cleanup")
def cleanup_old_backups(
    db: Session = Depends(get_db),
    _: any = Depends(get_current_user)
):
    """Löscht alte Backups basierend auf der konfigurierten Aufbewahrungszeit"""
    deleted_count, deleted_files = BackupManager.delete_old_backups(db)
    
    return {
        "success": True,
        "deleted_count": deleted_count,
        "deleted_files": deleted_files,
        "message": f"{deleted_count} alte Backup(s) gelöscht"
    }
