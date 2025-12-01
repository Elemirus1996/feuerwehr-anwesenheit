"""
Sessions API Routes für die Feuerwehr Anwesenheits-App
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Session as SessionModel, Attendance, EventType, SessionStatus
from ..services.session_manager import SessionManager
from ..services.qr_generator import QRGenerator
from ..utils.auth import get_current_user

router = APIRouter(prefix="/api/sessions", tags=["Sessions"])


# Pydantic Modelle
class SessionCreate(BaseModel):
    event_type: EventType


class SessionEnd(BaseModel):
    stammrollennummer: Optional[str] = None


class SessionResponse(BaseModel):
    id: int
    event_type: str
    event_type_display: str
    start_time: str
    end_time: Optional[str]
    status: str
    ended_by_stammrollennummer: Optional[str]
    attendee_count: int
    remaining_minutes: Optional[int]
    created_at: str


class SessionListResponse(BaseModel):
    sessions: List[SessionResponse]
    total: int


# Öffentliche Routen (für Check-in Interface)
@router.get("/active")
def get_active_session(db: Session = Depends(get_db)):
    """Gibt die aktuelle aktive Session zurück"""
    session = SessionManager.get_active_session(db)
    if not session:
        return {"active": False, "session": None}
    
    attendee_count = db.query(Attendance).filter(
        Attendance.session_id == session.id,
        Attendance.check_out_time == None
    ).count()
    
    return {
        "active": True,
        "session": {
            "id": session.id,
            "event_type": session.event_type.value,
            "event_type_display": session.get_event_type_display(),
            "start_time": session.start_time.isoformat(),
            "attendee_count": attendee_count,
            "remaining_minutes": SessionManager.get_session_remaining_time(session)
        }
    }


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_session(session_data: SessionCreate, db: Session = Depends(get_db)):
    """Erstellt eine neue Session"""
    try:
        session = SessionManager.create_session(db, session_data.event_type)
        
        # QR-Token generieren und speichern
        token = QRGenerator.generate_session_token(session.id)
        session.qr_token = token
        db.commit()
        db.refresh(session)
        
        return {
            "id": session.id,
            "event_type": session.event_type.value,
            "event_type_display": session.get_event_type_display(),
            "start_time": session.start_time.isoformat(),
            "status": session.status.value
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{session_id}/end")
def end_session(
    session_id: int,
    end_data: SessionEnd,
    db: Session = Depends(get_db)
):
    """Beendet eine Session"""
    try:
        session = SessionManager.end_session(
            db, 
            session_id, 
            stammrollennummer=end_data.stammrollennummer
        )
        return {
            "id": session.id,
            "status": session.status.value,
            "end_time": session.end_time.isoformat() if session.end_time else None,
            "message": "Session erfolgreich beendet"
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/event-types")
def get_event_types():
    """Gibt alle verfügbaren Event-Typen zurück"""
    return [
        {"value": "einsatz", "label": "Einsatz", "auto_timeout": False},
        {"value": "uebungsdienst", "label": "Übungsdienst", "auto_timeout": True},
        {"value": "arbeitsdienst_a", "label": "Arbeitsdienst Tour A", "auto_timeout": True},
        {"value": "arbeitsdienst_b", "label": "Arbeitsdienst Tour B", "auto_timeout": True},
        {"value": "arbeitsdienst_c", "label": "Arbeitsdienst Tour C", "auto_timeout": True},
    ]


# Admin-geschützte Routen
@router.get("/", response_model=SessionListResponse)
def list_sessions(
    status_filter: Optional[str] = None,
    event_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    _: any = Depends(get_current_user)
):
    """Gibt alle Sessions zurück (Admin-geschützt)"""
    query = db.query(SessionModel)
    
    if status_filter:
        query = query.filter(SessionModel.status == status_filter)
    
    if event_type:
        query = query.filter(SessionModel.event_type == event_type)
    
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
            query = query.filter(SessionModel.start_time >= start_dt)
        except ValueError:
            pass
    
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
            query = query.filter(SessionModel.start_time <= end_dt)
        except ValueError:
            pass
    
    total = query.count()
    sessions = query.order_by(SessionModel.start_time.desc()).offset(offset).limit(limit).all()
    
    result = []
    for session in sessions:
        attendee_count = db.query(Attendance).filter(
            Attendance.session_id == session.id
        ).count()
        
        result.append(SessionResponse(
            id=session.id,
            event_type=session.event_type.value,
            event_type_display=session.get_event_type_display(),
            start_time=session.start_time.isoformat(),
            end_time=session.end_time.isoformat() if session.end_time else None,
            status=session.status.value,
            ended_by_stammrollennummer=session.ended_by_stammrollennummer,
            attendee_count=attendee_count,
            remaining_minutes=SessionManager.get_session_remaining_time(session) if session.status == SessionStatus.ACTIVE else None,
            created_at=session.created_at.isoformat()
        ))
    
    return SessionListResponse(sessions=result, total=total)


@router.get("/{session_id}")
def get_session_detail(
    session_id: int,
    db: Session = Depends(get_db),
    _: any = Depends(get_current_user)
):
    """Gibt Details zu einer Session zurück (Admin-geschützt)"""
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session nicht gefunden"
        )
    
    attendances = db.query(Attendance).filter(
        Attendance.session_id == session_id
    ).order_by(Attendance.check_in_time).all()
    
    attendance_list = []
    for att in attendances:
        person = att.person
        duration = None
        if att.check_out_time:
            delta = att.check_out_time - att.check_in_time
            duration = int(delta.total_seconds() / 60)
        
        attendance_list.append({
            "id": att.id,
            "stammrollennummer": att.stammrollennummer,
            "vorname": person.vorname if person else "Unbekannt",
            "nachname": person.nachname if person else "Unbekannt",
            "dienstgrad": person.dienstgrad if person else "-",
            "check_in_time": att.check_in_time.isoformat(),
            "check_out_time": att.check_out_time.isoformat() if att.check_out_time else None,
            "duration_minutes": duration
        })
    
    return {
        "id": session.id,
        "event_type": session.event_type.value,
        "event_type_display": session.get_event_type_display(),
        "start_time": session.start_time.isoformat(),
        "end_time": session.end_time.isoformat() if session.end_time else None,
        "status": session.status.value,
        "ended_by_stammrollennummer": session.ended_by_stammrollennummer,
        "created_at": session.created_at.isoformat(),
        "attendances": attendance_list,
        "total_attendees": len(attendance_list)
    }


# QR-Code Routen
@router.get("/{session_id}/qr")
def get_session_qr_code(
    session_id: int,
    db: Session = Depends(get_db)
):
    """Gibt den QR-Code für eine Session als PNG zurück"""
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session nicht gefunden"
        )
    
    # Nur für aktive Sessions
    if session.status != SessionStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="QR-Code nur für aktive Sessions verfügbar"
        )
    
    # Token aus Session oder neu generieren
    token = session.qr_token
    if not token:
        token = QRGenerator.generate_session_token(session_id)
        session.qr_token = token
        db.commit()
    
    # QR-Code generieren
    png_bytes = QRGenerator.generate_qr_code_image(session_id, token)
    
    return Response(
        content=png_bytes,
        media_type="image/png",
        headers={
            "Content-Disposition": f"inline; filename=qr_session_{session_id}.png"
        }
    )


@router.get("/checkin/token/{token}")
def validate_checkin_token(
    token: str,
    db: Session = Depends(get_db)
):
    """Validiert einen Check-in Token und gibt Session-Daten zurück"""
    session_id = QRGenerator.validate_session_token(token)
    
    if session_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token ungültig oder abgelaufen"
        )
    
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session nicht gefunden"
        )
    
    if session.status != SessionStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session ist nicht mehr aktiv"
        )
    
    return {
        "valid": True,
        "session": {
            "id": session.id,
            "event_type": session.event_type.value,
            "event_type_display": session.get_event_type_display(),
            "start_time": session.start_time.isoformat()
        }
    }
