"""
Roles API Routes für die Feuerwehr Anwesenheits-App
Feature 9: Sicherheit - Rollen & Berechtigungen
"""

import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Role, AdminUser, Personnel, RoleName
from ..utils.auth import get_current_user
from ..utils.permissions import get_user_permissions

router = APIRouter(prefix="/api/roles", tags=["Roles"])


# Pydantic Modelle
class RoleResponse(BaseModel):
    id: int
    name: str
    permissions: List[str]
    user_count: int


class RolePermissionsUpdate(BaseModel):
    permissions: List[str]


class UserRoleUpdate(BaseModel):
    role_id: int


# Routen
@router.get("/", response_model=List[RoleResponse])
def get_roles(
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user)
):
    """Gibt alle Rollen zurück"""
    roles = db.query(Role).all()
    
    result = []
    for role in roles:
        # Zähle Benutzer mit dieser Rolle
        admin_count = db.query(AdminUser).filter(AdminUser.role_id == role.id).count()
        personnel_count = db.query(Personnel).filter(Personnel.role_id == role.id).count()
        user_count = admin_count + personnel_count
        
        permissions = []
        try:
            permissions = json.loads(role.permissions)
        except (json.JSONDecodeError, TypeError):
            permissions = []
        
        result.append(RoleResponse(
            id=role.id,
            name=role.name.value,
            permissions=permissions,
            user_count=user_count
        ))
    
    return result


@router.get("/permissions")
def get_all_permissions():
    """Gibt alle verfügbaren Berechtigungen zurück"""
    return {
        "personnel": [
            {"key": "personnel.view", "label": "Personal anzeigen"},
            {"key": "personnel.view_own", "label": "Eigene Daten anzeigen"},
            {"key": "personnel.create", "label": "Personal erstellen"},
            {"key": "personnel.edit", "label": "Personal bearbeiten"},
            {"key": "personnel.delete", "label": "Personal löschen"},
        ],
        "sessions": [
            {"key": "sessions.view", "label": "Sessions anzeigen"},
            {"key": "sessions.create", "label": "Sessions erstellen"},
            {"key": "sessions.end", "label": "Sessions beenden"},
        ],
        "reports": [
            {"key": "reports.view", "label": "Berichte anzeigen"},
            {"key": "reports.export", "label": "Berichte exportieren"},
        ],
        "settings": [
            {"key": "settings.edit", "label": "Einstellungen bearbeiten"},
        ],
        "announcements": [
            {"key": "announcements.view", "label": "Ankündigungen anzeigen"},
            {"key": "announcements.create", "label": "Ankündigungen erstellen"},
            {"key": "announcements.edit", "label": "Ankündigungen bearbeiten"},
            {"key": "announcements.delete", "label": "Ankündigungen löschen"},
        ],
        "groups": [
            {"key": "groups.view", "label": "Gruppen anzeigen"},
            {"key": "groups.create", "label": "Gruppen erstellen"},
            {"key": "groups.edit", "label": "Gruppen bearbeiten"},
            {"key": "groups.delete", "label": "Gruppen löschen"},
        ],
        "trainings": [
            {"key": "trainings.view", "label": "Schulungen anzeigen"},
            {"key": "trainings.create", "label": "Schulungen erstellen"},
            {"key": "trainings.edit", "label": "Schulungen bearbeiten"},
            {"key": "trainings.delete", "label": "Schulungen löschen"},
        ],
        "audit": [
            {"key": "audit.view", "label": "Audit-Log anzeigen"},
        ],
        "backup": [
            {"key": "backup.create", "label": "Backups erstellen"},
            {"key": "backup.restore", "label": "Backups wiederherstellen"},
            {"key": "backup.delete", "label": "Backups löschen"},
        ],
        "roles": [
            {"key": "roles.view", "label": "Rollen anzeigen"},
            {"key": "roles.edit", "label": "Rollen bearbeiten"},
        ]
    }


