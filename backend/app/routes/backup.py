"""
Backup API Routes für die Feuerwehr Anwesenheits-App
Feature 9: Sicherheit - Backup-Funktion
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import AdminUser
from ..utils.auth import get_current_user
from ..services.backup_service import BackupService, BackupConfig

router = APIRouter(prefix="/api/backup", tags=["Backup"])


# Pydantic Modelle
class BackupResponse(BaseModel):
    filename: str
    size: int
    created_at: str


class BackupConfigResponse(BaseModel):
    schedule: str
    time: str
    retention_days: int
    keep_minimum: int
    enabled: bool


class BackupConfigUpdate(BaseModel):
    schedule: Optional[str] = None
    time: Optional[str] = None
    retention_days: Optional[int] = None
    keep_minimum: Optional[int] = None
    enabled: Optional[bool] = None


class RestoreResponse(BaseModel):
    restored_from: str
    pre_restore_backup: str
    restored_at: str


# Routen
@router.post("/create", response_model=BackupResponse)
def create_backup(
    current_user: AdminUser = Depends(get_current_user)
):
    """Erstellt ein manuelles Backup"""
    try:
        result = BackupService.create_backup()
        return BackupResponse(
            filename=result["filename"],
            size=result["size"],
            created_at=result["created_at"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Erstellen des Backups: {str(e)}"
        )


@router.get("/list", response_model=List[BackupResponse])
def list_backups(
    current_user: AdminUser = Depends(get_current_user)
):
    """Listet alle verfügbaren Backups auf"""
    try:
        backups = BackupService.list_backups()
        return [
            BackupResponse(
                filename=b["filename"],
                size=b["size"],
                created_at=b["created_at"]
            )
            for b in backups
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Auflisten der Backups: {str(e)}"
        )


@router.get("/download/{filename}")
def download_backup(
    filename: str,
    current_user: AdminUser = Depends(get_current_user)
):
    """Lädt ein Backup herunter"""
    filepath = BackupService.get_backup_path(filename)
    
    if not filepath:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backup nicht gefunden"
        )
    
    return FileResponse(
        filepath,
        media_type="application/zip",
        filename=filename
    )


@router.post("/restore/{filename}", response_model=RestoreResponse)
def restore_backup(
    filename: str,
    current_user: AdminUser = Depends(get_current_user)
):
    """
    Stellt ein Backup wieder her
    ACHTUNG: Alle aktuellen Daten gehen verloren!
    Es wird automatisch ein Backup vor der Wiederherstellung erstellt.
    """
    try:
        result = BackupService.restore_backup(filename)
        return RestoreResponse(
            restored_from=result["restored_from"],
            pre_restore_backup=result["pre_restore_backup"],
            restored_at=result["restored_at"]
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backup nicht gefunden"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler bei der Wiederherstellung: {str(e)}"
        )


@router.delete("/{filename}", status_code=status.HTTP_204_NO_CONTENT)
def delete_backup(
    filename: str,
    current_user: AdminUser = Depends(get_current_user)
):
    """Löscht ein Backup"""
    if not BackupService.delete_backup(filename):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backup nicht gefunden"
        )
    return None


@router.get("/settings", response_model=BackupConfigResponse)
def get_backup_settings(
    current_user: AdminUser = Depends(get_current_user)
):
    """Gibt die Backup-Konfiguration zurück"""
    config = BackupConfig.get_config()
    return BackupConfigResponse(**config)


@router.put("/settings", response_model=BackupConfigResponse)
def update_backup_settings(
    config_data: BackupConfigUpdate,
    current_user: AdminUser = Depends(get_current_user)
):
    """Aktualisiert die Backup-Konfiguration"""
    config = BackupConfig.get_config()
    
    if config_data.schedule is not None:
        if config_data.schedule not in ["daily", "weekly", "monthly"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ungültiger Schedule-Wert"
            )
        config["schedule"] = config_data.schedule
    
    if config_data.time is not None:
        # Validiere Zeit-Format (HH:MM)
        try:
            datetime.strptime(config_data.time, "%H:%M")
            config["time"] = config_data.time
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ungültiges Zeit-Format (erwartet HH:MM)"
            )
    
    if config_data.retention_days is not None:
        if config_data.retention_days < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="retention_days muss mindestens 1 sein"
            )
        config["retention_days"] = config_data.retention_days
    
    if config_data.keep_minimum is not None:
        if config_data.keep_minimum < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="keep_minimum muss mindestens 1 sein"
            )
        config["keep_minimum"] = config_data.keep_minimum
    
    if config_data.enabled is not None:
        config["enabled"] = config_data.enabled
    
    BackupConfig.save_config(config)
    
    return BackupConfigResponse(**config)


@router.post("/cleanup")
def cleanup_old_backups(
    current_user: AdminUser = Depends(get_current_user)
):
    """Löscht alte Backups basierend auf der Konfiguration"""
    config = BackupConfig.get_config()
    
    deleted = BackupService.cleanup_old_backups(
        max_age_days=config["retention_days"],
        keep_minimum=config["keep_minimum"]
    )
    
    return {
        "deleted_count": len(deleted),
        "deleted_files": deleted
    }


@router.get("/status")
def get_backup_status(
    current_user: AdminUser = Depends(get_current_user)
):
    """Gibt den Backup-Status zurück"""
    backups = BackupService.list_backups()
    config = BackupConfig.get_config()
    
    last_backup = None
    last_backup_age_hours = None
    
    if backups:
        last_backup = backups[0]
        last_backup_time = datetime.fromisoformat(last_backup["created_at"])
        age = datetime.now() - last_backup_time
        last_backup_age_hours = int(age.total_seconds() / 3600)
    
    return {
        "total_backups": len(backups),
        "last_backup": last_backup,
        "last_backup_age_hours": last_backup_age_hours,
        "config": config,
        "warning": last_backup_age_hours is None or last_backup_age_hours > 48
    }
