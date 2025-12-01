#!/bin/bash

# =============================================================================
# Feuerwehr Anwesenheits-App - Setup Script für Raspberry Pi
# =============================================================================
# Dieses Script installiert alle erforderlichen Komponenten für die
# Feuerwehr Anwesenheitserfassungs-Anwendung auf einem Raspberry Pi.
# =============================================================================

set -e

# Farben für Ausgabe
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Konfiguration
APP_DIR="/opt/feuerwehr-anwesenheit"
APP_USER="feuerwehr"
SERVICE_NAME="feuerwehr-anwesenheit"
PYTHON_VERSION="3.9"

# Funktionen
print_header() {
    echo ""
    echo "============================================================"
    echo -e "${GREEN}$1${NC}"
    echo "============================================================"
}

print_info() {
    echo -e "${YELLOW}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

print_error() {
    echo -e "${RED}[FEHLER]${NC} $1"
    exit 1
}

# Prüfe ob Script als root ausgeführt wird
check_root() {
    if [ "$EUID" -ne 0 ]; then
        print_error "Bitte führen Sie dieses Script als root aus (sudo ./setup.sh)"
    fi
}

# System aktualisieren
update_system() {
    print_header "System aktualisieren"
    apt-get update
    apt-get upgrade -y
    print_success "System aktualisiert"
}

# Abhängigkeiten installieren
install_dependencies() {
    print_header "Abhängigkeiten installieren"
    
    apt-get install -y \
        python3 \
        python3-pip \
        python3-venv \
        nodejs \
        npm \
        git \
        chromium-browser \
        unclutter \
        xdotool \
        sqlite3
    
    print_success "Abhängigkeiten installiert"
}

# Benutzer erstellen
create_user() {
    print_header "Benutzer erstellen"
    
    if id "$APP_USER" &>/dev/null; then
        print_info "Benutzer $APP_USER existiert bereits"
    else
        useradd -r -s /bin/bash -m "$APP_USER"
        print_success "Benutzer $APP_USER erstellt"
    fi
}

# Anwendung installieren
install_application() {
    print_header "Anwendung installieren"
    
    # Verzeichnis erstellen
    mkdir -p "$APP_DIR"
    
    # Aktuelle Dateien kopieren (Script wird aus dem Repo ausgeführt)
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
    cp -r "$SCRIPT_DIR"/* "$APP_DIR/"
    
    # Backend vorbereiten
    print_info "Python Virtual Environment erstellen..."
    cd "$APP_DIR/backend"
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    deactivate
    
    # Frontend bauen
    print_info "Frontend bauen..."
    cd "$APP_DIR/frontend"
    npm install
    npm run build
    
    # Berechtigungen setzen
    chown -R "$APP_USER:$APP_USER" "$APP_DIR"
    
    print_success "Anwendung installiert"
}

# Konfigurationsdatei erstellen
create_config() {
    print_header "Konfiguration erstellen"
    
    if [ ! -f "$APP_DIR/config.json" ]; then
        cp "$APP_DIR/install/config.example.json" "$APP_DIR/config.json"
        print_info "Konfigurationsdatei erstellt: $APP_DIR/config.json"
        print_info "Bitte passen Sie die Konfiguration nach Bedarf an."
    else
        print_info "Konfigurationsdatei existiert bereits"
    fi
    
    chown "$APP_USER:$APP_USER" "$APP_DIR/config.json"
    print_success "Konfiguration erstellt"
}

# Systemd Service erstellen
create_service() {
    print_header "Systemd Service erstellen"
    
    cp "$APP_DIR/install/systemd/feuerwehr-anwesenheit.service" /etc/systemd/system/
    
    systemctl daemon-reload
    systemctl enable "$SERVICE_NAME"
    
    print_success "Systemd Service erstellt und aktiviert"
}

# Kiosk-Modus konfigurieren
configure_kiosk() {
    print_header "Kiosk-Modus konfigurieren"
    
    # Autostart für Chromium im Kiosk-Modus
    AUTOSTART_DIR="/home/$APP_USER/.config/autostart"
    mkdir -p "$AUTOSTART_DIR"
    
    cat > "$AUTOSTART_DIR/feuerwehr-kiosk.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Feuerwehr Anwesenheit
Exec=/bin/bash -c 'sleep 10 && chromium-browser --kiosk --disable-restore-session-state --noerrdialogs --disable-infobars --check-for-update-interval=604800 http://localhost:8000'
Hidden=false
X-GNOME-Autostart-enabled=true
EOF
    
    chown -R "$APP_USER:$APP_USER" "/home/$APP_USER/.config"
    
    # Unclutter für versteckten Mauszeiger
    cat > "$AUTOSTART_DIR/unclutter.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Unclutter
Exec=unclutter -idle 0.5 -root
Hidden=false
X-GNOME-Autostart-enabled=true
EOF
    
    print_success "Kiosk-Modus konfiguriert"
}

# Service starten
start_service() {
    print_header "Service starten"
    
    systemctl start "$SERVICE_NAME"
    
    # Kurz warten und Status prüfen
    sleep 3
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        print_success "Service läuft"
    else
        print_error "Service konnte nicht gestartet werden. Prüfen Sie: journalctl -u $SERVICE_NAME"
    fi
}

# Installation abschließen
finish_installation() {
    print_header "Installation abgeschlossen"
    
    echo ""
    echo "Die Feuerwehr Anwesenheits-App wurde erfolgreich installiert!"
    echo ""
    echo "Wichtige Informationen:"
    echo "  - Anwendung: http://localhost:8000"
    echo "  - Admin-Bereich: http://localhost:8000/admin"
    echo "  - Standard-Login: admin / feuerwehr2025"
    echo ""
    echo "  - Konfiguration: $APP_DIR/config.json"
    echo "  - Logs: journalctl -u $SERVICE_NAME"
    echo ""
    echo "Service-Befehle:"
    echo "  - Status:    sudo systemctl status $SERVICE_NAME"
    echo "  - Neustart:  sudo systemctl restart $SERVICE_NAME"
    echo "  - Stoppen:   sudo systemctl stop $SERVICE_NAME"
    echo ""
    echo -e "${YELLOW}WICHTIG: Bitte ändern Sie das Admin-Passwort nach dem ersten Login!${NC}"
    echo ""
}

# Hauptprogramm
main() {
    print_header "Feuerwehr Anwesenheits-App - Installation"
    
    check_root
    update_system
    install_dependencies
    create_user
    install_application
    create_config
    create_service
    configure_kiosk
    start_service
    finish_installation
}

# Script starten
main