@router.get("/my-permissions")
def get_my_permissions(
    current_user: AdminUser = Depends(get_current_user)
):
    """Gibt die Berechtigungen des aktuellen Benutzers zurück"""
    permissions = get_user_permissions(current_user)
    
    role_name = None
    if current_user.role:
        role_name = current_user.role.name.value
    
    return {
        "user_id": current_user.id,
        "username": current_user.username,
        "role": role_name,
        "permissions": permissions
    }


@router.get("/{role_id}", response_model=RoleResponse)
def get_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user)
):
    """Gibt eine einzelne Rolle zurück"""
    role = db.query(Role).filter(Role.id == role_id).first()
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rolle nicht gefunden"
        )
    
    admin_count = db.query(AdminUser).filter(AdminUser.role_id == role.id).count()
    personnel_count = db.query(Personnel).filter(Personnel.role_id == role.id).count()
    user_count = admin_count + personnel_count
    
    permissions = []
    try:
        permissions = json.loads(role.permissions)
    except (json.JSONDecodeError, TypeError):
        permissions = []
    
    return RoleResponse(
        id=role.id,
        name=role.name.value,
        permissions=permissions,
        user_count=user_count
    )


@router.get("/{role_id}/permissions")
def get_role_permissions(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user)
):
    """Gibt die Berechtigungen einer Rolle zurück"""
    role = db.query(Role).filter(Role.id == role_id).first()
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rolle nicht gefunden"
        )
    
    permissions = []
    try:
        permissions = json.loads(role.permissions)
    except (json.JSONDecodeError, TypeError):
        permissions = []
    
    return {
        "role_id": role.id,
        "role_name": role.name.value,
        "permissions": permissions
    }


@router.put("/{role_id}/permissions", response_model=RoleResponse)
def update_role_permissions(
    role_id: int,
    perm_data: RolePermissionsUpdate,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user)
):
    """Aktualisiert die Berechtigungen einer Rolle"""
    role = db.query(Role).filter(Role.id == role_id).first()
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rolle nicht gefunden"
        )
    
    role.permissions = json.dumps(perm_data.permissions)
    db.commit()
    db.refresh(role)
    
    admin_count = db.query(AdminUser).filter(AdminUser.role_id == role.id).count()
    personnel_count = db.query(Personnel).filter(Personnel.role_id == role.id).count()
    user_count = admin_count + personnel_count
    
    return RoleResponse(
        id=role.id,
        name=role.name.value,
        permissions=perm_data.permissions,
        user_count=user_count
    )


@router.put("/users/{user_id}/role")
def update_user_role(
    user_id: int,
    role_data: UserRoleUpdate,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user)
):
    """Ändert die Rolle eines Admin-Benutzers"""
    user = db.query(AdminUser).filter(AdminUser.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Benutzer nicht gefunden"
        )
    
    role = db.query(Role).filter(Role.id == role_data.role_id).first()
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rolle nicht gefunden"
        )
    
    user.role_id = role_data.role_id
    db.commit()
    
    return {
        "message": f"Rolle für {user.username} wurde auf {role.name.value} geändert",
        "user_id": user.id,
        "role_id": role.id,
        "role_name": role.name.value
    }


@router.put("/personnel/{personnel_id}/role")
def update_personnel_role(
    personnel_id: int,
    role_data: UserRoleUpdate,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user)
):
    """Ändert die Rolle eines Mitglieds"""
    personnel = db.query(Personnel).filter(Personnel.id == personnel_id).first()
    
    if not personnel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person nicht gefunden"
        )
    
    role = db.query(Role).filter(Role.id == role_data.role_id).first()
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rolle nicht gefunden"
        )
    
    personnel.role_id = role_data.role_id
    db.commit()
    
    return {
        "message": f"Rolle für {personnel.vorname} {personnel.nachname} wurde auf {role.name.value} geändert",
        "personnel_id": personnel.id,
        "role_id": role.id,
        "role_name": role.name.value
    }
