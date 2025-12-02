"""
Groups API Routes für die Feuerwehr Anwesenheits-App
Feature 15: Team-Features - Gruppenbildung
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Group, Personnel, AdminUser
from ..utils.auth import get_current_user

router = APIRouter(prefix="/api/groups", tags=["Groups"])


# Pydantic Modelle
class GroupCreate(BaseModel):
    name: str
    description: Optional[str] = None
    color: str = "#666666"


class GroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    is_active: Optional[bool] = None


class GroupResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    color: str
    is_active: bool
    member_count: int


class GroupMemberResponse(BaseModel):
    id: int
    stammrollennummer: str
    vorname: str
    nachname: str
    dienstgrad: str
    aktiv: bool


# Routen
@router.get("/", response_model=List[GroupResponse])
def get_groups(
    include_inactive: bool = False,
    db: Session = Depends(get_db)
):
    """Gibt alle Gruppen zurück"""
    query = db.query(Group)
    
    if not include_inactive:
        query = query.filter(Group.is_active == True)
    
    groups = query.order_by(Group.name).all()
    
    result = []
    for group in groups:
        member_count = db.query(Personnel).filter(
            Personnel.group_id == group.id,
            Personnel.aktiv == True
        ).count()
        
        result.append(GroupResponse(
            id=group.id,
            name=group.name,
            description=group.description,
            color=group.color,
            is_active=group.is_active,
            member_count=member_count
        ))
    
    return result


@router.get("/{group_id}", response_model=GroupResponse)
def get_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user)
):
    """Gibt eine einzelne Gruppe zurück"""
    group = db.query(Group).filter(Group.id == group_id).first()
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gruppe nicht gefunden"
        )
    
    member_count = db.query(Personnel).filter(
        Personnel.group_id == group.id,
        Personnel.aktiv == True
    ).count()
    
    return GroupResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        color=group.color,
        is_active=group.is_active,
        member_count=member_count
    )


@router.post("/", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
def create_group(
    group_data: GroupCreate,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user)
):
    """Erstellt eine neue Gruppe"""
    # Prüfe ob Name bereits existiert
    existing = db.query(Group).filter(Group.name == group_data.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Eine Gruppe mit diesem Namen existiert bereits"
        )
    
    # Validiere Hex-Farbe
    if not group_data.color.startswith("#") or len(group_data.color) != 7:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Farbe muss im Hex-Format sein (z.B. #FF0000)"
        )
    
    group = Group(
        name=group_data.name,
        description=group_data.description,
        color=group_data.color
    )
    
    db.add(group)
    db.commit()
    db.refresh(group)
    
    return GroupResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        color=group.color,
        is_active=group.is_active,
        member_count=0
    )


@router.put("/{group_id}", response_model=GroupResponse)
def update_group(
    group_id: int,
    group_data: GroupUpdate,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user)
):
    """Aktualisiert eine Gruppe"""
    group = db.query(Group).filter(Group.id == group_id).first()
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gruppe nicht gefunden"
        )
    
    if group_data.name is not None:
        # Prüfe ob Name bereits existiert
        existing = db.query(Group).filter(
            Group.name == group_data.name,
            Group.id != group_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Eine Gruppe mit diesem Namen existiert bereits"
            )
        group.name = group_data.name
    
    if group_data.description is not None:
        group.description = group_data.description
    
    if group_data.color is not None:
        if not group_data.color.startswith("#") or len(group_data.color) != 7:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Farbe muss im Hex-Format sein (z.B. #FF0000)"
            )
        group.color = group_data.color
    
    if group_data.is_active is not None:
        group.is_active = group_data.is_active
    
    db.commit()
    db.refresh(group)
    
    member_count = db.query(Personnel).filter(
        Personnel.group_id == group.id,
        Personnel.aktiv == True
    ).count()
    
    return GroupResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        color=group.color,
        is_active=group.is_active,
        member_count=member_count
    )


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user)
):
    """Löscht eine Gruppe"""
    group = db.query(Group).filter(Group.id == group_id).first()
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gruppe nicht gefunden"
        )
    
    # Entferne Gruppenzuordnung bei allen Mitgliedern
    db.query(Personnel).filter(Personnel.group_id == group_id).update(
        {"group_id": None}
    )
    
    db.delete(group)
    db.commit()
    return None


@router.get("/{group_id}/members", response_model=List[GroupMemberResponse])
def get_group_members(
    group_id: int,
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user)
):
    """Gibt alle Mitglieder einer Gruppe zurück"""
    group = db.query(Group).filter(Group.id == group_id).first()
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gruppe nicht gefunden"
        )
    
    query = db.query(Personnel).filter(Personnel.group_id == group_id)
    
    if not include_inactive:
        query = query.filter(Personnel.aktiv == True)
    
    members = query.order_by(Personnel.nachname, Personnel.vorname).all()
    
    return [
        GroupMemberResponse(
            id=m.id,
            stammrollennummer=m.stammrollennummer,
            vorname=m.vorname,
            nachname=m.nachname,
            dienstgrad=m.dienstgrad,
            aktiv=m.aktiv
        )
        for m in members
    ]


@router.post("/{group_id}/members/{personnel_id}")
def add_member_to_group(
    group_id: int,
    personnel_id: int,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user)
):
    """Fügt ein Mitglied zu einer Gruppe hinzu"""
    group = db.query(Group).filter(Group.id == group_id).first()
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gruppe nicht gefunden"
        )
    
    personnel = db.query(Personnel).filter(Personnel.id == personnel_id).first()
    
    if not personnel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person nicht gefunden"
        )
    
    personnel.group_id = group_id
    db.commit()
    
    return {
        "message": f"{personnel.vorname} {personnel.nachname} wurde zur Gruppe {group.name} hinzugefügt"
    }


@router.delete("/{group_id}/members/{personnel_id}")
def remove_member_from_group(
    group_id: int,
    personnel_id: int,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user)
):
    """Entfernt ein Mitglied aus einer Gruppe"""
    personnel = db.query(Personnel).filter(
        Personnel.id == personnel_id,
        Personnel.group_id == group_id
    ).first()
    
    if not personnel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person nicht in dieser Gruppe gefunden"
        )
    
    personnel.group_id = None
    db.commit()
    
    return {
        "message": f"{personnel.vorname} {personnel.nachname} wurde aus der Gruppe entfernt"
    }
