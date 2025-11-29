"""
Authentication module with human-like behavior.
"""

from playwright.async_api import Page
from loguru import logger

from src.stealth.human_behavior import HumanBehavior
from src.utils.selectors import SelectorManager
from src.utils.helpers import take_screenshot


async def login(
    page: Page,
    email: str,
    password: str,
    human: HumanBehavior,
    cookies_loaded: bool = False,
) -> bool:
    """
    Perform human-like login.
    
    Args:
        page: Playwright page
        email: User email
        password: User password
        human: HumanBehavior instance
        
    Returns:
        True if login successful, False otherwise
    """
    try:
        logger.info("🔐 Logging in...")
        
        # Navigate to login page
        await page.goto("https://www.kleinanzeigen.de/m-einloggen.html", wait_until="domcontentloaded")
        await human.delay("navigating")
        
        selectors = SelectorManager()
        # Only search for cookie banner if this is a fresh login (no cookies)
        if not cookies_loaded:
            logger.info("Accepting cookie banner...")
            cookie_btn = await selectors.find(page, "COOKIE_BANNER", timeout=3000)
            if cookie_btn:
                await human.human_click(page, cookie_btn)
                await human.delay("default")
        else:
            logger.debug("Cookies loaded - skipping cookie banner")
        
        # Fill email
        email_field = await selectors.find(page, "EMAIL_FIELD", timeout=10000)
        if not email_field:
            logger.error("❌ Email field not found")
            await take_screenshot(page, "login_email_error")
            return False
        
        await human.human_type(email_field, email)
        await human.delay("default")
        
        # Fill password
        password_field = await selectors.find(page, "PASSWORD_FIELD", timeout=10000)
        if not password_field:
            logger.error("❌ Password field not found")
            await take_screenshot(page, "login_password_error")
            return False
        
        await human.human_type(password_field, password)
        await human.delay("default")
        
        # Click submit
        submit_btn = await selectors.find(page, "LOGIN_SUBMIT", timeout=10000)
        if not submit_btn:
            logger.error("❌ Submit button not found")
            await take_screenshot(page, "login_submit_error")
            return False
        
        await human.human_click(page, submit_btn)
        await page.wait_for_timeout(2000)
        
        # Wait for redirect or login completion
        initial_url = page.url
        url_changed = False
        for i in range(20):  # Check 20 times over 10 seconds
            await page.wait_for_timeout(500)
            current_url = page.url
            if current_url != initial_url:
                url_changed = True
                break
            if "kleinanzeigen.de" in current_url and "einloggen" not in current_url.lower():
                url_changed = True
                break
        
        if url_changed:
            await page.wait_for_timeout(3000)
        
        # Check for CAPTCHA
        try:
            captcha_iframe = await page.wait_for_selector("iframe[src*='captcha']", timeout=2000)
            if captcha_iframe:
                logger.warning("⚠️  CAPTCHA detected")
                await take_screenshot(page, "captcha_detected")
                return False
        except:
            pass
        
        # Verify login success
        current_url = page.url.lower()
        if "login=success" in current_url:
            logger.info("✅ Login successful")
            return True
        
        # Check for logged-in indicators
        logged_in_selectors = [
            "a[href*='/nachrichtenbox']",
            "a[href*='/meine-anzeigen']",
            "[class*='user-menu']",
            "a:has-text('Meine Anzeigen')",
        ]
        
        for selector in logged_in_selectors:
            try:
                element = await page.wait_for_selector(selector, timeout=3000)
                if element and await element.is_visible():
                    logger.info("✅ Login successful")
                    return True
            except:
                continue
        
        logger.error("❌ Login failed: Could not verify login")
        await take_screenshot(page, "login_failed")
        return False
        
    except Exception as e:
        logger.error(f"❌ Login failed: {e}")
        await take_screenshot(page, "login_error")
        return False

