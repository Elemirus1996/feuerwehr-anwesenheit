"""
Datenbank-Modelle für die Feuerwehr Anwesenheits-App
"""

from datetime import datetime, date
from enum import Enum
from typing import Optional
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


# ===== Feature 12: Personalization Enums =====
class ThemeType(str, Enum):
    """Theme-Typen für Benutzereinstellungen"""
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"


class FontSize(str, Enum):
    """Schriftgrößen-Optionen"""
    NORMAL = "normal"
    LARGE = "large"
    EXTRA_LARGE = "extra_large"


# ===== Feature 15: Team-Features Enums =====
class AnnouncementPriority(str, Enum):
    """Prioritäten für Ankündigungen"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class TrainingCategory(str, Enum):
    """Kategorien für Schulungen"""
    LEHRGANG = "lehrgang"
    FORTBILDUNG = "fortbildung"
    ZERTIFIKAT = "zertifikat"


# ===== Feature 9: Security Enums =====
class RoleName(str, Enum):
    """Rollen-Namen"""
    ADMIN = "admin"
    WEHRFUEHRER = "wehrfuehrer"
    GRUPPENFUEHRER = "gruppenfuehrer"
    MITGLIED = "mitglied"


class AuditAction(str, Enum):
    """Aktionen für Audit-Log"""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"


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
# Korrekte Hierarchie: FM < OFM < HFM < UBM < BM < OBM < HBM < BI
DIENSTGRADE = {
    "FM": ("Feuerwehrmann", 1),
    "OFM": ("Oberfeuerwehrmann", 2),
    "HFM": ("Hauptfeuerwehrmann", 3),
    "UBM": ("Unterbrandmeister", 4),  # Mindestrang für Einsatz-Ende
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
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    attendances = relationship("Attendance", back_populates="person")
    group = relationship("Group", back_populates="members")
    role = relationship("Role", back_populates="personnel")
    trainings = relationship("PersonnelTraining", back_populates="personnel")

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
    qr_token = Column(String(500), nullable=True)
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
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    role = relationship("Role", back_populates="admin_users")
    preferences = relationship("UserPreferences", back_populates="admin_user", uselist=False)


# ===== Feature 12: Personalization Models =====

class UserPreferences(Base):
    """Benutzereinstellungen für Personalisierung"""
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("admin_users.id"), unique=True, nullable=False)
    theme = Column(SQLEnum(ThemeType), default=ThemeType.AUTO, nullable=False)
    font_size = Column(SQLEnum(FontSize), default=FontSize.NORMAL, nullable=False)
    high_contrast = Column(Boolean, default=False, nullable=False)
    language = Column(String(5), default="de", nullable=False)

    # Relationships
    admin_user = relationship("AdminUser", back_populates="preferences")


# ===== Feature 15: Team-Features Models =====

class Announcement(Base):
    """Ankündigungen für Schwarzes Brett"""
    __tablename__ = "announcements"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    author_id = Column(Integer, ForeignKey("admin_users.id"), nullable=False)
    priority = Column(SQLEnum(AnnouncementPriority), default=AnnouncementPriority.NORMAL, nullable=False)
    valid_from = Column(DateTime, default=datetime.utcnow, nullable=False)
    valid_until = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    target_groups = Column(Text, nullable=True)  # JSON Array stored as text
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class SystemSettings(Base):
    """System-Einstellungen Tabelle (Singleton - nur ein Eintrag)"""
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)
    # Backup-Einstellungen
    backup_enabled = Column(Boolean, default=True, nullable=False)
    backup_path = Column(String(500), default="./backups/", nullable=False)
    backup_schedule_time = Column(String(10), default="03:00", nullable=False)
    backup_retention_days = Column(Integer, default=30, nullable=False)
    # Zeitstempel des letzten Backups
    last_backup_time = Column(DateTime, nullable=True)
    last_backup_size = Column(Integer, nullable=True)  # Größe in Bytes
    # Allgemeine Einstellungen
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
