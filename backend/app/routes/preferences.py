"""
Preferences API Routes für die Feuerwehr Anwesenheits-App
Feature 12: Personalisierung
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import UserPreferences, AdminUser, ThemeType, FontSize
from ..utils.auth import get_current_user

router = APIRouter(prefix="/api/preferences", tags=["Preferences"])


# Pydantic Modelle
class PreferencesResponse(BaseModel):
    id: int
    user_id: int
    theme: str
    font_size: str
    high_contrast: bool
    language: str


class PreferencesUpdate(BaseModel):
    theme: Optional[str] = None
    font_size: Optional[str] = None
    high_contrast: Optional[bool] = None
    language: Optional[str] = None


class ThemeResponse(BaseModel):
    value: str
    label: str
    description: str


# Routen
@router.get("/", response_model=PreferencesResponse)
def get_preferences(
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user)
):
    """Gibt die Einstellungen des aktuellen Benutzers zurück"""
    prefs = db.query(UserPreferences).filter(
        UserPreferences.user_id == current_user.id
    ).first()
    
    # Erstelle Standard-Einstellungen falls nicht vorhanden
    if not prefs:
        prefs = UserPreferences(
            user_id=current_user.id,
            theme=ThemeType.AUTO,
            font_size=FontSize.NORMAL,
            high_contrast=False,
            language="de"
        )
        db.add(prefs)
        db.commit()
        db.refresh(prefs)
    
    return PreferencesResponse(
        id=prefs.id,
        user_id=prefs.user_id,
        theme=prefs.theme.value,
        font_size=prefs.font_size.value,
        high_contrast=prefs.high_contrast,
        language=prefs.language
    )


@router.put("/", response_model=PreferencesResponse)
def update_preferences(
    prefs_data: PreferencesUpdate,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user)
):
    """Aktualisiert die Einstellungen des aktuellen Benutzers"""
    prefs = db.query(UserPreferences).filter(
        UserPreferences.user_id == current_user.id
    ).first()
    
    # Erstelle Standard-Einstellungen falls nicht vorhanden
    if not prefs:
        prefs = UserPreferences(
            user_id=current_user.id,
            theme=ThemeType.AUTO,
            font_size=FontSize.NORMAL,
            high_contrast=False,
            language="de"
        )
        db.add(prefs)
        db.commit()
        db.refresh(prefs)
    
    # Aktualisiere die Felder
    if prefs_data.theme is not None:
        try:
            prefs.theme = ThemeType(prefs_data.theme)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ungültiger Theme-Wert: {prefs_data.theme}"
            )
    
    if prefs_data.font_size is not None:
        try:
            prefs.font_size = FontSize(prefs_data.font_size)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ungültiger Schriftgrößen-Wert: {prefs_data.font_size}"
            )
    
    if prefs_data.high_contrast is not None:
        prefs.high_contrast = prefs_data.high_contrast
    
    if prefs_data.language is not None:
        if prefs_data.language not in ["de", "en"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ungültige Sprache: {prefs_data.language}"
            )
        prefs.language = prefs_data.language
    
    db.commit()
    db.refresh(prefs)
    
    return PreferencesResponse(
        id=prefs.id,
        user_id=prefs.user_id,
        theme=prefs.theme.value,
        font_size=prefs.font_size.value,
        high_contrast=prefs.high_contrast,
        language=prefs.language
    )


@router.get("/themes")
def get_available_themes():
    """Gibt alle verfügbaren Themes zurück"""
    return [
        {
            "value": "light",
            "label": "Hell",
            "description": "Heller Modus für den Tag"
        },
        {
            "value": "dark",
            "label": "Dunkel",
            "description": "Dunkler Modus für weniger Augenbelastung"
        },
        {
            "value": "auto",
            "label": "Automatisch",
            "description": "Folgt den System-Einstellungen"
        }
    ]


@router.get("/font-sizes")
def get_available_font_sizes():
    """Gibt alle verfügbaren Schriftgrößen zurück"""
    return [
        {
            "value": "normal",
            "label": "Normal",
            "description": "Standard-Schriftgröße"
        },
        {
            "value": "large",
            "label": "Groß",
            "description": "Größere Schrift für bessere Lesbarkeit"
        },
        {
            "value": "extra_large",
            "label": "Sehr Groß",
            "description": "Extra große Schrift für Kiosk-Modus"
        }
    ]


@router.get("/languages")
def get_available_languages():
    """Gibt alle verfügbaren Sprachen zurück"""
    return [
        {
            "value": "de",
            "label": "Deutsch",
            "flag": "🇩🇪"
        },
        {
            "value": "en",
            "label": "English",
            "flag": "🇬🇧"
        }
    ]
