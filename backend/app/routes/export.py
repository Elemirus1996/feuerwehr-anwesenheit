"""
Export API Routes für die Feuerwehr Anwesenheits-App
PDF-Export für Sessions und Berichte
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.pdf_generator import PDFGenerator
from ..utils.auth import get_current_user

router = APIRouter(prefix="/api/export", tags=["Export"])


# Pydantic Modelle
class PeriodExportRequest(BaseModel):
    start_date: str
    end_date: str
    event_type: Optional[str] = None


# Routen
@router.get("/session/{session_id}/pdf")
def export_session_pdf(
    session_id: int,
    db: Session = Depends(get_db),
    _: any = Depends(get_current_user)
):
    """Exportiert eine einzelne Session als PDF"""
    try:
        pdf_bytes = PDFGenerator.generate_session_pdf(db, session_id)
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=anwesenheit_session_{session_id}.pdf"
            }
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Erstellen des PDFs: {str(e)}"
        )


@router.post("/period/pdf")
def export_period_pdf(
    request: PeriodExportRequest,
    db: Session = Depends(get_db),
    _: any = Depends(get_current_user)
):
    """Exportiert einen Zeitraum-Bericht als PDF"""
    try:
        start_date = datetime.fromisoformat(request.start_date)
        end_date = datetime.fromisoformat(request.end_date)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ungültiges Datumsformat. Bitte ISO-Format verwenden (YYYY-MM-DD)"
        )
    
    if start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Startdatum muss vor dem Enddatum liegen"
        )
    
    try:
        pdf_bytes = PDFGenerator.generate_period_report(
            db,
            start_date,
            end_date,
            request.event_type
        )
        
        filename = f"anwesenheit_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.pdf"
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Erstellen des PDFs: {str(e)}"
        )
