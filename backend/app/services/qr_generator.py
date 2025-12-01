"""
QR-Code Generator Service für die Feuerwehr Anwesenheits-App
Generiert QR-Codes für Session-Check-ins
"""

import io
import os
from datetime import datetime, timedelta
from typing import Optional
import qrcode
from qrcode.constants import ERROR_CORRECT_L
from jose import jwt

from ..utils.auth import SECRET_KEY, ALGORITHM


# QR-Code URL-Basis (kann über Umgebungsvariable überschrieben werden)
QR_BASE_URL = os.getenv("QR_BASE_URL", "http://localhost:5173")


class QRGenerator:
    """Generiert und validiert QR-Codes für Sessions"""

    @staticmethod
    def generate_session_token(session_id: int, session_end_time: Optional[datetime] = None) -> str:
        """
        Generiert einen JWT-Token für eine Session
        Token enthält Session-ID und läuft mit Session ab
        """
        # Token-Ablauf: entweder Session-Ende oder 24 Stunden
        if session_end_time:
            expire = session_end_time
        else:
            expire = datetime.utcnow() + timedelta(hours=24)
        
        payload = {
            "session_id": session_id,
            "type": "qr_checkin",
            "exp": expire
        }
        
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        return token

    @staticmethod
    def validate_session_token(token: str) -> Optional[int]:
        """
        Validiert einen Session-Token und gibt die Session-ID zurück
        Gibt None zurück wenn Token ungültig oder abgelaufen
        """
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            if payload.get("type") != "qr_checkin":
                return None
            return payload.get("session_id")
        except Exception:
            return None

    @staticmethod
    def generate_qr_code_image(session_id: int, token: str) -> bytes:
        """
        Generiert ein QR-Code-Bild als PNG-Bytes
        QR-Code enthält URL zum Check-in
        """
        # URL für QR-Code erstellen
        checkin_url = f"{QR_BASE_URL}/checkin?session={session_id}&token={token}"
        
        # QR-Code erstellen
        qr = qrcode.QRCode(
            version=1,
            error_correction=ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(checkin_url)
        qr.make(fit=True)
        
        # Bild erstellen
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Als Bytes zurückgeben
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()

    @staticmethod
    def generate_session_qr(session_id: int, session_end_time: Optional[datetime] = None) -> tuple:
        """
        Generiert Token und QR-Code-Bild für eine Session
        Gibt (token, png_bytes) zurück
        """
        token = QRGenerator.generate_session_token(session_id, session_end_time)
        png_bytes = QRGenerator.generate_qr_code_image(session_id, token)
        return token, png_bytes
