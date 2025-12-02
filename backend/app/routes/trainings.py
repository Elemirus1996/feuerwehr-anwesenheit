"""
Trainings API Routes für die Feuerwehr Anwesenheits-App
Feature 15: Team-Features - Ausbildungs-Tracking
"""

from typing import List, Optional
from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Training, PersonnelTraining, Personnel, AdminUser, TrainingCategory
from ..utils.auth import get_current_user

router = APIRouter(prefix="/api/trainings", tags=["Trainings"])


# Pydantic Modelle
class TrainingCreate(BaseModel):
    name: str
    category: str = "lehrgang"
    duration_hours: Optional[int] = None
    validity_months: Optional[int] = None


class TrainingUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    duration_hours: Optional[int] = None
    validity_months: Optional[int] = None


class TrainingResponse(BaseModel):
    id: int
    name: str
    category: str
    duration_hours: Optional[int]
    validity_months: Optional[int]
    personnel_count: int


class PersonnelTrainingCreate(BaseModel):
    training_id: int
    completed_date: str
    expires_date: Optional[str] = None
    certificate_number: Optional[str] = None
    instructor: Optional[str] = None
    notes: Optional[str] = None


class PersonnelTrainingUpdate(BaseModel):
    completed_date: Optional[str] = None
    expires_date: Optional[str] = None
    certificate_number: Optional[str] = None
    instructor: Optional[str] = None
    notes: Optional[str] = None


class PersonnelTrainingResponse(BaseModel):
    id: int
    personnel_id: int
    training_id: int
    training_name: str
    training_category: str
    completed_date: str
    expires_date: Optional[str]
    certificate_number: Optional[str]
    instructor: Optional[str]
    notes: Optional[str]
    is_expired: bool
    days_until_expiry: Optional[int]


class ExpiringTrainingResponse(BaseModel):
    id: int
    personnel_id: int
    personnel_name: str
    stammrollennummer: str
    training_id: int
    training_name: str
    expires_date: str
    days_until_expiry: int


# Routen für Schulungen
@router.get("/", response_model=List[TrainingResponse])
def get_trainings(
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user)
):
    """Gibt alle Schulungen zurück"""
    query = db.query(Training)
    
    if category:
        try:
            cat = TrainingCategory(category)
            query = query.filter(Training.category == cat)
        except ValueError:
            pass
    
    trainings = query.order_by(Training.name).all()
    
    result = []
    for t in trainings:
        personnel_count = db.query(PersonnelTraining).filter(
            PersonnelTraining.training_id == t.id
        ).count()
        
        result.append(TrainingResponse(
            id=t.id,
            name=t.name,
            category=t.category.value,
            duration_hours=t.duration_hours,
            validity_months=t.validity_months,
            personnel_count=personnel_count
        ))
    
    return result


@router.get("/categories")
def get_training_categories():
    """Gibt alle Schulungs-Kategorien zurück"""
    return [
        {"value": "lehrgang", "label": "Lehrgang"},
        {"value": "fortbildung", "label": "Fortbildung"},
        {"value": "zertifikat", "label": "Zertifikat"}
    ]


@router.post("/", response_model=TrainingResponse, status_code=status.HTTP_201_CREATED)
def create_training(
    training_data: TrainingCreate,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user)
):
    """Erstellt eine neue Schulung"""
    try:
        category = TrainingCategory(training_data.category)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ungültige Kategorie: {training_data.category}"
        )
    
    training = Training(
        name=training_data.name,
        category=category,
        duration_hours=training_data.duration_hours,
        validity_months=training_data.validity_months
    )
    
    db.add(training)
    db.commit()
    db.refresh(training)
    
    return TrainingResponse(
        id=training.id,
        name=training.name,
        category=training.category.value,
        duration_hours=training.duration_hours,
        validity_months=training.validity_months,
        personnel_count=0
    )


@router.get("/{training_id}", response_model=TrainingResponse)
def get_training(
    training_id: int,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user)
):
    """Gibt eine einzelne Schulung zurück"""
    training = db.query(Training).filter(Training.id == training_id).first()
    
    if not training:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schulung nicht gefunden"
        )
    
    personnel_count = db.query(PersonnelTraining).filter(
        PersonnelTraining.training_id == training.id
    ).count()
    
    return TrainingResponse(
        id=training.id,
        name=training.name,
        category=training.category.value,
        duration_hours=training.duration_hours,
        validity_months=training.validity_months,
        personnel_count=personnel_count
    )


