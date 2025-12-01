"""
Datenbank-Konfiguration und Verbindung für die Feuerwehr Anwesenheits-App
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base, Personnel, AdminUser, DIENSTGRADE
from passlib.context import CryptContext

# Datenbank-Pfad (kann über Umgebungsvariable überschrieben werden)
DATABASE_PATH = os.getenv("DATABASE_PATH", "feuerwehr_anwesenheit.db")
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# SQLAlchemy Engine und Session erstellen
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # Für SQLite erforderlich
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Password Hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def init_db():
    """Initialisiert die Datenbank und erstellt alle Tabellen"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency für FastAPI - gibt eine Datenbank-Session zurück"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_demo_data():
    """Erstellt Demo-Daten für Testing"""
    db = SessionLocal()
    try:
        # Prüfe ob bereits Daten vorhanden sind
        if db.query(Personnel).count() > 0:
            print("Demo-Daten bereits vorhanden - überspringe")
            return

        # Demo-Mitarbeiter erstellen (mit korrekter Dienstgrade-Hierarchie)
        demo_personnel = [
            {"stammrollennummer": "001", "vorname": "Max", "nachname": "Mustermann", "dienstgrad": "FM"},
            {"stammrollennummer": "002", "vorname": "Anna", "nachname": "Schmidt", "dienstgrad": "OFM"},
            {"stammrollennummer": "003", "vorname": "Thomas", "nachname": "Müller", "dienstgrad": "HFM"},
            {"stammrollennummer": "004", "vorname": "Lisa", "nachname": "Weber", "dienstgrad": "UBM"},
            {"stammrollennummer": "005", "vorname": "Michael", "nachname": "Fischer", "dienstgrad": "BM"},
            {"stammrollennummer": "006", "vorname": "Sarah", "nachname": "Wagner", "dienstgrad": "OBM"},
            {"stammrollennummer": "007", "vorname": "Peter", "nachname": "Becker", "dienstgrad": "HBM"},
            {"stammrollennummer": "008", "vorname": "Julia", "nachname": "Hoffmann", "dienstgrad": "BI"},
            {"stammrollennummer": "009", "vorname": "Stefan", "nachname": "Schneider", "dienstgrad": "UBM"},
            {"stammrollennummer": "010", "vorname": "Markus", "nachname": "Koch", "dienstgrad": "BI"},
        ]

        for person_data in demo_personnel:
            person = Personnel(**person_data)
            db.add(person)

        # Admin-Benutzer erstellen
        admin_user = db.query(AdminUser).filter(AdminUser.username == "admin").first()
        if not admin_user:
            admin_user = AdminUser(
                username="admin",
                password_hash=pwd_context.hash("feuerwehr2025")
            )
            db.add(admin_user)

        db.commit()
        print(f"Demo-Daten erstellt: {len(demo_personnel)} Mitarbeiter und 1 Admin-Benutzer")

    except Exception as e:
        db.rollback()
        print(f"Fehler beim Erstellen der Demo-Daten: {e}")
    finally:
        db.close()


def get_dienstgrade_list():
    """Gibt eine Liste aller Dienstgrade zurück"""
    return [
        {"kuerzel": k, "name": v[0], "level": v[1]}
        for k, v in DIENSTGRADE.items()
    ]
