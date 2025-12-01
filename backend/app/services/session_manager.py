"""
Session-Manager Service für die Feuerwehr Anwesenheits-App
Verwaltet automatische Session-Timeouts und Session-Logik
"""

import os
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session

from ..models import Session as SessionModel, Attendance, Personnel, EventType, SessionStatus, MIN_RANG_EINSATZ_BEENDEN

# Konfiguration: Auto-Timeout in Stunden (Standard: 3 Stunden)
AUTO_TIMEOUT_HOURS = float(os.getenv("AUTO_TIMEOUT_HOURS", "3"))


class SessionManager:
    """Verwaltet Sessions und deren Logik"""

    @staticmethod
    def get_active_session(db: Session) -> Optional[SessionModel]:
        """Gibt die aktive Session zurück, falls vorhanden"""
        return db.query(SessionModel).filter(
            SessionModel.status == SessionStatus.ACTIVE
        ).first()

    @staticmethod
    def create_session(db: Session, event_type: EventType) -> SessionModel:
        """Erstellt eine neue Session"""
        # Prüfe ob bereits eine aktive Session existiert
        active_session = SessionManager.get_active_session(db)
        if active_session:
            raise ValueError("Es existiert bereits eine aktive Session")

        session = SessionModel(
            event_type=event_type,
            start_time=datetime.utcnow(),
            status=SessionStatus.ACTIVE
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def end_session(
        db: Session, 
        session_id: int, 
        stammrollennummer: Optional[str] = None,
        force: bool = False
    ) -> SessionModel:
        """
        Beendet eine Session
        
        Bei Einsätzen muss die Person mindestens UBM-Rang haben
        Bei anderen Event-Typen kann die Session ohne Rangprüfung beendet werden
        """
        session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not session:
            raise ValueError("Session nicht gefunden")
        
        if session.status != SessionStatus.ACTIVE:
            raise ValueError("Session ist nicht aktiv")

        # Rangprüfung für Einsätze
        if session.event_type == EventType.EINSATZ and not force:
            if not stammrollennummer:
                raise ValueError("Stammrollennummer erforderlich um Einsatz zu beenden")
            
            person = db.query(Personnel).filter(
                Personnel.stammrollennummer == stammrollennummer
            ).first()
            
            if not person:
                raise ValueError("Person nicht gefunden")
            
            if not person.kann_einsatz_beenden():
                raise ValueError(
                    f"Nur Personen mit Rang >= UBM können Einsätze beenden. "
                    f"Aktueller Rang: {person.dienstgrad}"
                )

        # Alle noch anwesenden Personen auschecken
        SessionManager.checkout_all_attendees(db, session_id)

        # Session beenden
        session.end_time = datetime.utcnow()
        session.status = SessionStatus.COMPLETED
        session.ended_by_stammrollennummer = stammrollennummer
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def check_in(db: Session, session_id: int, stammrollennummer: str) -> Attendance:
        """Check-in einer Person zu einer Session"""
        # Prüfe ob Session existiert und aktiv ist
        session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not session:
            raise ValueError("Session nicht gefunden")
        if session.status != SessionStatus.ACTIVE:
            raise ValueError("Session ist nicht aktiv")

        # Prüfe ob Person existiert
        person = db.query(Personnel).filter(
            Personnel.stammrollennummer == stammrollennummer
        ).first()
        if not person:
            raise ValueError("Person mit dieser Stammrollennummer nicht gefunden")
        if not person.aktiv:
            raise ValueError("Person ist nicht aktiv")

        # Prüfe ob Person bereits eingecheckt ist
        existing = db.query(Attendance).filter(
            Attendance.session_id == session_id,
            Attendance.stammrollennummer == stammrollennummer,
            Attendance.check_out_time == None
        ).first()
        if existing:
            raise ValueError("Person ist bereits eingecheckt")

        # Check-in erstellen
        attendance = Attendance(
            session_id=session_id,
            stammrollennummer=stammrollennummer,
            check_in_time=datetime.utcnow()
        )
        db.add(attendance)
        db.commit()
        db.refresh(attendance)
        return attendance

    @staticmethod
    def check_out(db: Session, session_id: int, stammrollennummer: str) -> Attendance:
        """Check-out einer Person aus einer Session"""
        attendance = db.query(Attendance).filter(
            Attendance.session_id == session_id,
            Attendance.stammrollennummer == stammrollennummer,
            Attendance.check_out_time == None
        ).first()
        
        if not attendance:
            raise ValueError("Kein aktiver Check-in für diese Person gefunden")

        attendance.check_out_time = datetime.utcnow()
        db.commit()
        db.refresh(attendance)
        return attendance

    @staticmethod
    def checkout_all_attendees(db: Session, session_id: int) -> int:
        """Checkt alle noch anwesenden Personen aus einer Session aus"""
        now = datetime.utcnow()
        result = db.query(Attendance).filter(
            Attendance.session_id == session_id,
            Attendance.check_out_time == None
        ).update({"check_out_time": now})
        db.commit()
        return result

    @staticmethod
    def get_current_attendees(db: Session, session_id: int) -> List[dict]:
        """Gibt alle aktuell anwesenden Personen einer Session zurück"""
        attendances = db.query(Attendance).filter(
            Attendance.session_id == session_id,
            Attendance.check_out_time == None
        ).all()

        result = []
        for att in attendances:
            person = att.person
            result.append({
                "id": att.id,
                "stammrollennummer": att.stammrollennummer,
                "vorname": person.vorname if person else "Unbekannt",
                "nachname": person.nachname if person else "Unbekannt",
                "dienstgrad": person.dienstgrad if person else "Unbekannt",
                "check_in_time": att.check_in_time.isoformat()
            })
        return result

    @staticmethod
    def get_session_remaining_time(session: SessionModel) -> Optional[int]:
        """
        Berechnet die verbleibende Zeit in Minuten für eine Session
        Nur für Sessions mit Auto-Timeout (nicht für Einsätze)
        """
        if session.event_type == EventType.EINSATZ:
            return None  # Einsätze haben kein Auto-Timeout

        timeout_delta = timedelta(hours=AUTO_TIMEOUT_HOURS)
        session_end = session.start_time + timeout_delta
        remaining = session_end - datetime.utcnow()
        
        if remaining.total_seconds() < 0:
            return 0
        
        return int(remaining.total_seconds() / 60)

    @staticmethod
    def check_expired_sessions(db: Session) -> List[int]:
        """
        Prüft auf abgelaufene Sessions und beendet diese automatisch
        Wird vom Background-Worker aufgerufen
        Gibt eine Liste der beendeten Session-IDs zurück
        """
        timeout_delta = timedelta(hours=AUTO_TIMEOUT_HOURS)
        threshold_time = datetime.utcnow() - timeout_delta

        # Finde alle aktiven Sessions (außer Einsätze) die abgelaufen sind
        expired_sessions = db.query(SessionModel).filter(
            SessionModel.status == SessionStatus.ACTIVE,
            SessionModel.event_type != EventType.EINSATZ,
            SessionModel.start_time < threshold_time
        ).all()

        ended_ids = []
        for session in expired_sessions:
            try:
                SessionManager.end_session(db, session.id, force=True)
                ended_ids.append(session.id)
                print(f"Session {session.id} automatisch beendet (Timeout)")
            except Exception as e:
                print(f"Fehler beim Beenden von Session {session.id}: {e}")

        return ended_ids
