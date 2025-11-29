"""
Configuration constants: exit codes, delivery options, and selectors.
"""

from typing import Dict, List

# Exit codes
EXIT_CODES: Dict[str, int] = {
    "SUCCESS": 0,
    "LOGIN_FAILED": 1,
    "MESSAGE_FAILED": 2,
    "CONVERSATION_NOT_FOUND": 3,
    "OFFER_FAILED": 4,
    "BROWSER_FAILED": 5,
    "CAPTCHA_DETECTED": 10,
}

# Delivery method options mapping
DELIVERY_OPTIONS: Dict[str, str] = {
    "pickup": "Abholung",
    "shipping": "Versand",
    "both": "Beides",
}

# User-Agent pool for rotation
USER_AGENTS: List[str] = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
]

# All selectors as a centralized dictionary
ALL_SELECTORS: Dict[str, List[str]] = {
    "COOKIE_BANNER": [
        "button:has-text('Alle akzeptieren')",
        "button:has-text('Akzeptieren')",
        "button[id*='accept']",
        "button[class*='accept']",
        "[data-testid*='cookie-banner-accept']",
        "[data-qa*='cookie-banner-accept']",
    ],
    "LOGIN_LINK": [
        "a:has-text('Anmelden')",
        "a[href*='login']",
        "a[href*='einloggen']",
        "button:has-text('Anmelden')",
        "[data-testid*='login-link']",
        "[data-qa*='login-link']",
        "button[data-testid*='login-button']",
        "a[class*='login']",
    ],
    "EMAIL_FIELD": [
        "input[name='email']",
        "input[type='email']",
        "input[id*='email']",
        "input[placeholder*='E-Mail']",
        "[data-testid*='email-field']",
        "[data-qa*='email-field']",
    ],
    "PASSWORD_FIELD": [
        "input[name='password']",
        "input[type='password']",
        "input[id*='password']",
        "input[placeholder*='Passwort']",
        "[data-testid*='password-field']",
        "[data-qa*='password-field']",
    ],
    "LOGIN_SUBMIT": [
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
    ],
    "MESSAGE_BUTTON": [
        # 2024/2025 Primary selectors - ID based (most reliable)
        "a#viewad-contact",
        "a[id*='viewad-contact']",
        "button#viewad-contact",
        "button[id*='viewad-contact']",
        # Href-based
        "a[href='#contact']",
        "a[href*='#contact']",
        # Text-based (Playwright :text-is is exact match, very reliable)
        "a:text-is('Nachricht schreiben')",
        "button:text-is('Nachricht schreiben')",
        "a:text-is('Nachricht')",
        "button:text-is('Nachricht')",
        "a:text-is('Kontakt aufnehmen')",
        # Text-based (:text allows partial match)
        "a:text('Nachricht')",
        "button:text('Nachricht')",
        "a:text('Kontakt')",
        "button:text('Kontakt')",
        # Class-based
        "a.viewad-contact",
        "button.viewad-contact",
        "a[class*='contact']",
        "button[class*='contact']",
        "a[class*='message']",
        "button[class*='message']",
        # Data attributes (modern websites use these)
        "a[data-testid*='contact']",
        "button[data-testid*='contact']",
        "a[data-qa*='contact']",
        "button[data-qa*='contact']",
        "[data-gaaction*='contact']",
        # Legacy fallbacks (less reliable, but keep as last resort)
        "button:has-text('Nachricht schreiben')",
        "a:has-text('Nachricht schreiben')",
        "button:has-text('Nachricht senden')",
        "a:has-text('Nachricht senden')",
        "button:has-text('Kontakt')",
        "a:has-text('Kontakt')",
        # Ultra-broad fallbacks (only if nothing else works)
        "button[id*='contact']",
        "a[id*='contact']",
        "a[href*='nachricht']",
    ],
    "MESSAGE_TEXTAREA": [
        # ID-based (most specific and reliable)
        "textarea#viewad-contact-message",
        "textarea#message-text",
        "textarea#message",
        "textarea[id='message-text']",
        "textarea[id='message']",
        "textarea[id*='message']",
        "textarea[id*='text']",
        "textarea[id*='msg']",
        # Name attribute
        "textarea[name='message']",
        "textarea[name='text']",
        "textarea[name*='message']",
        "textarea[name*='text']",
        "textarea[name*='msg']",
        # Class-based
        "textarea.message-text",
        "textarea.viewad-contact-message",
        "textarea[class*='message']",
        "textarea[class*='contact']",
        "textarea[class*='textarea']",
        # Placeholder-based (very common)
        "textarea[placeholder*='Nachricht']",
        "textarea[placeholder*='Deine Nachricht']",
        "textarea[placeholder*='Text']",
        "textarea[placeholder*='Schreib']",
        "textarea[placeholder*='Ihre Nachricht']",
        "textarea[placeholder*='message']",
        # Data attributes
        "textarea[data-testid*='message']",
        "textarea[data-qa*='message']",
        # Generic catch-all (finds ANY textarea on page)
        "textarea",
        # Contenteditable fallback (some modern sites use this instead of textarea)
        "div[contenteditable='true'][role='textbox']",
        "div[contenteditable='true']",
        "[contenteditable='true']",
        # iFrame fallback (if textarea is inside iframe)
        "iframe >> textarea",
    ],
    "MESSAGE_SEND": [
        # Text-based (most reliable for buttons with text)
        "button:text-is('Senden')",
        "button:text-is('Nachricht senden')",
        "button:text-is('Absenden')",
        "button:text-is('Abschicken')",
        # Partial text match
        "button:text('Senden')",
        "button:text('Absenden')",
        "button:text('Abschicken')",
        # ID/Name-based
        "button#message-send",
        "button#message-submit-button",
        "button#send",
        "button[id*='send']",
        "button[id*='submit']",
        "button[id*='submit']",
        "button[name*='send']",
        "button[name*='submit']",
        # Class-based
        "button[class*='send']",
        "button[class*='submit']",
        "button[class*='message-send']",
        # Type-based (form submit buttons)
        "button[type='submit']",
        "input[type='submit']",
        # Data attributes
        "button[data-testid*='send']",
        "button[data-testid='message-submit-button']",
        "button[data-testid*='submit']",
        "button[data-qa*='send']",
        # Legacy fallbacks
        "button:has-text('Senden')",
        "button:has-text('Absenden')",
        "button:has-text('Nachricht senden')",
    ],
    "CONVERSATIONS_PAGE": [
        "a[href*='/nachrichtenbox']",
        "a:has-text('Nachrichten')",
        "a[href*='messages']",
        "[data-testid*='messages-link']",
    ],
    "LATEST_CONVERSATION": [
        "[data-testid='conversation-item']:first-child",
        "[class*='conversation']:first-child",
        "[class*='chat-item']:first-child",
        "a[href*='/nachrichten/']:first-child",
        "[data-qa*='conversation']:first-child",
        "li:first-child a[href*='nachricht']",
    ],
    "OFFER_BUTTON": [
        "button:has-text('Angebot machen')",
        "button:has-text('Angebot unterbreiten')",
        "button:has-text('Angebot')",
        "a:has-text('Angebot machen')",
        "[data-testid*='offer']",
        "[data-qa*='offer']",
        "button[class*='offer']",
    ],
    "OFFER_PRICE_INPUT": [
        "input[name*='price']",
        "input[placeholder*='EUR']",
        "input[placeholder*='€']",
        "input[type='number']",
        "input[id*='price']",
        "input[class*='price']",
    ],
    "OFFER_DELIVERY_SELECT": [
        "select[name*='delivery']",
        "select[name*='shipping']",
        "select[id*='delivery']",
        "select",
    ],
    "OFFER_SHIPPING_INPUT": [
        "input[name*='shipping']",
        "input[placeholder*='Versand']",
        "input[id*='shipping']",
    ],
    "OFFER_NOTE_TEXTAREA": [
        "textarea[name*='note']",
        "textarea[placeholder*='Nachricht']",
        "textarea[id*='note']",
        "textarea",
    ],
    "OFFER_SUBMIT": [
        "button:has-text('Angebot senden')",
        "button:has-text('Angebot unterbreiten')",
        "button:has-text('Senden')",
        "button[type='submit']",
        "[data-testid*='submit']",
        "button:has-text('Absenden')",
    ],
    "SUCCESS_INDICATOR": [
        "text=/erfolgreich/i",
        "text=/gesendet/i",
        "[class*='success']",
        "[class*='confirmed']",
    ],
    # Modal-specific selectors (for popup dialog after clicking message button)
    "MODAL_CONTAINER": [
        "div[role='dialog']",
        "div[class*='modal']",
        "div[class*='dialog']",
        "div[class*='popup']",
        "[aria-modal='true']",
        ".modal-content",
        "[data-testid*='modal']",
    ],
    "MODAL_MESSAGE_TEXTAREA": [
        "textarea#viewad-contact-message",
        "textarea.viewad-contact-message",
        "[data-tr-name='message']",
        "div[role='dialog'] textarea",
        "[aria-modal='true'] textarea",
        "div[class*='modal'] textarea",
        "div[class*='dialog'] textarea",
        "textarea[placeholder*='Nachricht']",
        "textarea[name*='message']",
        "textarea[id*='message']",
        "textarea",
    ],
    "MODAL_PROFILE_NAME_INPUT": [
        "input[placeholder*='Profilname']",
        "input[name*='profile']",
        "input[name*='name']",
        "div[role='dialog'] input[type='text']",
        "[aria-modal='true'] input[type='text']",
    ],
    "MODAL_OFFER_AMOUNT_INPUT": [
        "input[placeholder*='Betrag']",
        "input[name*='price']",
        "input[name*='amount']",
        "input[name*='betrag']",
        "input[type='number']",
        "div[role='dialog'] input[type='number']",
    ],
    "MODAL_SHIPPING_SELECT": [
        "select[name*='shipping']",
        "select[name*='versand']",
        "select[name*='delivery']",
        "div[role='dialog'] select",
        "[aria-modal='true'] select",
    ],
    "MODAL_BUYER_PROTECTION_TOGGLE": [
        "input[type='checkbox'][name*='protection']",
        "input[type='checkbox'][name*='käuferschutz']",
        "div[role='dialog'] input[type='checkbox']",
        "label:has-text('Käuferschutz') input",
    ],
    "MODAL_SEND_BUTTON": [
        "div[role='dialog'] button:text-is('Senden')",
        "[aria-modal='true'] button:text-is('Senden')",
        "div[class*='modal'] button:text-is('Senden')",
        "button:text-is('Senden')",
        "button#message-submit-button",
        "button[data-testid='message-submit-button']",
        "div[role='dialog'] button[type='submit']",
        "button:has-text('Senden')",
    ],
}

# Backward compatibility aliases
MODAL_CONTAINER = ALL_SELECTORS["MODAL_CONTAINER"]
MODAL_MESSAGE_TEXTAREA = ALL_SELECTORS["MODAL_MESSAGE_TEXTAREA"]
MODAL_PROFILE_NAME_INPUT = ALL_SELECTORS["MODAL_PROFILE_NAME_INPUT"]
MODAL_OFFER_AMOUNT_INPUT = ALL_SELECTORS["MODAL_OFFER_AMOUNT_INPUT"]
MODAL_SHIPPING_SELECT = ALL_SELECTORS["MODAL_SHIPPING_SELECT"]
MODAL_BUYER_PROTECTION_TOGGLE = ALL_SELECTORS["MODAL_BUYER_PROTECTION_TOGGLE"]
MODAL_SEND_BUTTON = ALL_SELECTORS["MODAL_SEND_BUTTON"]

