# Ubuntu Server Deployment Guide

## Voraussetzungen

Der Bot ist **bereits Ubuntu-Server-kompatibel** und sollte ohne Probleme laufen. Hier sind die wichtigsten Punkte:

### ✅ Bereits konfiguriert:

1. **Headless-Mode**: Standard ist `headless=True` (perfekt für Server ohne Display)
2. **Browser-Args**: Enthalten bereits Ubuntu-kompatible Flags:
   - `--no-sandbox` (wichtig für Docker/Container)
   - `--disable-setuid-sandbox` (wichtig für Ubuntu)
   - `--disable-dev-shm-usage` (verhindert Shared Memory Probleme)
3. **Dockerfile**: Bereits mit allen notwendigen System-Dependencies

## Option 1: Direkte Installation auf Ubuntu

### 1. System-Dependencies installieren

```bash
sudo apt-get update
sudo apt-get install -y \
    python3.10 \
    python3-pip \
    python3-venv \
    wget \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libwayland-client0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils
```

### 2. Projekt klonen und Setup

```bash
git clone <your-repo-url>
cd ebayScraper

# Virtuelle Umgebung erstellen
python3 -m venv venv
source venv/bin/activate

# Dependencies installieren
pip install -r requirements.txt

# Playwright Browser installieren
python3 -m playwright install chromium
python3 -m playwright install-deps chromium
```

### 3. Bot ausführen

```bash
# Im Headless-Mode (Standard für Server)
python cli.py \
    --url "https://www.kleinanzeigen.de/s-anzeige/..." \
    --email "your@email.com" \
    --password "yourpassword" \
    --message "Nachricht" \
    --price 100 \
    --delivery "pickup"
```

## Option 2: Docker Deployment

### 1. Docker Image bauen

```bash
docker build -t kleinanzeigen-bot .
```

### 2. Container ausführen

```bash
docker run --rm \
    -v $(pwd)/cookies.json:/app/cookies.json \
    -v $(pwd)/logs:/app/logs \
    -v $(pwd)/screenshots:/app/screenshots \
    kleinanzeigen-bot \
    --url "https://www.kleinanzeigen.de/s-anzeige/..." \
    --email "your@email.com" \
    --password "yourpassword" \
    --message "Nachricht" \
    --price 100 \
    --delivery "pickup"
```

## Wichtige Hinweise für Ubuntu Server

### 1. Headless-Mode ist Standard
Der Bot läuft standardmäßig im Headless-Mode (`headless=True`), was für Server ohne Display perfekt ist.

### 2. Cookie-Persistenz
Cookies werden in `cookies.json` gespeichert. Stelle sicher, dass die Datei schreibbar ist:
```bash
chmod 666 cookies.json
```

### 3. Logs und Screenshots
Logs werden in `logs/bot.log` geschrieben, Screenshots in `screenshots/`. Stelle sicher, dass diese Verzeichnisse existieren und schreibbar sind:
```bash
mkdir -p logs screenshots
chmod 755 logs screenshots
```

### 4. Systemd Service (Optional)

Erstelle `/etc/systemd/system/kleinanzeigen-bot.service`:

```ini
[Unit]
Description=Kleinanzeigen Bot
After=network.target

[Service]
Type=oneshot
User=your-user
WorkingDirectory=/path/to/ebayScraper
Environment="PATH=/path/to/ebayScraper/venv/bin"
ExecStart=/path/to/ebayScraper/venv/bin/python cli.py \
    --url "https://www.kleinanzeigen.de/s-anzeige/..." \
    --email "your@email.com" \
    --password "yourpassword" \
    --message "Nachricht" \
    --price 100 \
    --delivery "pickup"

[Install]
WantedBy=multi-user.target
```

Dann aktivieren:
```bash
sudo systemctl daemon-reload
sudo systemctl enable kleinanzeigen-bot.service
sudo systemctl start kleinanzeigen-bot.service
```

## Troubleshooting

### Problem: "playwright install chromium" schlägt fehl
**Lösung**: Installiere System-Dependencies:
```bash
python3 -m playwright install-deps chromium
```

### Problem: Browser startet nicht
**Lösung**: Prüfe, ob alle Browser-Args korrekt sind. Die Args `--no-sandbox` und `--disable-setuid-sandbox` sind bereits im Code enthalten.

### Problem: "Permission denied" bei cookies.json
**Lösung**: 
```bash
chmod 666 cookies.json
```

### Problem: Bot wird als Bot erkannt
**Lösung**: Der Bot verwendet bereits Anti-Detection-Maßnahmen:
- `--disable-blink-features=AutomationControlled`
- `navigator.webdriver` wird versteckt
- Realistische User-Agent und Headers
- Random Delays zwischen Aktionen

## Test auf Ubuntu

Um zu testen, ob alles funktioniert:

```bash
# Test mit Debug-Modus (zeigt mehr Logs)
python cli.py \
    --url "https://www.kleinanzeigen.de/s-anzeige/..." \
    --email "your@email.com" \
    --password "yourpassword" \
    --message "Test" \
    --price 100 \
    --delivery "pickup" \
    --debug
```

## Zusammenfassung

✅ **Der Bot ist bereits Ubuntu-Server-ready!**

- Headless-Mode ist Standard
- Alle notwendigen Browser-Args sind enthalten
- Dockerfile ist konfiguriert
- System-Dependencies sind dokumentiert

Du musst nur:
1. System-Dependencies installieren
2. Playwright Browser installieren
3. Bot ausführen (standardmäßig im Headless-Mode)

