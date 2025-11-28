# kleinanzeigen_message_bot

Production-ready Python bot for automating eBay Kleinanzeigen interactions: sending messages and making offers.

## Features

- ✅ **Automated Login** with cookie persistence
- ✅ **Send Messages** to listings
- ✅ **Navigate Conversations** automatically
- ✅ **Make Offers** with price, delivery method, and notes
- ✅ **Error Handling** with screenshots and detailed logging
- ✅ **CLI Interface** using Typer
- ✅ **Docker Support** for easy deployment

## Requirements

- Python 3.10+
- Playwright (browser automation)
- Chrome/Chromium browser

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/TimoDeg/chatBotKleinanzeigen.git
cd chatBotKleinanzeigen
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Install Playwright Browsers

```bash
playwright install chromium
```

### 4. (Optional) Setup Environment Variables

```bash
cp .env.example .env
# Edit .env with your credentials
```

## Usage

### Basic Command

```bash
python cli.py send-and-offer \
    --url "https://www.kleinanzeigen.de/s-anzeige/1234567890" \
    --email "your_email@example.com" \
    --password "your_password" \
    --message "Ist noch verfügbar?" \
    --price 50 \
    --delivery "pickup"
```

### Full Example with All Options

```bash
python cli.py send-and-offer \
    --url "https://www.kleinanzeigen.de/s-anzeige/1234567890" \
    --email "your_email@example.com" \
    --password "your_password" \
    --message "Guten Tag, ich bin interessiert!" \
    --price 75.50 \
    --delivery "both" \
    --shipping-cost 5.99 \
    --note "Kann Mo-Fr abholen oder Versand" \
    --headless \
    --screenshot \
    --timeout 30
```

### Command Options

#### Required Arguments

- `--url` / `-u`: Kleinanzeigen listing URL
- `--email` / `-e`: Your Kleinanzeigen email
- `--password` / `-p`: Your Kleinanzeigen password
- `--message` / `-m`: Message text to send
- `--price`: Offer price in EUR (float)
- `--delivery` / `-d`: Delivery method: `"pickup"` / `"shipping"` / `"both"`

#### Optional Arguments

- `--shipping-cost`: Shipping cost in EUR (only if shipping selected)
- `--note` / `-n`: Additional offer note
- `--headless` / `--no-headless`: Run browser in headless mode (default: True)
- `--no-cookies`: Force fresh login (ignore saved cookies)
- `--screenshot`: Save screenshot after success
- `--timeout` / `-t`: Max wait time in seconds (default: 30)
- `--debug`: Enable DEBUG logging

## Workflow

The bot performs the following steps:

1. **Setup Browser** - Initialize Playwright with anti-detection settings
2. **Authenticate** - Login or use saved cookies
3. **Send Message** - Navigate to listing and send message
4. **Navigate Conversation** - Open the conversation in messages
5. **Make Offer** - Fill offer form and submit

## Delivery Options

- `pickup`: Abholung (pickup only)
- `shipping`: Versand (shipping only)
- `both`: Beides (both options)

## Exit Codes

- `0`: ✅ Success - All steps completed
- `1`: ❌ Login failed
- `2`: ❌ Message sending failed
- `3`: ❌ Conversation not found
- `4`: ❌ Offer making failed
- `5`: ❌ Browser setup failed
- `10`: ⚠️ CAPTCHA detected (manual intervention needed)

## File Structure

```
kleinanzeigen_message_bot/
├── src/
│   ├── __init__.py
│   ├── bot.py              # Core bot class
│   ├── auth.py             # Login & cookie handling
│   ├── selectors.py        # CSS/XPath selectors
│   ├── config.py           # Configuration constants
│   └── utils.py            # Utilities & helpers
├── cli.py                  # Typer CLI entry point
├── requirements.txt        # Python dependencies
├── .env.example           # Environment template
├── Dockerfile             # Docker deployment
├── logs/                  # Log files (auto-created)
├── screenshots/           # Error screenshots (auto-created)
└── README.md             # This file
```

