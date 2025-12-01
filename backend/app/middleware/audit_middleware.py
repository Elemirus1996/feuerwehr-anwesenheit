"""
Audit Middleware für die Feuerwehr Anwesenheits-App
Feature 9: Sicherheit - Audit-Log
"""

import json
from datetime import datetime
from typing import Optional, Any
from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..models import AuditLog, AuditAction


def mask_sensitive_data(data: dict) -> dict:
    """Maskiert sensible Daten wie Passwörter"""
    sensitive_fields = ['password', 'password_hash', 'token', 'secret', 'api_key']
    masked_data = data.copy()
    
    for key in masked_data:
        if any(sensitive in key.lower() for sensitive in sensitive_fields):
            masked_data[key] = '***MASKED***'
    
    return masked_data


def log_audit_event(
    action: AuditAction,
    entity_type: str,
    entity_id: Optional[int] = None,
    user_id: Optional[int] = None,
    user_name: Optional[str] = None,
    changes: Optional[dict] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    db: Optional[Session] = None
):
    """
    Erstellt einen Audit-Log-Eintrag
    
    Args:
        action: Die ausgeführte Aktion (create, update, delete, login, logout)
        entity_type: Der Typ der Entity (personnel, session, announcement, etc.)
        entity_id: Die ID der Entity (optional)
        user_id: Die ID des Benutzers (optional)
        user_name: Der Name des Benutzers (für gelöschte User)
        changes: Ein Dictionary mit den Änderungen (old_value, new_value)
        ip_address: Die IP-Adresse des Benutzers
        user_agent: Der User-Agent String
        db: Optionale Datenbank-Session
    """
    should_close_db = False
    
    if db is None:
        db = SessionLocal()
        should_close_db = True
    
    try:
        # Maskiere sensible Daten
        masked_changes = None
        if changes:
            masked_changes = {}
            if 'old' in changes:
                masked_changes['old'] = mask_sensitive_data(changes['old']) if isinstance(changes['old'], dict) else changes['old']
            if 'new' in changes:
                masked_changes['new'] = mask_sensitive_data(changes['new']) if isinstance(changes['new'], dict) else changes['new']
        
        audit_log = AuditLog(
            user_id=user_id,
            user_name=user_name,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            changes=json.dumps(masked_changes) if masked_changes else None,
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=datetime.utcnow()
        )
        
        db.add(audit_log)
        db.commit()
        
    except Exception as e:
        print(f"Fehler beim Schreiben des Audit-Logs: {e}")
        db.rollback()
    finally:
        if should_close_db:
            db.close()


def get_client_ip(request) -> Optional[str]:
    """Extrahiert die Client-IP aus einem Request"""
    # Prüfe auf Proxy-Header
    forwarded_for = request.headers.get('X-Forwarded-For')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    
    real_ip = request.headers.get('X-Real-IP')
    if real_ip:
        return real_ip
    
    if hasattr(request, 'client') and request.client:
        return request.client.host
    
    return None


def get_user_agent(request) -> Optional[str]:
    """Extrahiert den User-Agent aus einem Request"""
    return request.headers.get('User-Agent')


class AuditLogger:
    """Convenience-Klasse für Audit-Logging"""
    
    def __init__(self, request=None, user=None, db=None):
        self.request = request
        self.user = user
        self.db = db
        
        self.ip_address = None
        self.user_agent = None
        self.user_id = None
        self.user_name = None
        
        if request:
            self.ip_address = get_client_ip(request)
            self.user_agent = get_user_agent(request)
        
        if user:
            self.user_id = user.id
            self.user_name = user.username if hasattr(user, 'username') else None
    
    def log_create(self, entity_type: str, entity_id: int, new_data: dict):
        """Loggt eine Create-Aktion"""
        log_audit_event(
            action=AuditAction.CREATE,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=self.user_id,
            user_name=self.user_name,
            changes={'new': new_data},
            ip_address=self.ip_address,
            user_agent=self.user_agent,
            db=self.db
        )
    
    def log_update(self, entity_type: str, entity_id: int, old_data: dict, new_data: dict):
        """Loggt eine Update-Aktion"""
        # Berechne nur die tatsächlichen Änderungen
        changes_old = {}
        changes_new = {}
        
        for key in set(list(old_data.keys()) + list(new_data.keys())):
            old_val = old_data.get(key)
            new_val = new_data.get(key)
            if old_val != new_val:
                changes_old[key] = old_val
                changes_new[key] = new_val
        
        if changes_old or changes_new:
            log_audit_event(
                action=AuditAction.UPDATE,
                entity_type=entity_type,
                entity_id=entity_id,
                user_id=self.user_id,
                user_name=self.user_name,
                changes={'old': changes_old, 'new': changes_new},
                ip_address=self.ip_address,
                user_agent=self.user_agent,
                db=self.db
            )
    
    def log_delete(self, entity_type: str, entity_id: int, deleted_data: dict = None):
        """Loggt eine Delete-Aktion"""
        log_audit_event(
            action=AuditAction.DELETE,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=self.user_id,
            user_name=self.user_name,
            changes={'old': deleted_data} if deleted_data else None,
            ip_address=self.ip_address,
            user_agent=self.user_agent,
            db=self.db
        )
    
    def log_login(self):
        """Loggt eine Login-Aktion"""
        log_audit_event(
            action=AuditAction.LOGIN,
            entity_type='user',
            entity_id=self.user_id,
            user_id=self.user_id,
            user_name=self.user_name,
            ip_address=self.ip_address,
            user_agent=self.user_agent,
            db=self.db
        )
    
    def log_logout(self):
        """Loggt eine Logout-Aktion"""
        log_audit_event(
            action=AuditAction.LOGOUT,
            entity_type='user',
            entity_id=self.user_id,
            user_id=self.user_id,
            user_name=self.user_name,
            ip_address=self.ip_address,
            user_agent=self.user_agent,
            db=self.db
        )
