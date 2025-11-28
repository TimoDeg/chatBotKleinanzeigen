"""
Centralized CSS/XPath selectors for eBay Kleinanzeigen elements.
Easy to update if the website changes its HTML structure.
"""

# Cookie banner selectors
COOKIE_BANNER: list = [
    "button:has-text('Alle akzeptieren')",
    "button:has-text('Akzeptieren')",
    "button[id*='accept']",
    "button[class*='accept']",
]

# Login selectors
LOGIN_LINK: list = [
    "a:has-text('Anmelden')",
    "a[href*='login']",
    "a[href*='einloggen']",
    "button:has-text('Anmelden')",
    "a[data-gaaction='login']",
    "[class*='login']",
    "[class*='anmelden']",
    "a[title*='Anmelden']",
    "a[title*='Login']",
]

EMAIL_FIELD: list = [
    "input[name='email']",
    "input[type='email']",
    "input[id*='email']",
    "input[placeholder*='E-Mail']",
]

PASSWORD_FIELD: list = [
    "input[name='password']",
    "input[type='password']",
    "input[id*='password']",
]

LOGIN_SUBMIT: list = [
    "button#login-submit",  # Exact ID from website: <button id="login-submit">
    "#login-submit",  # Shorthand
    "button[id='login-submit']",  # Alternative syntax
    "button.button[type='submit']",  # Class + type
    "button[type='submit']:has(span:has-text('Einloggen'))",  # Text in span
    "button:has-text('Einloggen')",  # Text-based fallback
    "button[type='submit']",  # Generic submit button
    "button:has-text('Anmelden')",  # Alternative text
    "button[class*='submit']",
    "button[class*='login']",
    "button[id*='submit']",
    "button[id*='login']",
    "input[type='submit']",
    "[data-testid*='login-submit']",
    "[data-qa*='login-submit']",
]

# Message sending selectors
MESSAGE_BUTTON: list = [
    "button:has-text('Nachricht schreiben')",
    "button:has-text('Nachricht senden')",
    "a:has-text('Nachricht schreiben')",
    "button[class*='message']",
    "a[href*='nachricht']",
]

MESSAGE_MODAL: list = [
    ".modal-content",
    ".qa-chat-form",
    "[class*='modal']",
    "[class*='message-form']",
]

MESSAGE_TEXTAREA: list = [
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

MESSAGE_SEND: list = [
    "button:has-text('Nachricht senden')",
    "button:has-text('Senden')",
    "button[type='submit']",
    "button[class*='send']",
]

# Conversation navigation selectors
CONVERSATIONS_PAGE: list = [
    "a[href*='/nachrichtenbox']",
    "a:has-text('Nachrichten')",
    "a[href*='messages']",
]

LATEST_CONVERSATION: list = [
    ".qa-chat-item:first-child",
    "[class*='conversation']:first-child",
    "[class*='chat-item']:first-child",
    "a[href*='/nachrichten/']:first-child",
]

# Offer making selectors
OFFER_BUTTON: list = [
    "button:has-text('Angebot machen')",
    "button:has-text('Angebot unterbreiten')",
    "button:has-text('Angebot')",
    "a:has-text('Angebot machen')",
]

OFFER_MODAL: list = [
    ".modal-content",
    "[class*='offer']",
    "[class*='modal']",
    "[class*='form']",
]

OFFER_PRICE_INPUT: list = [
    "input[name*='price']",
    "input[placeholder*='EUR']",
    "input[type='number']",
    "input[id*='price']",
]

OFFER_DELIVERY_SELECT: list = [
    "select[name*='delivery']",
    "select[name*='shipping']",
    "select[id*='delivery']",
    "select",
]

OFFER_SHIPPING_INPUT: list = [
    "input[name*='shipping']",
    "input[placeholder*='Versand']",
    "input[id*='shipping']",
]

OFFER_NOTE_TEXTAREA: list = [
    "textarea[name*='note']",
    "textarea[placeholder*='Nachricht']",
    "textarea[id*='note']",
    "textarea",
]

OFFER_SUBMIT: list = [
    "button:has-text('Angebot senden')",
    "button:has-text('Angebot unterbreiten')",
    "button:has-text('Senden')",
    "button[type='submit']",
]

# Success indicators
SUCCESS_INDICATOR: list = [
    "text=/Angebot.*versendet/",
    "text=/erfolgreich/",
    "text=/versendet/",
    "[class*='success']",
]

