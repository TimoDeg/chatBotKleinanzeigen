"""
Configuration constants, timeouts, and default values.
"""

from typing import Dict

# Timeout settings (in seconds)
TIMEOUTS: Dict[str, int] = {
    "page_load": 10,
    "modal_appearance": 5,
    "action": 3,
    "login": 30,
    "selector_wait": 10,
    "success_confirmation": 3,
}

# Delivery method options mapping
DELIVERY_OPTIONS: Dict[str, str] = {
    "pickup": "Abholung",
    "shipping": "Versand",
    "both": "Beides",
}

# Default values
DEFAULT_MESSAGE: str = "Ist noch verfügbar?"
HEADLESS_MODE: bool = True
LOG_LEVEL: str = "INFO"

# File paths
COOKIES_PATH: str = "./cookies.json"
LOGS_DIR: str = "./logs"
SCREENSHOTS_DIR: str = "./screenshots"
LOG_FILE: str = "./logs/bot.log"

# Browser settings
BROWSER_ARGS: list = [
    "--disable-blink-features=AutomationControlled",
    "--disable-dev-shm-usage",
    "--no-sandbox",
    "--disable-setuid-sandbox",
]

# Retry settings
MAX_RETRIES: int = 3
RETRY_BACKOFF: int = 5  # seconds

# Exit codes
EXIT_SUCCESS: int = 0
EXIT_LOGIN_FAILED: int = 1
EXIT_MESSAGE_FAILED: int = 2
EXIT_CONVERSATION_NOT_FOUND: int = 3
EXIT_OFFER_FAILED: int = 4
EXIT_BROWSER_FAILED: int = 5
EXIT_CAPTCHA_DETECTED: int = 10

