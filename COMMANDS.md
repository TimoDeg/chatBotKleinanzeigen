# Gespeicherte Befehle

## Standard-Befehl

```bash
source venv/bin/activate

python cli.py send-and-offer \
    --url "https://www.kleinanzeigen.de/s-anzeige/baba-ddr5-ram/3259103117-225-4564" \
    --email "degtyarevsemen@gmail.com" \
    --password "SamD1990*" \
    --message "Ist noch verfügbar?" \
    --price 100 \
    --delivery "pickup"
```

## Schnellstart mit Script

```bash
./run_bot.sh
```

Oder mit eigener URL:
```bash
./run_bot.sh "https://www.kleinanzeigen.de/s-anzeige/..."
```

## Gespeicherte Daten

- **Email**: degtyarevsemen@gmail.com
- **Password**: SamD1990*
- **Standard URL**: https://www.kleinanzeigen.de/s-anzeige/baba-ddr5-ram/3259103117-225-4564
- **Standard Message**: "Ist noch verfügbar?"
- **Standard Price**: 100 EUR
- **Standard Delivery**: pickup

## Weitere Optionen

Mit Screenshot:
```bash
python cli.py send-and-offer \
    --url "..." \
    --email "degtyarevsemen@gmail.com" \
    --password "SamD1990*" \
    --message "Ist noch verfügbar?" \
    --price 100 \
    --delivery "pickup" \
    --screenshot
```

Mit sichtbarem Browser (für Debugging):
```bash
python cli.py send-and-offer \
    --url "..." \
    --email "degtyarevsemen@gmail.com" \
    --password "SamD1990*" \
    --message "Ist noch verfügbar?" \
    --price 100 \
    --delivery "pickup" \
    --no-headless
```

Mit Versand:
```bash
python cli.py send-and-offer \
    --url "..." \
    --email "degtyarevsemen@gmail.com" \
    --password "SamD1990*" \
    --message "Ist noch verfügbar?" \
    --price 100 \
    --delivery "shipping" \
    --shipping-cost 5.99
```
