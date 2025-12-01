"""
Backup-Manager Service für die Feuerwehr Anwesenheits-App
Verwaltet Backup-Erstellung, -Wiederherstellung und -Verwaltung
"""

import os
import shutil
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple, List, Dict
from sqlalchemy.orm import Session

from ..models import SystemSettings


class BackupManager:
    """Verwaltet Backups der Anwendung"""

    # Standard-Datenbank-Pfad (kann überschrieben werden)
    DATABASE_PATH = os.getenv("DATABASE_PATH", "feuerwehr_anwesenheit.db")
    UPLOADS_PATH = "uploads"

    @staticmethod
    def get_settings(db: Session) -> SystemSettings:
        """Gibt die System-Einstellungen zurück, erstellt sie falls nicht vorhanden"""
        settings = db.query(SystemSettings).first()
        if not settings:
            settings = SystemSettings(
                backup_enabled=True,
                backup_path="./backups/",
                backup_schedule_time="03:00",
                backup_retention_days=30
            )
            db.add(settings)
            db.commit()
            db.refresh(settings)
        return settings

    @staticmethod
    def validate_backup_path(path: str) -> Tuple[bool, str]:
        """
        Validiert ob ein Backup-Pfad existiert und beschreibbar ist.
        
        Args:
            path: Der zu validierende Pfad
            
        Returns:
            Tuple[bool, str]: (Erfolg, Fehlermeldung oder Leerstring)
        """
        try:
            # Expandiere Tilde (~) für Benutzerverzeichnisse
            expanded_path = os.path.expanduser(path)
            
            # Normalisiere den Pfad
            normalized_path = os.path.normpath(expanded_path)
            
            # Prüfe ob der Pfad existiert
            if not os.path.exists(normalized_path):
                # Versuche das Verzeichnis zu erstellen
                try:
                    os.makedirs(normalized_path, exist_ok=True)
                except PermissionError:
                    return False, "Keine Berechtigung zum Erstellen des Verzeichnisses"
                except OSError as e:
                    return False, f"Verzeichnis kann nicht erstellt werden: {str(e)}"
            
            # Prüfe ob es ein Verzeichnis ist
            if not os.path.isdir(normalized_path):
                return False, "Pfad ist kein Verzeichnis"
            
            # Prüfe Schreibberechtigung durch Erstellen einer Test-Datei
            test_file = os.path.join(normalized_path, ".backup_test_write")
            try:
                with open(test_file, 'w') as f:
                    f.write("test")
                os.remove(test_file)
            except PermissionError:
                return False, "Keine Schreibberechtigung für dieses Verzeichnis"
            except OSError as e:
                return False, f"Schreibtest fehlgeschlagen: {str(e)}"
            
            return True, ""
            
        except Exception as e:
            return False, f"Pfad-Validierung fehlgeschlagen: {str(e)}"

    @staticmethod
    def _normalize_path(path: str) -> str:
        """Normalisiert und expandiert einen Pfad"""
        return os.path.normpath(os.path.expanduser(path))

    @staticmethod
    def create_backup(db: Session, custom_path: Optional[str] = None) -> Tuple[bool, str, Optional[str]]:
        """
        Erstellt ein Backup der Datenbank und des uploads-Ordners.
        
        Args:
            db: Datenbank-Session
            custom_path: Optionaler benutzerdefinierter Pfad (überschreibt Settings)
            
        Returns:
            Tuple[bool, str, Optional[str]]: (Erfolg, Nachricht, Dateiname)
        """
        try:
            settings = BackupManager.get_settings(db)
            
            # Bestimme Backup-Pfad
            backup_path = custom_path if custom_path else settings.backup_path
            backup_path = BackupManager._normalize_path(backup_path)
            
            # Validiere Pfad
            valid, error_msg = BackupManager.validate_backup_path(backup_path)
            if not valid:
                return False, error_msg, None
            
            # Erstelle Backup-Dateiname mit Timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            backup_filename = f"feuerwehr_backup_{timestamp}.zip"
            backup_filepath = os.path.join(backup_path, backup_filename)
            
            # Erstelle ZIP-Datei
            with zipfile.ZipFile(backup_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Füge Datenbank hinzu
                db_path = BackupManager.DATABASE_PATH
                if os.path.exists(db_path):
                    zipf.write(db_path, os.path.basename(db_path))
                
                # Füge uploads-Ordner hinzu (falls vorhanden)
                uploads_path = BackupManager.UPLOADS_PATH
                if os.path.exists(uploads_path) and os.path.isdir(uploads_path):
                    for root, dirs, files in os.walk(uploads_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, os.path.dirname(uploads_path))
                            zipf.write(file_path, arcname)
            
            # Aktualisiere Settings mit letztem Backup
            file_size = os.path.getsize(backup_filepath)
            settings.last_backup_time = datetime.utcnow()
            settings.last_backup_size = file_size
            db.commit()
            
            return True, f"Backup erfolgreich erstellt: {backup_filename}", backup_filename
            
        except Exception as e:
            return False, f"Backup-Erstellung fehlgeschlagen: {str(e)}", None

    @staticmethod
    def list_backups(db: Session, custom_path: Optional[str] = None) -> List[Dict]:
        """
        Listet alle Backups im konfigurierten Backup-Pfad auf.
        
        Args:
            db: Datenbank-Session
            custom_path: Optionaler benutzerdefinierter Pfad
            
        Returns:
            Liste von Backup-Informationen
        """
        settings = BackupManager.get_settings(db)
        backup_path = custom_path if custom_path else settings.backup_path
        backup_path = BackupManager._normalize_path(backup_path)
        
        backups = []
        
        if not os.path.exists(backup_path):
            return backups
        
        try:
            for filename in os.listdir(backup_path):
                if filename.startswith("feuerwehr_backup_") and filename.endswith(".zip"):
                    filepath = os.path.join(backup_path, filename)
                    stat = os.stat(filepath)
                    
                    # Extrahiere Timestamp aus Dateiname
                    try:
                        timestamp_str = filename.replace("feuerwehr_backup_", "").replace(".zip", "")
                        created = datetime.strptime(timestamp_str, "%Y-%m-%d_%H-%M-%S")
                    except ValueError:
                        created = datetime.fromtimestamp(stat.st_mtime)
                    
                    backups.append({
                        "filename": filename,
                        "filepath": filepath,
                        "size_bytes": stat.st_size,
                        "size_mb": round(stat.st_size / (1024 * 1024), 2),
                        "created": created.isoformat(),
                        "created_timestamp": stat.st_mtime
                    })
            
            # Sortiere nach Erstellungsdatum (neueste zuerst)
            backups.sort(key=lambda x: x["created_timestamp"], reverse=True)
            
        except Exception as e:
            print(f"Fehler beim Auflisten der Backups: {e}")
        
        return backups

    @staticmethod
    def delete_backup(db: Session, filename: str, custom_path: Optional[str] = None) -> Tuple[bool, str]:
        """
        Löscht ein einzelnes Backup.
        
        Args:
            db: Datenbank-Session
            filename: Name der zu löschenden Backup-Datei
            custom_path: Optionaler benutzerdefinierter Pfad
            
        Returns:
            Tuple[bool, str]: (Erfolg, Nachricht)
        """
        try:
            settings = BackupManager.get_settings(db)
            backup_path = custom_path if custom_path else settings.backup_path
            backup_path = BackupManager._normalize_path(backup_path)
            
            # Sicherheitsprüfung: Nur erlaubte Dateinamen
            if not filename.startswith("feuerwehr_backup_") or not filename.endswith(".zip"):
                return False, "Ungültiger Backup-Dateiname"
            
            # Verhindere Path Traversal
            if ".." in filename or "/" in filename or "\\" in filename:
                return False, "Ungültiger Dateiname"
            
            filepath = os.path.join(backup_path, filename)
            
            if not os.path.exists(filepath):
                return False, "Backup-Datei nicht gefunden"
            
            os.remove(filepath)
            return True, f"Backup {filename} erfolgreich gelöscht"
            
        except Exception as e:
            return False, f"Löschen fehlgeschlagen: {str(e)}"

    @staticmethod
    def delete_old_backups(db: Session, retention_days: Optional[int] = None) -> Tuple[int, List[str]]:
        """
        Löscht Backups, die älter als die konfigurierte Aufbewahrungszeit sind.
        
        Args:
            db: Datenbank-Session
            retention_days: Optionale Anzahl Tage (überschreibt Settings)
            
        Returns:
            Tuple[int, List[str]]: (Anzahl gelöschter Backups, Liste der gelöschten Dateinamen)
        """
        settings = BackupManager.get_settings(db)
        days = retention_days if retention_days is not None else settings.backup_retention_days
        
        cutoff_date = datetime.now() - timedelta(days=days)
        backups = BackupManager.list_backups(db)
        
        deleted = []
        for backup in backups:
            try:
                backup_date = datetime.fromisoformat(backup["created"])
                if backup_date < cutoff_date:
                    success, _ = BackupManager.delete_backup(db, backup["filename"])
                    if success:
                        deleted.append(backup["filename"])
            except Exception as e:
                print(f"Fehler beim Löschen von {backup['filename']}: {e}")
        
        return len(deleted), deleted

    @staticmethod
    def restore_backup(db: Session, backup_filepath: str, create_safety_backup: bool = True) -> Tuple[bool, str]:
        """
        Stellt ein Backup wieder her.
        
        ACHTUNG: Diese Funktion überschreibt alle aktuellen Daten!
        
        Args:
            db: Datenbank-Session
            backup_filepath: Pfad zur Backup-Datei
            create_safety_backup: Ob vor dem Restore ein Sicherungs-Backup erstellt werden soll
            
        Returns:
            Tuple[bool, str]: (Erfolg, Nachricht)
        """
        try:
            if not os.path.exists(backup_filepath):
                return False, "Backup-Datei nicht gefunden"
            
            # Erstelle Sicherungs-Backup vor dem Restore
            if create_safety_backup:
                success, msg, _ = BackupManager.create_backup(db, custom_path="./backups/safety/")
                if not success:
                    return False, f"Sicherungs-Backup fehlgeschlagen: {msg}"
            
            # Extrahiere Backup
            temp_restore_dir = "/tmp/feuerwehr_restore_temp"
            if os.path.exists(temp_restore_dir):
                shutil.rmtree(temp_restore_dir)
            os.makedirs(temp_restore_dir)
            
            with zipfile.ZipFile(backup_filepath, 'r') as zipf:
                zipf.extractall(temp_restore_dir)
            
            # Stelle Datenbank wieder her
            db_filename = os.path.basename(BackupManager.DATABASE_PATH)
            temp_db_path = os.path.join(temp_restore_dir, db_filename)
            
            if os.path.exists(temp_db_path):
                # Schließe alle Datenbankverbindungen (in der Praxis muss die App neugestartet werden)
                shutil.copy2(temp_db_path, BackupManager.DATABASE_PATH)
            
            # Stelle uploads-Ordner wieder her
            temp_uploads_path = os.path.join(temp_restore_dir, "uploads")
            if os.path.exists(temp_uploads_path):
                if os.path.exists(BackupManager.UPLOADS_PATH):
                    shutil.rmtree(BackupManager.UPLOADS_PATH)
                shutil.copytree(temp_uploads_path, BackupManager.UPLOADS_PATH)
            
            # Aufräumen
            shutil.rmtree(temp_restore_dir)
            
            return True, "Backup erfolgreich wiederhergestellt. Bitte starten Sie die Anwendung neu."
            
        except zipfile.BadZipFile:
            return False, "Ungültige oder beschädigte Backup-Datei"
        except Exception as e:
            return False, f"Wiederherstellung fehlgeschlagen: {str(e)}"

    @staticmethod
    def get_backup_filepath(db: Session, filename: str) -> Optional[str]:
        """
        Gibt den vollständigen Pfad zu einer Backup-Datei zurück.
        
        Args:
            db: Datenbank-Session
            filename: Backup-Dateiname
            
        Returns:
            Vollständiger Dateipfad oder None
        """
        settings = BackupManager.get_settings(db)
        backup_path = BackupManager._normalize_path(settings.backup_path)
        
        # Sicherheitsprüfung
        if not filename.startswith("feuerwehr_backup_") or not filename.endswith(".zip"):
            return None
        if ".." in filename or "/" in filename or "\\" in filename:
            return None
        
        filepath = os.path.join(backup_path, filename)
        
        if os.path.exists(filepath):
            return filepath
        return None