@router.put("/{training_id}", response_model=TrainingResponse)
def update_training(
    training_id: int,
    training_data: TrainingUpdate,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user)
):
    """Aktualisiert eine Schulung"""
    training = db.query(Training).filter(Training.id == training_id).first()
    
    if not training:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schulung nicht gefunden"
        )
    
    if training_data.name is not None:
        training.name = training_data.name
    
    if training_data.category is not None:
        try:
            training.category = TrainingCategory(training_data.category)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ungültige Kategorie: {training_data.category}"
            )
    
    if training_data.duration_hours is not None:
        training.duration_hours = training_data.duration_hours
    
    if training_data.validity_months is not None:
        training.validity_months = training_data.validity_months
    
    db.commit()
    db.refresh(training)
    
    personnel_count = db.query(PersonnelTraining).filter(
        PersonnelTraining.training_id == training.id
    ).count()
    
    return TrainingResponse(
        id=training.id,
        name=training.name,
        category=training.category.value,
        duration_hours=training.duration_hours,
        validity_months=training.validity_months,
        personnel_count=personnel_count
    )


@router.delete("/{training_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_training(
    training_id: int,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user)
):
    """Löscht eine Schulung"""
    training = db.query(Training).filter(Training.id == training_id).first()
    
    if not training:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schulung nicht gefunden"
        )
    
    # Lösche auch alle PersonnelTraining-Einträge
    db.query(PersonnelTraining).filter(
        PersonnelTraining.training_id == training_id
    ).delete()
    
    db.delete(training)
    db.commit()
    return None


# Ablaufende Zertifikate
@router.get("/expiring", response_model=List[ExpiringTrainingResponse])
def get_expiring_trainings(
    days: int = 90,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user)
):
    """Gibt alle ablaufenden Zertifikate zurück"""
    threshold_date = date.today() + timedelta(days=days)
    
    expiring = db.query(PersonnelTraining).filter(
        PersonnelTraining.expires_date != None,
        PersonnelTraining.expires_date <= threshold_date,
        PersonnelTraining.expires_date >= date.today()
    ).all()
    
    result = []
    for pt in expiring:
        personnel = pt.personnel
        training = pt.training
        
        if personnel and training:
            days_until = (pt.expires_date - date.today()).days
            result.append(ExpiringTrainingResponse(
                id=pt.id,
                personnel_id=personnel.id,
                personnel_name=f"{personnel.vorname} {personnel.nachname}",
                stammrollennummer=personnel.stammrollennummer,
                training_id=training.id,
                training_name=training.name,
                expires_date=pt.expires_date.isoformat(),
                days_until_expiry=days_until
            ))
    
    # Sortiere nach Ablaufdatum
    result.sort(key=lambda x: x.days_until_expiry)
    
    return result


# Routen für Personnel Trainings
@router.get("/personnel/{personnel_id}", response_model=List[PersonnelTrainingResponse])
def get_personnel_trainings(
    personnel_id: int,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user)
):
    """Gibt alle Schulungen eines Mitglieds zurück"""
    personnel = db.query(Personnel).filter(Personnel.id == personnel_id).first()
    
    if not personnel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person nicht gefunden"
        )
    
    pt_list = db.query(PersonnelTraining).filter(
        PersonnelTraining.personnel_id == personnel_id
    ).all()
    
    result = []
    today = date.today()
    
    for pt in pt_list:
        training = pt.training
        if not training:
            continue
        
        is_expired = False
        days_until = None
        
        if pt.expires_date:
            is_expired = pt.expires_date < today
            days_until = (pt.expires_date - today).days
        
        result.append(PersonnelTrainingResponse(
            id=pt.id,
            personnel_id=pt.personnel_id,
            training_id=pt.training_id,
            training_name=training.name,
            training_category=training.category.value,
            completed_date=pt.completed_date.isoformat(),
            expires_date=pt.expires_date.isoformat() if pt.expires_date else None,
            certificate_number=pt.certificate_number,
            instructor=pt.instructor,
            notes=pt.notes,
            is_expired=is_expired,
            days_until_expiry=days_until
        ))
    
    return result


