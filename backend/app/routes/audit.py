"""
Audit API Routes für die Feuerwehr Anwesenheits-App
Feature 9: Sicherheit - Audit-Log
"""

import json
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session
import csv
import io

from ..database import get_db
from ..models import AuditLog, AdminUser, AuditAction
from ..utils.auth import get_current_user

router = APIRouter(prefix="/api/audit", tags=["Audit"])


# Pydantic Modelle
class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int]
    user_name: Optional[str]
    action: str
    entity_type: str
    entity_id: Optional[int]
    changes: Optional[dict]
    ip_address: Optional[str]
    user_agent: Optional[str]
    timestamp: str


class AuditLogListResponse(BaseModel):
    logs: List[AuditLogResponse]
    total: int
    page: int
    per_page: int


# Routen
@router.get("/", response_model=AuditLogListResponse)
def get_audit_logs(
    page: int = 1,
    per_page: int = 50,
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    user_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user)
):
    """Gibt alle Audit-Log-Einträge zurück (mit Pagination)"""
    query = db.query(AuditLog)
    
    # Filter
    if action:
        try:
            action_enum = AuditAction(action)
            query = query.filter(AuditLog.action == action_enum)
        except ValueError:
            pass
    
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
            query = query.filter(AuditLog.timestamp >= start_dt)
        except ValueError:
            pass
    
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
            query = query.filter(AuditLog.timestamp <= end_dt)
        except ValueError:
            pass
    
    # Gesamtzahl
    total = query.count()
    
    # Pagination
    offset = (page - 1) * per_page
    logs = query.order_by(AuditLog.timestamp.desc()).offset(offset).limit(per_page).all()
    
    result = []
    for log in logs:
        changes = None
        if log.changes:
            try:
                changes = json.loads(log.changes)
            except json.JSONDecodeError:
                changes = None
        
        result.append(AuditLogResponse(
            id=log.id,
            user_id=log.user_id,
            user_name=log.user_name,
            action=log.action.value,
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            changes=changes,
            ip_address=log.ip_address,
            user_agent=log.user_agent,
            timestamp=log.timestamp.isoformat()
        ))
    
    return AuditLogListResponse(
        logs=result,
        total=total,
        page=page,
        per_page=per_page
    )


@router.get("/actions")
def get_audit_actions():
    """Gibt alle möglichen Aktionen zurück"""
    return [
        {"value": "create", "label": "Erstellen", "icon": "🔨"},
        {"value": "update", "label": "Aktualisieren", "icon": "✏️"},
        {"value": "delete", "label": "Löschen", "icon": "🗑️"},
        {"value": "login", "label": "Anmelden", "icon": "🔐"},
        {"value": "logout", "label": "Abmelden", "icon": "🚪"}
    ]


@router.get("/entity-types")
def get_entity_types():
    """Gibt alle Entity-Typen zurück"""
    return [
        {"value": "personnel", "label": "Personal"},
        {"value": "session", "label": "Session"},
        {"value": "announcement", "label": "Ankündigung"},
        {"value": "group", "label": "Gruppe"},
        {"value": "training", "label": "Schulung"},
        {"value": "backup", "label": "Backup"},
        {"value": "role", "label": "Rolle"},
        {"value": "user", "label": "Benutzer"}
    ]


@router.get("/user/{user_id}", response_model=AuditLogListResponse)
def get_user_audit_logs(
    user_id: int,
    page: int = 1,
    per_page: int = 50,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user)
):
    """Gibt alle Audit-Logs eines Benutzers zurück"""
    query = db.query(AuditLog).filter(AuditLog.user_id == user_id)
    
    total = query.count()
    offset = (page - 1) * per_page
    logs = query.order_by(AuditLog.timestamp.desc()).offset(offset).limit(per_page).all()
    
    result = []
    for log in logs:
        changes = None
        if log.changes:
            try:
                changes = json.loads(log.changes)
            except json.JSONDecodeError:
                changes = None
        
        result.append(AuditLogResponse(
            id=log.id,
            user_id=log.user_id,
            user_name=log.user_name,
            action=log.action.value,
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            changes=changes,
            ip_address=log.ip_address,
            user_agent=log.user_agent,
            timestamp=log.timestamp.isoformat()
        ))
    
    return AuditLogListResponse(
        logs=result,
        total=total,
        page=page,
        per_page=per_page
    )


@router.get("/entity/{entity_type}/{entity_id}", response_model=List[AuditLogResponse])
def get_entity_audit_logs(
    entity_type: str,
    entity_id: int,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user)
):
    """Gibt die History einer Entity zurück"""
    logs = db.query(AuditLog).filter(
        AuditLog.entity_type == entity_type,
        AuditLog.entity_id == entity_id
    ).order_by(AuditLog.timestamp.desc()).all()
    
    result = []
    for log in logs:
        changes = None
        if log.changes:
            try:
                changes = json.loads(log.changes)
            except json.JSONDecodeError:
                changes = None
        
        result.append(AuditLogResponse(
            id=log.id,
            user_id=log.user_id,
            user_name=log.user_name,
            action=log.action.value,
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            changes=changes,
            ip_address=log.ip_address,
            user_agent=log.user_agent,
            timestamp=log.timestamp.isoformat()
        ))
    
    return result


@router.get("/export")
def export_audit_logs(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user)
):
    """Exportiert Audit-Logs als CSV"""
    query = db.query(AuditLog)
    
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
            query = query.filter(AuditLog.timestamp >= start_dt)
        except ValueError:
            pass
    
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
            query = query.filter(AuditLog.timestamp <= end_dt)
        except ValueError:
            pass
    
    logs = query.order_by(AuditLog.timestamp.desc()).all()
    
    # CSV erstellen
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        "ID", "Benutzer-ID", "Benutzername", "Aktion",
        "Entity-Typ", "Entity-ID", "Änderungen",
        "IP-Adresse", "User-Agent", "Zeitstempel"
    ])
    
    for log in logs:
        changes_str = ""
        if log.changes:
            try:
                changes = json.loads(log.changes)
                changes_str = str(changes)
            except json.JSONDecodeError:
                changes_str = log.changes
        
        writer.writerow([
            log.id,
            log.user_id,
            log.user_name,
            log.action.value,
            log.entity_type,
            log.entity_id,
            changes_str,
            log.ip_address,
            log.user_agent,
            log.timestamp.isoformat()
        ])
    
    content = output.getvalue()
    output.close()
    
    filename = f"audit_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return Response(
        content=content.encode('utf-8-sig'),  # UTF-8 with BOM for Excel
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.get("/stats")
def get_audit_stats(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user)
):
    """Gibt Statistiken zum Audit-Log zurück"""
    threshold = datetime.utcnow() - timedelta(days=days)
    
    query = db.query(AuditLog).filter(AuditLog.timestamp >= threshold)
    
    total = query.count()
    
    # Zähle nach Aktion
    action_counts = {}
    for action in AuditAction:
        count = query.filter(AuditLog.action == action).count()
        action_counts[action.value] = count
    
    # Zähle nach Entity-Typ
    entity_types = ["personnel", "session", "announcement", "group", "training", "backup", "role", "user"]
    entity_counts = {}
    for entity_type in entity_types:
        count = query.filter(AuditLog.entity_type == entity_type).count()
        entity_counts[entity_type] = count
    
    return {
        "period_days": days,
        "total_entries": total,
        "by_action": action_counts,
        "by_entity_type": entity_counts
    }
