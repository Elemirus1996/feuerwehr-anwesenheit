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

    # Relationships
    author = relationship("AdminUser")


class Group(Base):
    """Gruppen für Personal (Jugend, Aktive, Ehrenabteilung, etc.)"""
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    color = Column(String(7), default="#666666", nullable=False)  # Hex color
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    members = relationship("Personnel", back_populates="group")


class Training(Base):
    """Schulungen und Ausbildungen"""
    __tablename__ = "trainings"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    category = Column(SQLEnum(TrainingCategory), default=TrainingCategory.LEHRGANG, nullable=False)
    duration_hours = Column(Integer, nullable=True)
    validity_months = Column(Integer, nullable=True)  # Null = unbegrenzt gültig

    # Relationships
    personnel_trainings = relationship("PersonnelTraining", back_populates="training")


class PersonnelTraining(Base):
    """Verknüpfung Personal zu Schulungen (Many-to-Many)"""
    __tablename__ = "personnel_trainings"

    id = Column(Integer, primary_key=True, index=True)
    personnel_id = Column(Integer, ForeignKey("personnel.id"), nullable=False)
    training_id = Column(Integer, ForeignKey("trainings.id"), nullable=False)
    completed_date = Column(Date, nullable=False)
    expires_date = Column(Date, nullable=True)
    certificate_number = Column(String(100), nullable=True)
    instructor = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships
    personnel = relationship("Personnel", back_populates="trainings")
    training = relationship("Training", back_populates="personnel_trainings")


# ===== Feature 9: Security Models =====

# Standard-Berechtigungen
DEFAULT_PERMISSIONS = {
    RoleName.ADMIN: [
        "personnel.view", "personnel.create", "personnel.edit", "personnel.delete",
        "sessions.view", "sessions.create", "sessions.end",
        "reports.view", "reports.export",
        "settings.edit",
        "announcements.view", "announcements.create", "announcements.edit", "announcements.delete",
        "groups.view", "groups.create", "groups.edit", "groups.delete",
        "trainings.view", "trainings.create", "trainings.edit", "trainings.delete",
        "audit.view",
        "backup.create", "backup.restore", "backup.delete",
        "roles.view", "roles.edit"
    ],
    RoleName.WEHRFUEHRER: [
        "personnel.view", "personnel.create", "personnel.edit", "personnel.delete",
        "sessions.view", "sessions.create", "sessions.end",
        "reports.view", "reports.export",
        "announcements.view", "announcements.create", "announcements.edit", "announcements.delete",
        "groups.view", "groups.create", "groups.edit",
        "trainings.view", "trainings.create", "trainings.edit",
        "audit.view"
    ],
    RoleName.GRUPPENFUEHRER: [
        "personnel.view", "personnel.edit",
        "sessions.view", "sessions.end",
        "reports.view",
        "announcements.view",
        "groups.view",
        "trainings.view"
    ],
    RoleName.MITGLIED: [
        "personnel.view_own",
        "sessions.view",
        "announcements.view"
    ]
}


class Role(Base):
    """Rollen für Berechtigungen"""
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(SQLEnum(RoleName), unique=True, nullable=False)
    permissions = Column(Text, nullable=False)  # JSON Array stored as text

    # Relationships
    personnel = relationship("Personnel", back_populates="role")
    admin_users = relationship("AdminUser", back_populates="role")


class AuditLog(Base):
    """Audit-Log für Änderungsverfolgung"""
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)
    user_name = Column(String(255), nullable=True)  # Für gelöschte User
    action = Column(SQLEnum(AuditAction), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(Integer, nullable=True)
    changes = Column(Text, nullable=True)  # JSON: alte und neue Werte
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