@router.post("/personnel/{personnel_id}", response_model=PersonnelTrainingResponse, status_code=status.HTTP_201_CREATED)
def assign_training_to_personnel(
    personnel_id: int,
    pt_data: PersonnelTrainingCreate,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user)
):
    """Weist einem Mitglied eine Schulung zu"""
    personnel = db.query(Personnel).filter(Personnel.id == personnel_id).first()
    
    if not personnel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person nicht gefunden"
        )
    
    training = db.query(Training).filter(Training.id == pt_data.training_id).first()
    
    if not training:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schulung nicht gefunden"
        )
    
    # Parse Datum
    try:
        completed_date = date.fromisoformat(pt_data.completed_date)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ungültiges Datum für completed_date"
        )
    
    expires_date = None
    if pt_data.expires_date:
        try:
            expires_date = date.fromisoformat(pt_data.expires_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ungültiges Datum für expires_date"
            )
    elif training.validity_months:
        # Berechne Ablaufdatum basierend auf Gültigkeitsdauer
        from dateutil.relativedelta import relativedelta
        expires_date = completed_date + relativedelta(months=training.validity_months)
    
    pt = PersonnelTraining(
        personnel_id=personnel_id,
        training_id=pt_data.training_id,
        completed_date=completed_date,
        expires_date=expires_date,
        certificate_number=pt_data.certificate_number,
        instructor=pt_data.instructor,
        notes=pt_data.notes
    )
    
    db.add(pt)
    db.commit()
    db.refresh(pt)
    
    today = date.today()
    is_expired = False
    days_until = None
    
    if pt.expires_date:
        is_expired = pt.expires_date < today
        days_until = (pt.expires_date - today).days
    
    return PersonnelTrainingResponse(
        id=pt.id,
        personnel_id=pt.personnel_id,
        training_id=pt.training_id,
        training_name=training.name,
        training_category=training.category.value,
        completed_date=pt.completed_date.isoformat(),
        expires_date=pt.expires_date.isoformat() if pt.expires_date else None,
        certificate_number=pt.certificate_number,
        instructor=pt.instructor,
        notes=pt.notes,
        is_expired=is_expired,
        days_until_expiry=days_until
    )


@router.put("/personnel/{personnel_id}/{training_record_id}", response_model=PersonnelTrainingResponse)
def update_personnel_training(
    personnel_id: int,
    training_record_id: int,
    pt_data: PersonnelTrainingUpdate,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user)
):
    """Aktualisiert einen Schulungs-Eintrag"""
    pt = db.query(PersonnelTraining).filter(
        PersonnelTraining.id == training_record_id,
        PersonnelTraining.personnel_id == personnel_id
    ).first()
    
    if not pt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schulungs-Eintrag nicht gefunden"
        )
    
    if pt_data.completed_date is not None:
        try:
            pt.completed_date = date.fromisoformat(pt_data.completed_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ungültiges Datum für completed_date"
            )
    
    if pt_data.expires_date is not None:
        try:
            pt.expires_date = date.fromisoformat(pt_data.expires_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ungültiges Datum für expires_date"
            )
    
    if pt_data.certificate_number is not None:
        pt.certificate_number = pt_data.certificate_number
    
    if pt_data.instructor is not None:
        pt.instructor = pt_data.instructor
    
    if pt_data.notes is not None:
        pt.notes = pt_data.notes
    
    db.commit()
    db.refresh(pt)
    
    training = pt.training
    today = date.today()
    is_expired = False
    days_until = None
    
    if pt.expires_date:
        is_expired = pt.expires_date < today
        days_until = (pt.expires_date - today).days
    
    return PersonnelTrainingResponse(
        id=pt.id,
        personnel_id=pt.personnel_id,
        training_id=pt.training_id,
        training_name=training.name if training else "Unbekannt",
        training_category=training.category.value if training else "unbekannt",
        completed_date=pt.completed_date.isoformat(),
        expires_date=pt.expires_date.isoformat() if pt.expires_date else None,
        certificate_number=pt.certificate_number,
        instructor=pt.instructor,
        notes=pt.notes,
        is_expired=is_expired,
        days_until_expiry=days_until
    )


@router.delete("/personnel/{personnel_id}/{training_record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_personnel_training(
    personnel_id: int,
    training_record_id: int,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user)
):
    """Löscht einen Schulungs-Eintrag"""
    pt = db.query(PersonnelTraining).filter(
        PersonnelTraining.id == training_record_id,
        PersonnelTraining.personnel_id == personnel_id
    ).first()
    
    if not pt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schulungs-Eintrag nicht gefunden"
        )
    
    db.delete(pt)
    db.commit()
    return None
