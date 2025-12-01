# 🚒 Feuerwehr Anwesenheits-App

Eine digitale Anwesenheitserfassungs-Anwendung für Feuerwachen, optimiert für den Betrieb auf einem Raspberry Pi mit Touchscreen.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.9+-green)
![React](https://img.shields.io/badge/react-18.2-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## 📋 Übersicht

Diese Anwendung ermöglicht die einfache Erfassung der Anwesenheit bei:
- **Einsätzen** (manuelle Beendigung durch UBM oder höher erforderlich)
- **Übungsdiensten** (automatisches Ende nach 3 Stunden)
- **Arbeitsdiensten Tour A/B/C** (automatisches Ende nach 3 Stunden)

### Features

✅ **Touchscreen-optimiertes Interface** mit großen Buttons und Numpad  
✅ **Check-in/Check-out** per Stammrollennummer  
✅ **Automatische Session-Timeouts** für Übungs- und Arbeitsdienste  
✅ **Web-basierter Admin-Bereich** für Personalverwaltung  
✅ **PDF-Export** für Anwesenheitslisten und Zeitraum-Berichte  
✅ **Kiosk-Modus** für unbeaufsichtigten Betrieb  
✅ **Lokaler Betrieb** ohne Internet-Verbindung  

## 🖥️ Systemanforderungen

### Hardware
- Raspberry Pi 3, 4 oder 5 (empfohlen: Pi 4 mit 4GB RAM)
- Touchscreen (7" oder größer empfohlen)
- SD-Karte (mindestens 16GB)
- Stromversorgung

### Software
- Raspberry Pi OS (64-bit empfohlen)
- Python 3.9 oder höher
- Node.js 18 oder höher
- Chromium Browser (für Kiosk-Modus)

## 🚀 Installation

### Schnellinstallation (Raspberry Pi)

```bash
# Repository klonen
git clone https://github.com/your-repo/feuerwehr-anwesenheit.git
cd feuerwehr-anwesenheit

# Setup-Script ausführen
sudo chmod +x install/setup.sh
sudo ./install/setup.sh
```

Das Setup-Script führt automatisch folgende Schritte aus:
1. System-Updates installieren
2. Abhängigkeiten installieren (Python, Node.js, etc.)
3. Anwendung konfigurieren
4. Systemd-Service einrichten
5. Kiosk-Modus konfigurieren

### Manuelle Installation

#### 1. Backend einrichten

```bash
cd backend

# Virtual Environment erstellen
python3 -m venv venv
source venv/bin/activate

# Dependencies installieren
pip install -r requirements.txt

# Backend starten (Entwicklung)
python main.py
```

#### 2. Frontend einrichten

```bash
cd frontend

# Dependencies installieren
npm install

# Entwicklungsserver starten
npm run dev

# Für Produktion bauen
npm run build
```

### Docker Installation

```bash
# Mit Docker Compose starten
docker-compose up -d

# Logs anzeigen
docker-compose logs -f
```

## ⚙️ Konfiguration

### Umgebungsvariablen

| Variable | Beschreibung | Standard |
|----------|--------------|----------|
| `HOST` | Server-Adresse | `0.0.0.0` |
| `PORT` | Server-Port | `8000` |
| `DATABASE_PATH` | Pfad zur SQLite-DB | `feuerwehr_anwesenheit.db` |
| `SECRET_KEY` | JWT-Geheimnis | Generiert |
| `TOKEN_EXPIRE_MINUTES` | Token-Gültigkeit | `480` (8h) |
| `FEUERWACHE_NAME` | Name für PDFs | `Freiwillige Feuerwehr Musterstadt` |
| `AUTO_TIMEOUT_HOURS` | Session-Timeout | `3` |
| `SESSION_CHECK_INTERVAL` | Prüf-Intervall (Sek.) | `60` |
| `CREATE_DEMO_DATA` | Demo-Daten erstellen | `true` |

### Konfigurationsdatei

Eine Beispiel-Konfigurationsdatei finden Sie unter `install/config.example.json`.

## 📖 Verwendung

### Kiosk-Modus (Check-in Interface)

Nach dem Start ist die Anwendung unter `http://localhost:8000` erreichbar.

1. **Session starten**: Event-Typ auswählen (Einsatz, Übungsdienst, etc.)
2. **Check-in**: Stammrollennummer über Numpad eingeben
3. **Check-out**: Erneut Stammrollennummer eingeben
4. **Session beenden**: Bei Einsätzen nur durch UBM oder höheren Rang möglich

### Admin-Bereich

Erreichbar unter `http://localhost:8000/admin`

**Standard-Anmeldedaten:**
- Benutzername: `admin`
- Passwort: `feuerwehr2025`

> ⚠️ **Wichtig:** Ändern Sie das Passwort nach dem ersten Login!

#### Funktionen:
- **Dashboard**: Übersicht über aktive Sessions und Statistiken
- **Personal**: Mitarbeiter anlegen, bearbeiten und verwalten
- **Sessions**: Anwesenheitslisten einsehen und als PDF exportieren

### Dienstgrade

Folgende Dienstgrade sind verfügbar (aufsteigend nach Rang):

| Kürzel | Bezeichnung |
|--------|-------------|
| FM | Feuerwehrmann |
| OFM | Oberfeuerwehrmann |
| HFM | Hauptfeuerwehrmann |
| LM | Löschmeister |
| OLM | Oberlöschmeister |
| HLM | Hauptlöschmeister |
| BM | Brandmeister |
| OBM | Oberbrandmeister |
| HBM | Hauptbrandmeister |
| **UBM** | **Unterbrandmeister** (min. Rang für Einsatz-Ende) |
| BI | Brandinspektor |
| OBI | Oberbrandinspektor |
| HBI | Hauptbrandinspektor |
| BR | Brandrat |
| OBR | Oberbrandrat |
| BD | Branddirektor |

## 🔧 Service-Verwaltung

```bash
# Status prüfen
sudo systemctl status feuerwehr-anwesenheit

# Neu starten
sudo systemctl restart feuerwehr-anwesenheit

# Stoppen
sudo systemctl stop feuerwehr-anwesenheit

# Logs anzeigen
journalctl -u feuerwehr-anwesenheit -f
```

## 💾 Backup

### Datenbank-Backup

```bash
# Backup erstellen
cp /opt/feuerwehr-anwesenheit/data/feuerwehr_anwesenheit.db /backup/feuerwehr_$(date +%Y%m%d).db

# Automatisches Backup (Crontab)
0 2 * * * cp /opt/feuerwehr-anwesenheit/data/feuerwehr_anwesenheit.db /backup/feuerwehr_$(date +\%Y\%m\%d).db
```

### Backup wiederherstellen

```bash
sudo systemctl stop feuerwehr-anwesenheit
cp /backup/feuerwehr_YYYYMMDD.db /opt/feuerwehr-anwesenheit/data/feuerwehr_anwesenheit.db
sudo chown feuerwehr:feuerwehr /opt/feuerwehr-anwesenheit/data/feuerwehr_anwesenheit.db
sudo systemctl start feuerwehr-anwesenheit
```

## ❓ Troubleshooting

### Anwendung startet nicht

```bash
# Logs prüfen
journalctl -u feuerwehr-anwesenheit -n 50

# Konfiguration prüfen
cat /opt/feuerwehr-anwesenheit/config.json

# Berechtigungen prüfen
ls -la /opt/feuerwehr-anwesenheit/data/
```

### Datenbank-Fehler

```bash
# Datenbank-Integrität prüfen
sqlite3 /opt/feuerwehr-anwesenheit/data/feuerwehr_anwesenheit.db "PRAGMA integrity_check;"
```

### Port bereits belegt

```bash
# Prozess auf Port 8000 finden
sudo lsof -i :8000

# Anderen Port in der Konfiguration verwenden
```

### Kiosk-Modus Probleme

```bash
# Autostart-Konfiguration prüfen
cat /home/feuerwehr/.config/autostart/feuerwehr-kiosk.desktop

# Manuell testen
chromium-browser --kiosk http://localhost:8000
```

## 🏗️ Projektstruktur

```
feuerwehr-anwesenheit/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── models.py          # Datenbank-Modelle
│   │   ├── database.py        # DB-Konfiguration
│   │   ├── routes/            # API-Routen
│   │   │   ├── personnel.py
│   │   │   ├── sessions.py
│   │   │   ├── attendance.py
│   │   │   ├── admin.py
│   │   │   └── export.py
│   │   ├── services/          # Business-Logik
│   │   │   ├── session_manager.py
│   │   │   └── pdf_generator.py
│   │   └── utils/
│   │       └── auth.py        # Authentifizierung
│   ├── requirements.txt
│   └── main.py                # Einstiegspunkt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── CheckIn/       # Kiosk-Interface
│   │   │   └── Admin/         # Admin-Dashboard
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
├── install/
│   ├── setup.sh               # Installations-Script
│   ├── systemd/
│   │   └── feuerwehr-anwesenheit.service
│   └── config.example.json
├── docker-compose.yml
├── Dockerfile
├── README.md
└── .gitignore
```

## 🔒 Sicherheit

- Alle Passwörter werden mit bcrypt gehasht
- JWT-Token für Admin-Authentifizierung
- Lokaler Betrieb ohne Internet-Verbindung
- Kein Cloud-Upload von Daten

**Empfehlungen:**
- Ändern Sie das Standard-Admin-Passwort
- Verwenden Sie einen sicheren SECRET_KEY in der Produktion
- Regelmäßige Backups der Datenbank

## 📄 Lizenz

MIT License - siehe [LICENSE](LICENSE)

## 🤝 Beitragen

Beiträge sind willkommen! Bitte erstellen Sie einen Pull Request oder öffnen Sie ein Issue.

## 📞 Support

Bei Fragen oder Problemen erstellen Sie bitte ein Issue im Repository.