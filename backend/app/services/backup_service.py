"""
Backup Service für die Feuerwehr Anwesenheits-App
Feature 9: Sicherheit - Backup-Funktion
"""

import os
import shutil
import zipfile
from datetime import datetime, timedelta
from typing import List, Optional
from pathlib import Path

from ..database import DATABASE_PATH


class BackupService:
    """Service für Datenbank-Backups"""
    
    BACKUP_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "backups")
    
    @staticmethod
    def ensure_backup_dir():
        """Stellt sicher, dass das Backup-Verzeichnis existiert"""
        os.makedirs(BackupService.BACKUP_DIR, exist_ok=True)
    
    @staticmethod
    def create_backup() -> dict:
        """
        Erstellt ein Backup der SQLite-Datenbank
        Returns: dict mit Backup-Informationen
        """
        BackupService.ensure_backup_dir()
        
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_filename = f"backup_{timestamp}.db.zip"
        backup_path = os.path.join(BackupService.BACKUP_DIR, backup_filename)
        
        # Prüfe ob Datenbank existiert
        if not os.path.exists(DATABASE_PATH):
            raise FileNotFoundError(f"Datenbank nicht gefunden: {DATABASE_PATH}")
        
        # Erstelle ZIP-Archiv mit der Datenbank
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(DATABASE_PATH, os.path.basename(DATABASE_PATH))
        
        # Hole Dateigröße
        file_size = os.path.getsize(backup_path)
        
        return {
            "filename": backup_filename,
            "path": backup_path,
            "size": file_size,
            "created_at": datetime.now().isoformat(),
            "database_file": os.path.basename(DATABASE_PATH)
        }
    
    @staticmethod
    def list_backups() -> List[dict]:
        """Listet alle vorhandenen Backups auf"""
        BackupService.ensure_backup_dir()
        
        backups = []
        
        for filename in os.listdir(BackupService.BACKUP_DIR):
            if filename.startswith("backup_") and filename.endswith(".db.zip"):
                filepath = os.path.join(BackupService.BACKUP_DIR, filename)
                stat = os.stat(filepath)
                
                # Extrahiere Timestamp aus Dateiname
                try:
                    timestamp_str = filename.replace("backup_", "").replace(".db.zip", "")
                    created_at = datetime.strptime(timestamp_str, "%Y-%m-%d_%H-%M-%S")
                except ValueError:
                    created_at = datetime.fromtimestamp(stat.st_mtime)
                
                backups.append({
                    "filename": filename,
                    "size": stat.st_size,
                    "created_at": created_at.isoformat(),
                    "path": filepath
                })
        
        # Sortiere nach Erstellungsdatum (neueste zuerst)
        backups.sort(key=lambda x: x["created_at"], reverse=True)
        
        return backups
    
    @staticmethod
    def get_backup_path(filename: str) -> Optional[str]:
        """Gibt den Pfad zu einem Backup zurück"""
        BackupService.ensure_backup_dir()
        
        # Sicherheitsprüfung: Nur Dateien im Backup-Verzeichnis erlauben
        if ".." in filename or "/" in filename or "\\" in filename:
            return None
        
        filepath = os.path.join(BackupService.BACKUP_DIR, filename)
        
        if os.path.exists(filepath) and os.path.isfile(filepath):
            return filepath
        
        return None
    
    @staticmethod
    def delete_backup(filename: str) -> bool:
        """Löscht ein Backup"""
        filepath = BackupService.get_backup_path(filename)
        
        if filepath:
            os.remove(filepath)
            return True
        
        return False
    
    @staticmethod
    def restore_backup(filename: str) -> dict:
        """
        Stellt ein Backup wieder her
        ACHTUNG: Erstellt automatisch ein Backup vor der Wiederherstellung
        """
        filepath = BackupService.get_backup_path(filename)
        
        if not filepath:
            raise FileNotFoundError(f"Backup nicht gefunden: {filename}")
        
        # Erstelle Sicherungs-Backup vor Restore
        pre_restore_backup = BackupService.create_backup()
        
        # Entpacke und ersetze Datenbank
        with zipfile.ZipFile(filepath, 'r') as zipf:
            # Finde die .db Datei im Archiv
            db_files = [f for f in zipf.namelist() if f.endswith('.db')]
            if not db_files:
                raise ValueError("Kein Datenbank-File im Backup gefunden")
            
            # Extrahiere in temporäres Verzeichnis
            import tempfile
            with tempfile.TemporaryDirectory() as tmpdir:
                zipf.extract(db_files[0], tmpdir)
                extracted_db = os.path.join(tmpdir, db_files[0])
                
                # Ersetze aktuelle Datenbank
                shutil.copy2(extracted_db, DATABASE_PATH)
        
        return {
            "restored_from": filename,
            "pre_restore_backup": pre_restore_backup["filename"],
            "restored_at": datetime.now().isoformat()
        }
    
    @staticmethod
    def cleanup_old_backups(max_age_days: int = 30, keep_minimum: int = 5) -> List[str]:
        """
        Löscht alte Backups
        
        Args:
            max_age_days: Maximales Alter in Tagen
            keep_minimum: Mindestanzahl an Backups die behalten werden
        
        Returns:
            Liste der gelöschten Dateinamen
        """
        backups = BackupService.list_backups()
        threshold = datetime.now() - timedelta(days=max_age_days)
        
        deleted = []
        
        # Behalte mindestens keep_minimum Backups
        for i, backup in enumerate(backups):
            if i < keep_minimum:
                continue
            
            created_at = datetime.fromisoformat(backup["created_at"])
            if created_at < threshold:
                if BackupService.delete_backup(backup["filename"]):
                    deleted.append(backup["filename"])
        
        return deleted


# Backup-Konfiguration
class BackupConfig:
    """Konfiguration für automatische Backups"""
    
    CONFIG_FILE = os.path.join(
        os.path.dirname(__file__), "..", "..", "backup_config.json"
    )
    
    DEFAULT_CONFIG = {
        "schedule": "daily",  # daily, weekly, monthly
        "time": "03:00",
        "retention_days": 30,
        "keep_minimum": 5,
        "enabled": True
    }
    
    @staticmethod
    def get_config() -> dict:
        """Lädt die Backup-Konfiguration"""
        import json
        
        if os.path.exists(BackupConfig.CONFIG_FILE):
            with open(BackupConfig.CONFIG_FILE, 'r') as f:
                return json.load(f)
        
        return BackupConfig.DEFAULT_CONFIG.copy()
    
    @staticmethod
    def save_config(config: dict):
        """Speichert die Backup-Konfiguration"""
        import json
        
        with open(BackupConfig.CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