## Logging

Logs are written to:
- **Console**: Colored output with timestamps
- **File**: `logs/bot.log` (rotated at 10MB, kept for 7 days)

Log levels:
- `DEBUG`: Detailed selector attempts, element searches
- `INFO`: Workflow steps, success messages
- `WARNING`: Retries, non-critical issues
- `ERROR`: Failures, exceptions

## Cookie Persistence

The bot saves cookies to `cookies.json` after successful login. On next run, it will:
1. Load cookies
2. Verify they're still valid
3. Skip login if valid, otherwise perform fresh login

Use `--no-cookies` to force a fresh login.

## Error Handling

- **Timeouts**: Logged with selector information
- **Network Errors**: Retried 3x with exponential backoff
- **Session Expired**: Automatic re-login
- **CAPTCHA**: Detected and logged (manual intervention needed)
- **Screenshots**: Automatically saved on errors to `screenshots/`

## Docker Deployment

### Build Image

```bash
docker build -t ka-bot .
```

### Run Container

```bash
docker run --rm ka-bot \
    --url "https://www.kleinanzeigen.de/s-anzeige/..." \
    --email "your_email@example.com" \
    --password "your_password" \
    --message "Ist noch verfügbar?" \
    --price 50 \
    --delivery "pickup"
```

### Docker with Volume for Cookies

```bash
docker run --rm \
    -v $(pwd)/cookies.json:/app/cookies.json \
    -v $(pwd)/logs:/app/logs \
    -v $(pwd)/screenshots:/app/screenshots \
    ka-bot \
    --url "..." \
    --email "..." \
    --password "..." \
    --message "..." \
    --price 50 \
    --delivery "pickup"
```

## Troubleshooting

### Browser Not Found

```bash
playwright install chromium
```

### Selectors Not Found

The bot uses multiple fallback selectors. If all fail:
1. Check `screenshots/` for error screenshots
2. Review `logs/bot.log` for detailed error messages
3. eBay Kleinanzeigen may have changed their HTML structure

### CAPTCHA Detected

If CAPTCHA appears:
1. Bot will log warning and exit with code 10
2. Check screenshot in `screenshots/captcha_detected_*.png`
3. Run with `--no-headless` to solve manually
4. Consider using anti-CAPTCHA service (future enhancement)

### Login Fails

- Verify credentials are correct
- Try `--no-cookies` to force fresh login
- Check if account is locked or requires 2FA
- Run with `--no-headless` to see what's happening

### Rate Limiting

If you get 403 errors:
- Add random delays between actions (future enhancement)
- Reduce frequency of runs
- Use different IP/proxy

## Development

### Run with Debug Logging

```bash
python cli.py send-and-offer \
    --url "..." \
    --email "..." \
    --password "..." \
    --message "..." \
    --price 50 \
    --delivery "pickup" \
    --debug
```

### Run with Visible Browser

```bash
python cli.py send-and-offer \
    --url "..." \
    --email "..." \
    --password "..." \
    --message "..." \
    --price 50 \
    --delivery "pickup" \
    --no-headless
```

## Known Limitations

- **CAPTCHA**: Cannot be solved automatically (requires manual intervention)
- **2FA**: Not supported (accounts with 2FA will fail)
- **Rate Limiting**: No built-in rate limiting (use responsibly)
- **Selector Changes**: eBay Kleinanzeigen may change HTML structure

## Future Enhancements

- [ ] Batch processing (CSV of URLs)
- [ ] Message templating with variables
- [ ] CAPTCHA solving integration
- [ ] Database for tracking sent messages
- [ ] Telegram/Discord notifications
- [ ] Web dashboard
- [ ] Scheduled runs

## Legal Disclaimer

This bot is for educational and personal use only. Use responsibly and in accordance with eBay Kleinanzeigen's Terms of Service. The authors are not responsible for any misuse or violations.

## License

Apache-2.0 License

## Support

For issues, questions, or contributions, please open an issue on GitHub.

