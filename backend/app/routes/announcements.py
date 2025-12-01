"""
Announcements API Routes für die Feuerwehr Anwesenheits-App
Feature 15: Team-Features - Schwarzes Brett
"""

import json
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Announcement, AdminUser, AnnouncementPriority
from ..utils.auth import get_current_user

router = APIRouter(prefix="/api/announcements", tags=["Announcements"])


# Pydantic Modelle
class AnnouncementCreate(BaseModel):
    title: str
    content: str
    priority: str = "normal"
    valid_from: Optional[str] = None
    valid_until: Optional[str] = None
    target_groups: Optional[List[str]] = None


class AnnouncementUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    priority: Optional[str] = None
    valid_from: Optional[str] = None
    valid_until: Optional[str] = None
    is_active: Optional[bool] = None
    target_groups: Optional[List[str]] = None


class AnnouncementResponse(BaseModel):
    id: int
    title: str
    content: str
    author_id: int
    author_name: Optional[str] = None
    priority: str
    valid_from: str
    valid_until: Optional[str]
    is_active: bool
    target_groups: List[str]
    created_at: str


# Öffentliche Route (für Kiosk)
@router.get("/", response_model=List[AnnouncementResponse])
def get_active_announcements(
    group: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Gibt alle aktiven und gültigen Ankündigungen zurück (für Kiosk)"""
    now = datetime.utcnow()
    
    query = db.query(Announcement).filter(
        Announcement.is_active == True,
        Announcement.valid_from <= now
    )
    
    # Filter für gültige Ankündigungen (ohne Ablaufdatum oder noch nicht abgelaufen)
    announcements = query.order_by(
        Announcement.priority.desc(),
        Announcement.created_at.desc()
    ).all()
    
    result = []
    for ann in announcements:
        # Prüfe Ablaufdatum
        if ann.valid_until and ann.valid_until < now:
            continue
        
        # Parse target_groups
        target_groups = []
        if ann.target_groups:
            try:
                target_groups = json.loads(ann.target_groups)
            except json.JSONDecodeError:
                target_groups = []
        
        # Filter nach Gruppe falls angegeben
        if group and target_groups and 'all' not in target_groups:
            if group not in target_groups:
                continue
        
        # Hole Author-Name
        author_name = None
        if ann.author:
            author_name = ann.author.username
        
        result.append(AnnouncementResponse(
            id=ann.id,
            title=ann.title,
            content=ann.content,
            author_id=ann.author_id,
            author_name=author_name,
            priority=ann.priority.value,
            valid_from=ann.valid_from.isoformat(),
            valid_until=ann.valid_until.isoformat() if ann.valid_until else None,
            is_active=ann.is_active,
            target_groups=target_groups,
            created_at=ann.created_at.isoformat()
        ))
    
    return result


# Admin-geschützte Routen
@router.get("/all", response_model=List[AnnouncementResponse])
def get_all_announcements(
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user)
):
    """Gibt alle Ankündigungen zurück (Admin)"""
    query = db.query(Announcement)
    
    if not include_inactive:
        query = query.filter(Announcement.is_active == True)
    
    announcements = query.order_by(Announcement.created_at.desc()).all()
    
    result = []
    for ann in announcements:
        target_groups = []
        if ann.target_groups:
            try:
                target_groups = json.loads(ann.target_groups)
            except json.JSONDecodeError:
                target_groups = []
        
        author_name = None
        if ann.author:
            author_name = ann.author.username
        
        result.append(AnnouncementResponse(
            id=ann.id,
            title=ann.title,
            content=ann.content,
            author_id=ann.author_id,
            author_name=author_name,
            priority=ann.priority.value,
            valid_from=ann.valid_from.isoformat(),
            valid_until=ann.valid_until.isoformat() if ann.valid_until else None,
            is_active=ann.is_active,
            target_groups=target_groups,
            created_at=ann.created_at.isoformat()
        ))
    
    return result


@router.post("/", response_model=AnnouncementResponse, status_code=status.HTTP_201_CREATED)
def create_announcement(
    ann_data: AnnouncementCreate,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user)
):
    """Erstellt eine neue Ankündigung"""
    # Validiere Priority
    try:
        priority = AnnouncementPriority(ann_data.priority)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ungültige Priorität: {ann_data.priority}"
        )
    
    # Parse Datum
    valid_from = datetime.utcnow()
    if ann_data.valid_from:
        try:
            valid_from = datetime.fromisoformat(ann_data.valid_from)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ungültiges Datum für valid_from"
            )
    
    valid_until = None
    if ann_data.valid_until:
        try:
            valid_until = datetime.fromisoformat(ann_data.valid_until)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ungültiges Datum für valid_until"
            )
    
    # Target Groups als JSON
    target_groups = json.dumps(ann_data.target_groups or ["all"])
    
    announcement = Announcement(
        title=ann_data.title,
        content=ann_data.content,
        author_id=current_user.id,
        priority=priority,
        valid_from=valid_from,
        valid_until=valid_until,
        target_groups=target_groups
    )
    
    db.add(announcement)
    db.commit()
    db.refresh(announcement)
    
    return AnnouncementResponse(
        id=announcement.id,
        title=announcement.title,
        content=announcement.content,
        author_id=announcement.author_id,
        author_name=current_user.username,
        priority=announcement.priority.value,
        valid_from=announcement.valid_from.isoformat(),
        valid_until=announcement.valid_until.isoformat() if announcement.valid_until else None,
        is_active=announcement.is_active,
        target_groups=ann_data.target_groups or ["all"],
        created_at=announcement.created_at.isoformat()
    )


@router.get("/{announcement_id}", response_model=AnnouncementResponse)
def get_announcement(
    announcement_id: int,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user)
):
    """Gibt eine einzelne Ankündigung zurück"""
    announcement = db.query(Announcement).filter(Announcement.id == announcement_id).first()
    
    if not announcement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ankündigung nicht gefunden"
        )
    
    target_groups = []
    if announcement.target_groups:
        try:
            target_groups = json.loads(announcement.target_groups)
        except json.JSONDecodeError:
            target_groups = []
    
    author_name = None
    if announcement.author:
        author_name = announcement.author.username
    
    return AnnouncementResponse(
        id=announcement.id,
        title=announcement.title,
        content=announcement.content,
        author_id=announcement.author_id,
        author_name=author_name,
        priority=announcement.priority.value,
        valid_from=announcement.valid_from.isoformat(),
        valid_until=announcement.valid_until.isoformat() if announcement.valid_until else None,
        is_active=announcement.is_active,
        target_groups=target_groups,
        created_at=announcement.created_at.isoformat()
    )


@router.put("/{announcement_id}", response_model=AnnouncementResponse)
def update_announcement(
    announcement_id: int,
    ann_data: AnnouncementUpdate,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user)
):
    """Aktualisiert eine Ankündigung"""
    announcement = db.query(Announcement).filter(Announcement.id == announcement_id).first()
    
    if not announcement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ankündigung nicht gefunden"
        )
    
    if ann_data.title is not None:
        announcement.title = ann_data.title
    
    if ann_data.content is not None:
        announcement.content = ann_data.content
    
    if ann_data.priority is not None:
        try:
            announcement.priority = AnnouncementPriority(ann_data.priority)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ungültige Priorität: {ann_data.priority}"
            )
    
    if ann_data.valid_from is not None:
        try:
            announcement.valid_from = datetime.fromisoformat(ann_data.valid_from)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ungültiges Datum für valid_from"
            )
    
    if ann_data.valid_until is not None:
        try:
            announcement.valid_until = datetime.fromisoformat(ann_data.valid_until)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ungültiges Datum für valid_until"
            )
    
    if ann_data.is_active is not None:
        announcement.is_active = ann_data.is_active
    
    if ann_data.target_groups is not None:
        announcement.target_groups = json.dumps(ann_data.target_groups)
    
    db.commit()
    db.refresh(announcement)
    
    target_groups = []
    if announcement.target_groups:
        try:
            target_groups = json.loads(announcement.target_groups)
        except json.JSONDecodeError:
            target_groups = []
    
    author_name = None
    if announcement.author:
        author_name = announcement.author.username
    
    return AnnouncementResponse(
        id=announcement.id,
        title=announcement.title,
        content=announcement.content,
        author_id=announcement.author_id,
        author_name=author_name,
        priority=announcement.priority.value,
        valid_from=announcement.valid_from.isoformat(),
        valid_until=announcement.valid_until.isoformat() if announcement.valid_until else None,
        is_active=announcement.is_active,
        target_groups=target_groups,
        created_at=announcement.created_at.isoformat()
    )


@router.delete("/{announcement_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_announcement(
    announcement_id: int,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user)
):
    """Löscht eine Ankündigung"""
    announcement = db.query(Announcement).filter(Announcement.id == announcement_id).first()
    
    if not announcement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ankündigung nicht gefunden"
        )
    
    db.delete(announcement)
    db.commit()
    return None
