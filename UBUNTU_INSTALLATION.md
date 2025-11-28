# Ubuntu Server Installation - Schritt für Schritt

## Schnellstart (Alle Befehle auf einmal)

```bash
# 1. System-Dependencies installieren
sudo apt-get update
sudo apt-get install -y python3.10 python3-pip python3-venv git wget gnupg ca-certificates fonts-liberation libasound2 libatk-bridge2.0-0 libatk1.0-0 libatspi2.0-0 libcups2 libdbus-1-3 libdrm2 libgbm1 libgtk-3-0 libnspr4 libnss3 libwayland-client0 libxcomposite1 libxdamage1 libxfixes3 libxkbcommon0 libxrandr2 xdg-utils

# 2. Projekt klonen (Branch: ubuntu)
git clone -b ubuntu <DEINE_GITHUB_REPO_URL> ebayScraper
cd ebayScraper

# 3. Virtuelle Umgebung erstellen
python3 -m venv venv
source venv/bin/activate

# 4. Python Dependencies installieren
pip install --upgrade pip
pip install -r requirements.txt

# 5. Playwright Browser installieren
python3 -m playwright install chromium
python3 -m playwright install-deps chromium

# 6. Verzeichnisse erstellen
mkdir -p logs screenshots
chmod 755 logs screenshots

# 7. Bot ausführen
python cli.py \
    --url "https://www.kleinanzeigen.de/s-anzeige/..." \
    --email "your@email.com" \
    --password "yourpassword" \
    --message "Nachricht" \
    --price 100 \
    --delivery "pickup"
```

## Detaillierte Anleitung

### Schritt 1: System-Dependencies installieren

```bash
sudo apt-get update
sudo apt-get install -y \
    python3.10 \
    python3-pip \
    python3-venv \
    git \
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

### Schritt 2: Projekt klonen

**Wichtig:** Ersetze `<DEINE_GITHUB_REPO_URL>` mit deiner tatsächlichen GitHub Repository URL!

```bash
# Repository klonen (Branch: ubuntu)
git clone -b ubuntu <DEINE_GITHUB_REPO_URL> ebayScraper

# In das Verzeichnis wechseln
cd ebayScraper
```

**Beispiel:**
```bash
git clone -b ubuntu https://github.com/TimoDeg/chatBotKleinanzeigen.git ebayScraper
cd ebayScraper
```

### Schritt 3: Virtuelle Umgebung erstellen

```bash
# Virtuelle Umgebung erstellen
python3 -m venv venv

# Aktivieren
source venv/bin/activate
```

**Hinweis:** Die virtuelle Umgebung muss bei jeder neuen SSH-Session aktiviert werden:
```bash
cd ebayScraper
source venv/bin/activate
```

### Schritt 4: Python Dependencies installieren

```bash
# Pip aktualisieren
pip install --upgrade pip

# Dependencies installieren
pip install -r requirements.txt
```

### Schritt 5: Playwright Browser installieren

```bash
# Chromium Browser installieren
python3 -m playwright install chromium

# System-Dependencies für Playwright installieren
python3 -m playwright install-deps chromium
```

### Schritt 6: Verzeichnisse erstellen

```bash
# Logs und Screenshots Verzeichnisse
mkdir -p logs screenshots
chmod 755 logs screenshots
```

### Schritt 7: Bot ausführen

```bash
# Bot im Headless-Mode ausführen (Standard für Server)
python cli.py \
    --url "https://www.kleinanzeigen.de/s-anzeige/..." \
    --email "your@email.com" \
    --password "yourpassword" \
    --message "Ist noch verfügbar?" \
    --price 100 \
    --delivery "pickup"
```

## Automatisches Installations-Script

Alternativ kannst du das Installations-Script verwenden:

```bash
# Script herunterladen (wenn du es auf GitHub hochgeladen hast)
wget https://raw.githubusercontent.com/<USERNAME>/<REPO>/ubuntu/install_ubuntu.sh

# Oder manuell erstellen und ausführen
chmod +x install_ubuntu.sh
bash install_ubuntu.sh
```

## Wichtige Hinweise

### 1. Virtuelle Umgebung aktivieren

Bei jeder neuen SSH-Session musst du die virtuelle Umgebung aktivieren:
```bash
cd ~/ebayScraper  # oder wo auch immer du es installiert hast
source venv/bin/activate
```

### 2. Cookies persistieren

Cookies werden in `cookies.json` gespeichert. Stelle sicher, dass die Datei schreibbar ist:
```bash
touch cookies.json
chmod 666 cookies.json
```

### 3. Logs ansehen

```bash
# Live-Logs ansehen
tail -f logs/bot.log

# Letzte 50 Zeilen
tail -n 50 logs/bot.log
```

### 4. Bot als Service einrichten (Optional)

Erstelle `/etc/systemd/system/kleinanzeigen-bot.service`:

```ini
[Unit]
Description=Kleinanzeigen Bot
After=network.target

[Service]
Type=oneshot
User=dein-user
WorkingDirectory=/home/dein-user/ebayScraper
Environment="PATH=/home/dein-user/ebayScraper/venv/bin"
ExecStart=/home/dein-user/ebayScraper/venv/bin/python cli.py \
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

### Problem: "python3.10 not found"
```bash
# Prüfe verfügbare Python Version
python3 --version

# Falls Python 3.10 nicht verfügbar, installiere es:
sudo apt-get install -y software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt-get update
sudo apt-get install -y python3.10 python3.10-venv python3.10-pip
```

### Problem: "playwright install chromium" schlägt fehl
```bash
# Stelle sicher, dass System-Dependencies installiert sind
python3 -m playwright install-deps chromium
```

### Problem: "Permission denied" bei cookies.json
```bash
chmod 666 cookies.json
```

## Zusammenfassung - Alle Befehle

```bash
# 1. System-Dependencies
sudo apt-get update && sudo apt-get install -y python3.10 python3-pip python3-venv git wget gnupg ca-certificates fonts-liberation libasound2 libatk-bridge2.0-0 libatk1.0-0 libatspi2.0-0 libcups2 libdbus-1-3 libdrm2 libgbm1 libgtk-3-0 libnspr4 libnss3 libwayland-client0 libxcomposite1 libxdamage1 libxfixes3 libxkbcommon0 libxrandr2 xdg-utils

# 2. Klonen (ERsetze <REPO_URL> mit deiner URL!)
git clone -b ubuntu <REPO_URL> ebayScraper && cd ebayScraper

# 3. Virtuelle Umgebung
python3 -m venv venv && source venv/bin/activate

# 4. Dependencies
pip install --upgrade pip && pip install -r requirements.txt

# 5. Playwright
python3 -m playwright install chromium && python3 -m playwright install-deps chromium

# 6. Verzeichnisse
mkdir -p logs screenshots && chmod 755 logs screenshots

# 7. Bot starten
python cli.py --url "..." --email "..." --password "..." --message "..." --price 100 --delivery "pickup"
```

