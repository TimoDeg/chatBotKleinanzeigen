"""
Centralized CSS/XPath selectors with fallback options for robustness.
All selectors are lists to support multiple fallback strategies.
"""

# Cookie banner selectors
COOKIE_BANNER_SELECTORS: list = [
    "button:has-text('Alle akzeptieren')",
    "button:has-text('Akzeptieren')",
    "button[id*='accept']",
    "button[class*='accept']",
    "[data-testid*='cookie-banner-accept']",
    "[data-qa*='cookie-banner-accept']",
]

# Login selectors
LOGIN_LINK_SELECTORS: list = [
    "a:has-text('Anmelden')",
    "a[href*='login']",
    "a[href*='einloggen']",
    "button:has-text('Anmelden')",
    "[data-testid*='login-link']",
    "[data-qa*='login-link']",
    "button[data-testid*='login-button']",
    "a[class*='login']",
]

EMAIL_FIELD_SELECTORS: list = [
    "input[name='email']",
    "input[type='email']",
    "input[id*='email']",
    "input[placeholder*='E-Mail']",
    "[data-testid*='email-field']",
    "[data-qa*='email-field']",
]

PASSWORD_FIELD_SELECTORS: list = [
    "input[name='password']",
    "input[type='password']",
    "input[id*='password']",
    "input[placeholder*='Passwort']",
    "[data-testid*='password-field']",
    "[data-qa*='password-field']",
]

LOGIN_SUBMIT_SELECTORS: list = [
    "button#login-submit",
    "#login-submit",
    "button[id='login-submit']",
    "button.button[type='submit']",
    "button[type='submit']:has(span:has-text('Einloggen'))",
    "button:has-text('Einloggen')",
    "button[type='submit']",
    "button:has-text('Anmelden')",
    "[data-testid*='login-submit']",
    "[data-qa*='login-submit']",
]

# Message sending selectors
MESSAGE_BUTTON_SELECTORS: list = [
    "button:has-text('Nachricht schreiben')",
    "a:has-text('Nachricht schreiben')",
    "button:has-text('Nachricht senden')",
    "a:has-text('Nachricht senden')",
    "button:has-text('Kontakt')",
    "a:has-text('Kontakt')",
    "a[href*='nachricht']",
    "button[class*='contact']",
    "button[class*='message']",
    "a[class*='contact']",
    "a[class*='message']",
    "[data-testid*='contact']",
    "[data-qa*='contact']",
    "[data-gaaction*='contact']",
    "button[id*='contact']",
    "a[id*='contact']",
]

MESSAGE_TEXTAREA_SELECTORS: list = [
    "textarea[placeholder*='Nachricht']",
    "textarea[placeholder*='Ihre Nachricht']",
    "textarea[placeholder*='Nachricht an']",
    "textarea[name*='message']",
    "textarea[id*='message']",
    "textarea[class*='message']",
    "textarea[data-testid*='message']",
    "textarea[data-qa*='message']",
    "iframe >> textarea",
    "div[contenteditable='true']",
    "textarea",
]

MESSAGE_SEND_SELECTORS: list = [
    "button:has-text('Nachricht senden')",
    "button:has-text('Senden')",
    "button[type='submit']",
    "button[class*='send']",
    "[data-testid*='send']",
    "[data-qa*='send']",
    "button:has-text('Absenden')",
]

# Conversation navigation selectors
CONVERSATIONS_PAGE_SELECTORS: list = [
    "a[href*='/nachrichtenbox']",
    "a:has-text('Nachrichten')",
    "a[href*='messages']",
    "[data-testid*='messages-link']",
]

LATEST_CONVERSATION_SELECTORS: list = [
    "[data-testid='conversation-item']:first-child",
    "[class*='conversation']:first-child",
    "[class*='chat-item']:first-child",
    "a[href*='/nachrichten/']:first-child",
    "[data-qa*='conversation']:first-child",
    "li:first-child a[href*='nachricht']",
]

# Offer making selectors
OFFER_BUTTON_SELECTORS: list = [
    "button:has-text('Angebot machen')",
    "button:has-text('Angebot unterbreiten')",
    "button:has-text('Angebot')",
    "a:has-text('Angebot machen')",
    "[data-testid*='offer']",
    "[data-qa*='offer']",
    "button[class*='offer']",
]

OFFER_PRICE_INPUT_SELECTORS: list = [
    "input[name*='price']",
    "input[placeholder*='EUR']",
    "input[placeholder*='€']",
    "input[type='number']",
    "input[id*='price']",
    "input[class*='price']",
]

OFFER_DELIVERY_SELECT_SELECTORS: list = [
    "select[name*='delivery']",
    "select[name*='shipping']",
    "select[id*='delivery']",
    "select",
]

OFFER_SHIPPING_INPUT_SELECTORS: list = [
    "input[name*='shipping']",
    "input[placeholder*='Versand']",
    "input[id*='shipping']",
]

OFFER_NOTE_TEXTAREA_SELECTORS: list = [
    "textarea[name*='note']",
    "textarea[placeholder*='Nachricht']",
    "textarea[id*='note']",
    "textarea",
]

OFFER_SUBMIT_SELECTORS: list = [
    "button:has-text('Angebot senden')",
    "button:has-text('Angebot unterbreiten')",
    "button:has-text('Senden')",
    "button[type='submit']",
    "[data-testid*='submit']",
    "button:has-text('Absenden')",
]

# Success indicators
SUCCESS_INDICATOR_SELECTORS: list = [
    "text=/erfolgreich/i",
    "text=/gesendet/i",
    "[class*='success']",
    "[class*='confirmed']",
]

# Backward compatibility - keep old names as aliases
COOKIE_BANNER = COOKIE_BANNER_SELECTORS
LOGIN_LINK = LOGIN_LINK_SELECTORS
EMAIL_FIELD = EMAIL_FIELD_SELECTORS
PASSWORD_FIELD = PASSWORD_FIELD_SELECTORS
LOGIN_SUBMIT = LOGIN_SUBMIT_SELECTORS
MESSAGE_BUTTON = MESSAGE_BUTTON_SELECTORS
MESSAGE_TEXTAREA = MESSAGE_TEXTAREA_SELECTORS
MESSAGE_SEND = MESSAGE_SEND_SELECTORS
CONVERSATIONS_PAGE = CONVERSATIONS_PAGE_SELECTORS
LATEST_CONVERSATION = LATEST_CONVERSATION_SELECTORS
OFFER_BUTTON = OFFER_BUTTON_SELECTORS
OFFER_PRICE_INPUT = OFFER_PRICE_INPUT_SELECTORS
OFFER_DELIVERY_SELECT = OFFER_DELIVERY_SELECT_SELECTORS
OFFER_SHIPPING_INPUT = OFFER_SHIPPING_INPUT_SELECTORS
OFFER_NOTE_TEXTAREA = OFFER_NOTE_TEXTAREA_SELECTORS
OFFER_SUBMIT = OFFER_SUBMIT_SELECTORS
SUCCESS_INDICATOR = SUCCESS_INDICATOR_SELECTORS
