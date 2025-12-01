"""
Attendance API Routes für die Feuerwehr Anwesenheits-App
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.session_manager import SessionManager

router = APIRouter(prefix="/api/attendance", tags=["Attendance"])


# Pydantic Modelle
class CheckInRequest(BaseModel):
    session_id: int
    stammrollennummer: str


class CheckOutRequest(BaseModel):
    session_id: int
    stammrollennummer: str


class AttendeeResponse(BaseModel):
    id: int
    stammrollennummer: str
    vorname: str
    nachname: str
    dienstgrad: str
    check_in_time: str


# Routen
@router.post("/check-in")
def check_in(request: CheckInRequest, db: Session = Depends(get_db)):
    """Check-in einer Person zu einer Session"""
    try:
        attendance = SessionManager.check_in(
            db,
            request.session_id,
            request.stammrollennummer
        )
        person = attendance.person
        return {
            "success": True,
            "message": f"{person.vorname} {person.nachname} erfolgreich eingecheckt",
            "attendance": {
                "id": attendance.id,
                "stammrollennummer": attendance.stammrollennummer,
                "vorname": person.vorname,
                "nachname": person.nachname,
                "dienstgrad": person.dienstgrad,
                "check_in_time": attendance.check_in_time.isoformat()
            }
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/check-out")
def check_out(request: CheckOutRequest, db: Session = Depends(get_db)):
    """Check-out einer Person aus einer Session"""
    try:
        attendance = SessionManager.check_out(
            db,
            request.session_id,
            request.stammrollennummer
        )
        person = attendance.person
        duration = attendance.get_duration_minutes()
        return {
            "success": True,
            "message": f"{person.vorname} {person.nachname} erfolgreich ausgecheckt",
            "attendance": {
                "id": attendance.id,
                "stammrollennummer": attendance.stammrollennummer,
                "vorname": person.vorname,
                "nachname": person.nachname,
                "dienstgrad": person.dienstgrad,
                "check_in_time": attendance.check_in_time.isoformat(),
                "check_out_time": attendance.check_out_time.isoformat(),
                "duration_minutes": duration
            }
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/current/{session_id}", response_model=List[AttendeeResponse])
def get_current_attendees(session_id: int, db: Session = Depends(get_db)):
    """Gibt alle aktuell anwesenden Personen einer Session zurück"""
    attendees = SessionManager.get_current_attendees(db, session_id)
    return [AttendeeResponse(**a) for a in attendees]


@router.post("/toggle")
def toggle_attendance(request: CheckInRequest, db: Session = Depends(get_db)):
    """
    Schaltet den Anwesenheitsstatus um:
    - Wenn eingecheckt: Check-out
    - Wenn nicht eingecheckt: Check-in
    """
    from ..models import Attendance
    
    # Prüfe ob Person bereits eingecheckt ist
    existing = db.query(Attendance).filter(
        Attendance.session_id == request.session_id,
        Attendance.stammrollennummer == request.stammrollennummer,
        Attendance.check_out_time == None
    ).first()
    
    if existing:
        # Check-out
        return check_out(CheckOutRequest(
            session_id=request.session_id,
            stammrollennummer=request.stammrollennummer
        ), db)
    else:
        # Check-in
        return check_in(request, db)
