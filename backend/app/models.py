"""
Datenbank-Modelle für die Feuerwehr Anwesenheits-App
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class EventType(str, Enum):
    """Event-Typen für Sessions"""
    EINSATZ = "einsatz"
    UEBUNGSDIENST = "uebungsdienst"
    ARBEITSDIENST_A = "arbeitsdienst_a"
    ARBEITSDIENST_B = "arbeitsdienst_b"
    ARBEITSDIENST_C = "arbeitsdienst_c"


class SessionStatus(str, Enum):
    """Status einer Session"""
    ACTIVE = "active"
    COMPLETED = "completed"


# Dienstgrade mit Hierarchie (höhere Zahl = höherer Rang)
DIENSTGRADE = {
    "FM": ("Feuerwehrmann", 1),
    "OFM": ("Oberfeuerwehrmann", 2),
    "HFM": ("Hauptfeuerwehrmann", 3),
    "UBM": ("Unterbrandmeister", 4),
    "BM": ("Brandmeister", 5),
    "OBM": ("Oberbrandmeister", 6),
    "HBM": ("Hauptbrandmeister", 7),
    "BI": ("Brandinspektor", 8),
}

# Mindestrang für das Beenden einer Einsatz-Session
MIN_RANG_EINSATZ_BEENDEN = 4  # UBM


class Personnel(Base):
    """Personal-Tabelle"""
    __tablename__ = "personnel"

    id = Column(Integer, primary_key=True, index=True)
    stammrollennummer = Column(String(50), unique=True, nullable=False, index=True)
    vorname = Column(String(100), nullable=False)
    nachname = Column(String(100), nullable=False)
    dienstgrad = Column(String(10), nullable=False, default="FM")
    aktiv = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship zu Attendance
    attendances = relationship("Attendance", back_populates="person")

    def get_rang_level(self) -> int:
        """Gibt das Rang-Level zurück (für Berechtigungsprüfungen)"""
        return DIENSTGRADE.get(self.dienstgrad, ("", 0))[1]

    def kann_einsatz_beenden(self) -> bool:
        """Prüft ob die Person einen Einsatz beenden kann"""
        return self.get_rang_level() >= MIN_RANG_EINSATZ_BEENDEN


class Session(Base):
    """Sessions-Tabelle (Ereignisse)"""
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(SQLEnum(EventType), nullable=False)
    start_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    end_time = Column(DateTime, nullable=True)
    status = Column(SQLEnum(SessionStatus), default=SessionStatus.ACTIVE, nullable=False)
    ended_by_stammrollennummer = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship zu Attendance
    attendances = relationship("Attendance", back_populates="session")

    def is_active(self) -> bool:
        """Prüft ob die Session aktiv ist"""
        return self.status == SessionStatus.ACTIVE

    def get_event_type_display(self) -> str:
        """Gibt den Anzeigenamen des Event-Typs zurück"""
        display_names = {
            EventType.EINSATZ: "Einsatz",
            EventType.UEBUNGSDIENST: "Übungsdienst",
            EventType.ARBEITSDIENST_A: "Arbeitsdienst Tour A",
            EventType.ARBEITSDIENST_B: "Arbeitsdienst Tour B",
            EventType.ARBEITSDIENST_C: "Arbeitsdienst Tour C",
        }
        return display_names.get(self.event_type, str(self.event_type))


class Attendance(Base):
    """Anwesenheits-Tabelle"""
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    stammrollennummer = Column(String(50), ForeignKey("personnel.stammrollennummer"), nullable=False)
    check_in_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    check_out_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    session = relationship("Session", back_populates="attendances")
    person = relationship("Personnel", back_populates="attendances")

    def get_duration_minutes(self) -> Optional[int]:
        """Berechnet die Anwesenheitsdauer in Minuten"""
        if self.check_out_time:
            delta = self.check_out_time - self.check_in_time
            return int(delta.total_seconds() / 60)
        return None


class AdminUser(Base):
    """Admin-Benutzer Tabelle"""
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
