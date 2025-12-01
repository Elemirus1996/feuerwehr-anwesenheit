"""
Berechtigungs-Utilities für die Feuerwehr Anwesenheits-App
"""

import json
from functools import wraps
from typing import List, Optional
from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import AdminUser, Role


def get_user_permissions(user: AdminUser) -> List[str]:
    """Gibt alle Berechtigungen eines Benutzers zurück"""
    if not user.role:
        return []
    
    try:
        return json.loads(user.role.permissions)
    except (json.JSONDecodeError, TypeError):
        return []


def has_permission(user: AdminUser, permission: str) -> bool:
    """Prüft ob ein Benutzer eine bestimmte Berechtigung hat"""
    permissions = get_user_permissions(user)
    return permission in permissions


def require_permission(permission: str):
    """
    Decorator für Routen die eine bestimmte Berechtigung erfordern
    
    Verwendung:
    @router.get("/protected")
    @require_permission("personnel.view")
    def protected_route(current_user: AdminUser = Depends(get_current_user)):
        ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Hole den current_user aus den kwargs
            current_user = kwargs.get('current_user') or kwargs.get('_')
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Nicht authentifiziert"
                )
            
            if not has_permission(current_user, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Keine Berechtigung für diese Aktion: {permission}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


class PermissionChecker:
    """
    Dependency Klasse für Berechtigungsprüfung
    
    Verwendung:
    @router.get("/protected")
    def protected_route(
        permission: bool = Depends(PermissionChecker("personnel.view")),
        current_user: AdminUser = Depends(get_current_user)
    ):
        ...
    """
    def __init__(self, permission: str):
        self.permission = permission
    
    def __call__(
        self,
        current_user: AdminUser = Depends(None)  # Will be overridden by actual dependency
    ) -> bool:
        if not current_user:
            return False
        return has_permission(current_user, self.permission)
