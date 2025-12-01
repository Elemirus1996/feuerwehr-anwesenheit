"""
PDF-Generator Service für die Feuerwehr Anwesenheits-App
Erstellt professionelle PDF-Dokumente für Anwesenheitslisten
"""

import os
import io
from datetime import datetime
from typing import List, Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from sqlalchemy.orm import Session

from ..models import Session as SessionModel, Attendance, Personnel, FireStation

# Upload-Verzeichnis für Logo
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads", "logo")


class PDFGenerator:
    """Generiert PDF-Dokumente für Anwesenheitslisten"""

    @staticmethod
    def _get_styles():
        """Erstellt die Styles für das PDF"""
        styles = getSampleStyleSheet()
        
        styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=12,
            alignment=TA_CENTER,
            textColor=colors.darkred
        ))
        
        styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=styles['Normal'],
            fontSize=14,
            spaceAfter=6,
            alignment=TA_CENTER,
            textColor=colors.darkgray
        ))
        
        styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=styles['Heading2'],
            fontSize=12,
            spaceBefore=12,
            spaceAfter=6,
            textColor=colors.black
        ))
        
        styles.add(ParagraphStyle(
            name='CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=4
        ))
        
        styles.add(ParagraphStyle(
            name='Footer',
            parent=styles['Normal'],
            fontSize=8,
            alignment=TA_CENTER,
            textColor=colors.gray
        ))
        
        return styles

    @staticmethod
    def _format_datetime(dt: datetime) -> str:
        """Formatiert ein Datum für die Anzeige"""
        if dt is None:
            return "-"
        return dt.strftime("%d.%m.%Y %H:%M")

    @staticmethod
    def _format_date(dt: datetime) -> str:
        """Formatiert ein Datum (ohne Zeit)"""
        if dt is None:
            return "-"
        return dt.strftime("%d.%m.%Y")

    @staticmethod
    def _format_time(dt: datetime) -> str:
        """Formatiert eine Zeit"""
        if dt is None:
            return "-"
        return dt.strftime("%H:%M")

    @staticmethod
    def _calculate_duration(start: datetime, end: Optional[datetime]) -> str:
        """Berechnet die Dauer zwischen zwei Zeitpunkten"""
        if end is None:
            return "Noch anwesend"
        delta = end - start
        hours = int(delta.total_seconds() // 3600)
        minutes = int((delta.total_seconds() % 3600) // 60)
        return f"{hours}h {minutes}min"

    @staticmethod
    def _get_fire_station_info(db: Session) -> tuple:
        """Holt Feuerwehr-Daten für PDF"""
        fire_station = db.query(FireStation).first()
        if fire_station:
            name = fire_station.name
            address = ""
            if fire_station.street:
                address = f"{fire_station.street}, "
            address += f"{fire_station.postal_code} {fire_station.city}"
            
            logo_path = None
            if fire_station.logo_path:
                full_logo_path = os.path.join(UPLOAD_DIR, fire_station.logo_path)
                if os.path.exists(full_logo_path):
                    logo_path = full_logo_path
            
            return name, address, logo_path
        return "Freiwillige Feuerwehr", "", None

    @staticmethod
    def generate_session_pdf(db: Session, session_id: int) -> bytes:
        """Generiert ein PDF für eine einzelne Session"""
        # Session laden
        session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not session:
            raise ValueError("Session nicht gefunden")

        # Feuerwehr-Daten laden
        fire_station_name, fire_station_address, logo_path = PDFGenerator._get_fire_station_info(db)

        # Attendance-Daten laden
        attendances = db.query(Attendance).filter(
            Attendance.session_id == session_id
        ).order_by(Attendance.check_in_time).all()

        # PDF-Buffer erstellen
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )

        styles = PDFGenerator._get_styles()
        elements = []

        # Header mit Logo (falls vorhanden)
        if logo_path:
            try:
                logo = Image(logo_path, width=3*cm, height=3*cm)
                logo.hAlign = 'CENTER'
                elements.append(logo)
                elements.append(Spacer(1, 0.3*cm))
            except Exception:
                pass  # Falls Logo nicht geladen werden kann, ohne Logo fortfahren

        # Header Text
        elements.append(Paragraph(fire_station_name, styles['CustomTitle']))
        if fire_station_address:
            elements.append(Paragraph(fire_station_address, styles['CustomNormal']))
        elements.append(Paragraph("Anwesenheitsliste", styles['CustomSubtitle']))
        elements.append(Spacer(1, 0.5*cm))

        # Session-Details
        elements.append(Paragraph("Veranstaltungsdetails", styles['CustomHeading']))
        
        session_info = [
            ["Event-Typ:", session.get_event_type_display()],
            ["Datum:", PDFGenerator._format_date(session.start_time)],
            ["Startzeit:", PDFGenerator._format_time(session.start_time)],
            ["Endzeit:", PDFGenerator._format_time(session.end_time) if session.end_time else "Noch aktiv"],
            ["Gesamtdauer:", PDFGenerator._calculate_duration(session.start_time, session.end_time)],
            ["Status:", "Abgeschlossen" if session.status.value == "completed" else "Aktiv"],
        ]
        
        if session.ended_by_stammrollennummer:
            ended_by = db.query(Personnel).filter(
                Personnel.stammrollennummer == session.ended_by_stammrollennummer
            ).first()
            if ended_by:
                session_info.append([
                    "Beendet von:",
                    f"{ended_by.dienstgrad} {ended_by.vorname} {ended_by.nachname}"
                ])

        info_table = Table(session_info, colWidths=[4*cm, 10*cm])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 0.5*cm))

        # Teilnehmerliste
        elements.append(Paragraph(f"Teilnehmerliste ({len(attendances)} Personen)", styles['CustomHeading']))

        if attendances:
            # Tabellen-Header
            table_data = [["Nr.", "Stammr.", "Dienstgrad", "Name", "Check-in", "Check-out", "Dauer"]]

            for i, att in enumerate(attendances, 1):
                person = att.person
                name = f"{person.vorname} {person.nachname}" if person else "Unbekannt"
                dienstgrad = person.dienstgrad if person else "-"
                
                table_data.append([
                    str(i),
                    att.stammrollennummer,
                    dienstgrad,
                    name,
                    PDFGenerator._format_time(att.check_in_time),
                    PDFGenerator._format_time(att.check_out_time) if att.check_out_time else "-",
                    PDFGenerator._calculate_duration(att.check_in_time, att.check_out_time)
                ])

            # Tabelle erstellen
            attendee_table = Table(
                table_data,
                colWidths=[1*cm, 2*cm, 2*cm, 5*cm, 1.8*cm, 1.8*cm, 2.4*cm]
            )
            attendee_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (3, 0), (3, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.Color(0.95, 0.95, 0.95)]),
            ]))
            elements.append(attendee_table)
        else:
            elements.append(Paragraph("Keine Teilnehmer registriert.", styles['CustomNormal']))

        elements.append(Spacer(1, 1*cm))

        # Unterschriftenfeld
        elements.append(Paragraph("Unterschrift Veranstaltungsleiter:", styles['CustomHeading']))
        elements.append(Spacer(1, 1.5*cm))
        
        signature_line = Table(
            [["_" * 40, "", "_" * 30]],
            colWidths=[6*cm, 2*cm, 5*cm]
        )
        signature_line.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        elements.append(signature_line)
        
        signature_labels = Table(
            [["Unterschrift", "", "Datum"]],
            colWidths=[6*cm, 2*cm, 5*cm]
        )
        signature_labels.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.gray),
        ]))
        elements.append(signature_labels)

        elements.append(Spacer(1, 1*cm))

        # Footer
        elements.append(Paragraph(
            f"Erstellt am {datetime.now().strftime('%d.%m.%Y um %H:%M Uhr')} | {fire_station_name}",
            styles['Footer']
        ))

        # PDF generieren
        doc.build(elements)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    @staticmethod
    def generate_period_report(
        db: Session,
        start_date: datetime,
        end_date: datetime,
        event_type: Optional[str] = None
    ) -> bytes:
        """Generiert einen PDF-Bericht für einen Zeitraum"""
        # Feuerwehr-Daten laden
        fire_station_name, fire_station_address, logo_path = PDFGenerator._get_fire_station_info(db)

        # Sessions im Zeitraum finden
        query = db.query(SessionModel).filter(
            SessionModel.start_time >= start_date,
            SessionModel.start_time <= end_date
        )
        
        if event_type:
            query = query.filter(SessionModel.event_type == event_type)
        
        sessions = query.order_by(SessionModel.start_time).all()

        # PDF-Buffer erstellen
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )

        styles = PDFGenerator._get_styles()
        elements = []

        # Header mit Logo (falls vorhanden)
        if logo_path:
            try:
                logo = Image(logo_path, width=3*cm, height=3*cm)
                logo.hAlign = 'CENTER'
                elements.append(logo)
                elements.append(Spacer(1, 0.3*cm))
            except Exception:
                pass  # Falls Logo nicht geladen werden kann, ohne Logo fortfahren

        # Header Text
        elements.append(Paragraph(fire_station_name, styles['CustomTitle']))
        if fire_station_address:
            elements.append(Paragraph(fire_station_address, styles['CustomNormal']))
        elements.append(Paragraph("Anwesenheitsbericht", styles['CustomSubtitle']))
        elements.append(Spacer(1, 0.5*cm))

        # Zeitraum-Info
        period_info = f"Zeitraum: {start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}"
        if event_type:
            period_info += f" | Typ: {event_type}"
        elements.append(Paragraph(period_info, styles['CustomNormal']))
        elements.append(Paragraph(f"Anzahl Veranstaltungen: {len(sessions)}", styles['CustomNormal']))
        elements.append(Spacer(1, 0.5*cm))

        # Sessions-Übersicht
        if sessions:
            table_data = [["Datum", "Event-Typ", "Start", "Ende", "Dauer", "Teilnehmer"]]

            for session in sessions:
                attendee_count = db.query(Attendance).filter(
                    Attendance.session_id == session.id
                ).count()
                
                table_data.append([
                    PDFGenerator._format_date(session.start_time),
                    session.get_event_type_display(),
                    PDFGenerator._format_time(session.start_time),
                    PDFGenerator._format_time(session.end_time) if session.end_time else "-",
                    PDFGenerator._calculate_duration(session.start_time, session.end_time),
                    str(attendee_count)
                ])

            session_table = Table(
                table_data,
                colWidths=[2.5*cm, 4*cm, 2*cm, 2*cm, 2.5*cm, 2.5*cm]
            )
            session_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.Color(0.95, 0.95, 0.95)]),
            ]))
            elements.append(session_table)
        else:
            elements.append(Paragraph("Keine Veranstaltungen im angegebenen Zeitraum.", styles['CustomNormal']))

        elements.append(Spacer(1, 1*cm))

        # Footer
        elements.append(Paragraph(
            f"Erstellt am {datetime.now().strftime('%d.%m.%Y um %H:%M Uhr')} | {fire_station_name}",
            styles['Footer']
        ))

        # PDF generieren
        doc.build(elements)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes
