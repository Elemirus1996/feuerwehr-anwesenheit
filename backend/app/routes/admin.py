"""
Admin API Routes für die Feuerwehr Anwesenheits-App
"""

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import AdminUser
from ..utils.auth import (
    authenticate_user,
    create_access_token,
    get_current_user,
    get_password_hash,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

router = APIRouter(prefix="/api/admin", tags=["Admin"])


# Pydantic Modelle
class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str


class UserInfo(BaseModel):
    id: int
    username: str


# Routen
@router.post("/login", response_model=TokenResponse)
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """Admin-Login"""
    user = authenticate_user(db, login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ungültiger Benutzername oder Passwort",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.get("/me", response_model=UserInfo)
def get_current_user_info(current_user: AdminUser = Depends(get_current_user)):
    """Gibt Informationen zum aktuell eingeloggten Benutzer zurück"""
    return UserInfo(
        id=current_user.id,
        username=current_user.username
    )


@router.post("/change-password")
def change_password(
    password_data: PasswordChangeRequest,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user)
):
    """Ändert das Passwort des aktuellen Benutzers"""
    from ..utils.auth import verify_password
    
    if not verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Aktuelles Passwort ist falsch"
        )
    
    if len(password_data.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Neues Passwort muss mindestens 8 Zeichen lang sein"
        )
    
    current_user.password_hash = get_password_hash(password_data.new_password)
    db.commit()
    
    return {"message": "Passwort erfolgreich geändert"}


@router.post("/logout")
def logout(current_user: AdminUser = Depends(get_current_user)):
    """Logout (Token-Invalidierung erfolgt client-seitig)"""
    return {"message": "Erfolgreich abgemeldet"}


@router.get("/stats")
def get_stats(
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_user)
):
    """Gibt Statistiken für das Admin-Dashboard zurück"""
    from ..models import Session as SessionModel, Personnel, Attendance, SessionStatus
    from datetime import datetime, timedelta
    
    # Zähle aktive Sessions
    active_sessions = db.query(SessionModel).filter(
        SessionModel.status == SessionStatus.ACTIVE
    ).count()
    
    # Zähle alle Mitarbeiter
    total_personnel = db.query(Personnel).count()
    active_personnel = db.query(Personnel).filter(Personnel.aktiv == True).count()
    
    # Sessions der letzten 30 Tage
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_sessions = db.query(SessionModel).filter(
        SessionModel.created_at >= thirty_days_ago
    ).count()
    
    # Aktuelle Anwesende (falls aktive Session)
    current_attendees = 0
    current_session = db.query(SessionModel).filter(
        SessionModel.status == SessionStatus.ACTIVE
    ).first()
    if current_session:
        current_attendees = db.query(Attendance).filter(
            Attendance.session_id == current_session.id,
            Attendance.check_out_time == None
        ).count()
    
    return {
        "active_sessions": active_sessions,
        "total_personnel": total_personnel,
        "active_personnel": active_personnel,
        "recent_sessions_30d": recent_sessions,
        "current_attendees": current_attendees
    }
