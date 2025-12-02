"""
Personnel API Routes für die Feuerwehr Anwesenheits-App
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db, get_dienstgrade_list
from ..models import Personnel
from ..utils.auth import get_current_user

router = APIRouter(prefix="/api/personnel", tags=["Personnel"])


# Pydantic Modelle
class PersonnelBase(BaseModel):
    stammrollennummer: str
    vorname: str
    nachname: str
    dienstgrad: str = "FM"
    aktiv: bool = True
    group_id: Optional[int] = None


class PersonnelCreate(PersonnelBase):
    pass


class PersonnelUpdate(BaseModel):
    vorname: Optional[str] = None
    nachname: Optional[str] = None
    dienstgrad: Optional[str] = None
    aktiv: Optional[bool] = None
    group_id: Optional[int] = None


class PersonnelResponse(BaseModel):
    id: int
    stammrollennummer: str
    vorname: str
    nachname: str
    dienstgrad: str
    aktiv: bool
    group_id: Optional[int] = None
    group_name: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True


class DienstgradResponse(BaseModel):
    kuerzel: str
    name: str
    level: int


# Öffentliche Routen (für Check-in)
@router.get("/verify/{stammrollennummer}")
def verify_personnel(stammrollennummer: str, db: Session = Depends(get_db)):
    """Verifiziert eine Stammrollennummer und gibt Basisinfos zurück"""
    person = db.query(Personnel).filter(
        Personnel.stammrollennummer == stammrollennummer
    ).first()
    
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person mit dieser Stammrollennummer nicht gefunden"
        )
    
    if not person.aktiv:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Person ist nicht aktiv"
        )
    
    return {
        "stammrollennummer": person.stammrollennummer,
        "vorname": person.vorname,
        "nachname": person.nachname,
        "dienstgrad": person.dienstgrad,
        "kann_einsatz_beenden": person.kann_einsatz_beenden()
    }


@router.get("/dienstgrade", response_model=List[DienstgradResponse])
def get_dienstgrade():
    """Gibt alle verfügbaren Dienstgrade zurück"""
    return get_dienstgrade_list()


# Admin-geschützte Routen
@router.get("/", response_model=List[PersonnelResponse])
def list_personnel(
    aktiv_only: bool = False,
    group_id: Optional[int] = None,
    db: Session = Depends(get_db),
    _: any = Depends(get_current_user)
):
    """Gibt alle Mitarbeiter zurück (Admin-geschützt)"""
    query = db.query(Personnel)
    if aktiv_only:
        query = query.filter(Personnel.aktiv == True)
    if group_id:
        query = query.filter(Personnel.group_id == group_id)
    personnel = query.order_by(Personnel.nachname, Personnel.vorname).all()
    
    return [
        PersonnelResponse(
            id=p.id,
            stammrollennummer=p.stammrollennummer,
            vorname=p.vorname,
            nachname=p.nachname,
            dienstgrad=p.dienstgrad,
            aktiv=p.aktiv,
            group_id=p.group_id,
            group_name=p.group.name if p.group else None,
            created_at=p.created_at.isoformat()
        )
        for p in personnel
    ]


@router.get("/{person_id}", response_model=PersonnelResponse)
def get_personnel(
    person_id: int,
    db: Session = Depends(get_db),
    _: any = Depends(get_current_user)
):
    """Gibt einen einzelnen Mitarbeiter zurück (Admin-geschützt)"""
    person = db.query(Personnel).filter(Personnel.id == person_id).first()
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person nicht gefunden"
        )
    
    return PersonnelResponse(
        id=person.id,
        stammrollennummer=person.stammrollennummer,
        vorname=person.vorname,
        nachname=person.nachname,
        dienstgrad=person.dienstgrad,
        aktiv=person.aktiv,
        group_id=person.group_id,
        group_name=person.group.name if person.group else None,
        created_at=person.created_at.isoformat()
    )


@router.post("/", response_model=PersonnelResponse, status_code=status.HTTP_201_CREATED)
def create_personnel(
    person_data: PersonnelCreate,
    db: Session = Depends(get_db),
    _: any = Depends(get_current_user)
):
    """Erstellt einen neuen Mitarbeiter (Admin-geschützt)"""
    # Prüfe ob Stammrollennummer bereits existiert
    existing = db.query(Personnel).filter(
        Personnel.stammrollennummer == person_data.stammrollennummer
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stammrollennummer bereits vergeben"
        )
    
    person = Personnel(**person_data.model_dump())
    db.add(person)
    db.commit()
    db.refresh(person)
    
    return PersonnelResponse(
        id=person.id,
        stammrollennummer=person.stammrollennummer,
        vorname=person.vorname,
        nachname=person.nachname,
        dienstgrad=person.dienstgrad,
        aktiv=person.aktiv,
        group_id=person.group_id,
        group_name=person.group.name if person.group else None,
        created_at=person.created_at.isoformat()
    )


@router.put("/{person_id}", response_model=PersonnelResponse)
def update_personnel(
    person_id: int,
    person_data: PersonnelUpdate,
    db: Session = Depends(get_db),
    _: any = Depends(get_current_user)
):
    """Aktualisiert einen Mitarbeiter (Admin-geschützt)"""
    person = db.query(Personnel).filter(Personnel.id == person_id).first()
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person nicht gefunden"
        )
    
    update_data = person_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(person, key, value)
    
    db.commit()
    db.refresh(person)
    
    return PersonnelResponse(
        id=person.id,
        stammrollennummer=person.stammrollennummer,
        vorname=person.vorname,
        nachname=person.nachname,
        dienstgrad=person.dienstgrad,
        aktiv=person.aktiv,
        group_id=person.group_id,
        group_name=person.group.name if person.group else None,
        created_at=person.created_at.isoformat()
    )


@router.delete("/{person_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_personnel(
    person_id: int,
    db: Session = Depends(get_db),
    _: any = Depends(get_current_user)
):
    """Löscht einen Mitarbeiter (Admin-geschützt)"""
    person = db.query(Personnel).filter(Personnel.id == person_id).first()
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person nicht gefunden"
        )
    
    db.delete(person)
    db.commit()
    return None
