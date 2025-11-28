"""
Authentication and session management with cookie persistence.
"""

import json
import os
import time
from typing import Optional

from playwright.async_api import Browser, Page, BrowserContext
from loguru import logger

from src.config import COOKIES_PATH, TIMEOUTS
from src.selectors import (
    COOKIE_BANNER,
    LOGIN_LINK,
    EMAIL_FIELD,
    PASSWORD_FIELD,
    LOGIN_SUBMIT,
)
from src.utils import safe_click, safe_fill, take_screenshot, random_delay


async def save_cookies(context: BrowserContext) -> bool:
    """
    Save browser cookies to JSON file for persistent sessions.
    Extends cookie expiration to 30 days to keep sessions alive longer.
    
    Args:
        context: Playwright browser context
        
    Returns:
        True if saved successfully, False otherwise
    """
    try:
        cookies = await context.cookies()
        
        if not cookies:
            logger.warning("No cookies to save")
            return False
        
        # Extend cookie expiration (30 days from now)
        extended_cookies = []
        current_time = time.time()
        expiration_extension = 30 * 24 * 60 * 60  # 30 days in seconds
        
        for cookie in cookies:
            # Extend expiration if it exists
            if 'expires' in cookie and cookie['expires'] > 0:
                # Extend to 30 days from now
                cookie['expires'] = int(current_time) + expiration_extension
            elif 'expires' not in cookie:
                # Add expiration if missing (session cookie -> persistent)
                cookie['expires'] = int(current_time) + expiration_extension
            
            extended_cookies.append(cookie)
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(COOKIES_PATH) or ".", exist_ok=True)
        
        with open(COOKIES_PATH, "w", encoding="utf-8") as f:
            json.dump(extended_cookies, f, indent=2)
        
        logger.info(f"✅ Cookies saved to {COOKIES_PATH} (extended expiration to 30 days)")
        return True
    except Exception as e:
        logger.error(f"Failed to save cookies: {e}")
        return False


async def load_cookies(context: BrowserContext) -> bool:
    """
    Load cookies from JSON file if it exists.
    Validates cookies and extends expiration if needed.
    
    Args:
        context: Playwright browser context
        
    Returns:
        True if cookies loaded, False if file doesn't exist
    """
    if not os.path.exists(COOKIES_PATH):
        logger.debug("No existing cookies file found")
        return False
    
    try:
        with open(COOKIES_PATH, "r", encoding="utf-8") as f:
            cookies = json.load(f)
        
        if not cookies:
            logger.debug("Cookie file is empty")
            return False
        
        # Filter out expired cookies and extend valid ones
        current_time = time.time()
        expiration_extension = 30 * 24 * 60 * 60  # 30 days
        
        valid_cookies = []
        for cookie in cookies:
            # Check if cookie is expired
            if 'expires' in cookie:
                if cookie['expires'] <= current_time:
                    continue  # Skip expired cookies
                # Extend expiration if it's expiring soon (within 7 days)
                elif cookie['expires'] < current_time + (7 * 24 * 60 * 60):
                    cookie['expires'] = int(current_time) + expiration_extension
                    logger.debug(f"Extended expiration for cookie: {cookie.get('name', 'unknown')}")
            else:
                # Session cookie - add expiration
                cookie['expires'] = int(current_time) + expiration_extension
            
            valid_cookies.append(cookie)
        
        if not valid_cookies:
            logger.debug("All cookies are expired")
            return False
        
        await context.add_cookies(valid_cookies)
        logger.info(f"✅ Cookies loaded from {COOKIES_PATH} ({len(valid_cookies)} valid cookies)")
        return True
    except Exception as e:
        logger.warning(f"Failed to load cookies: {e}")
        return False


async def accept_cookie_banner(page: Page) -> bool:
    """
    Accept cookie banner if present.
    
    Args:
        page: Playwright page object
        
    Returns:
        True if banner was found and accepted, False otherwise
    """
    try:
        logger.debug("Checking for cookie banner...")
        clicked = await safe_click(
            page,
            COOKIE_BANNER,
            timeout=3,
            description="cookie banner"
        )
        
        if clicked:
            logger.info("Cookie banner accepted")
            await page.wait_for_timeout(1000)  # Wait 1 second after click
        
        return clicked
    except Exception as e:
        logger.debug(f"No cookie banner or error: {e}")
        return False


async def login(
    page: Page,
    email: str,
    password: str,
    force_fresh: bool = False
) -> bool:
    """
    Perform login flow on eBay Kleinanzeigen.
    
    Args:
        page: Playwright page object
        email: User email address
        password: User password
        force_fresh: If True, skip cookie check and force new login
        
    Returns:
        True if login successful, False otherwise
    """
    try:
        logger.info("Starting login process...")
        
        # We're already on the login page (navigated in authenticate), just accept cookie banner
        logger.info("Accepting cookie banner...")
        await accept_cookie_banner(page)
        
        # We're already on the login page, ready to fill credentials
        logger.info("On login page, ready to fill credentials...")
        
        # Fill email - with 1 second delay
        logger.info("Filling email...")
        email_filled = await safe_fill(
            page,
            EMAIL_FIELD,
            email,
            timeout=10,
            description="email field"
        )
        
        if not email_filled:
            # Try alternative: find any email input and fill it
            logger.warning("Standard email field not found, trying alternative selectors...")
            try:
                email_input = await page.wait_for_selector("input[type='email'], input[name*='mail'], input[id*='mail']", timeout=5000)
                if email_input:
                    await email_input.fill(email)
                    logger.info("Email filled using alternative selector")
                    email_filled = True
            except:
                pass
        
        if not email_filled:
            logger.error("Failed to find email field")
            await take_screenshot(page, prefix="login_email_error")
            # Try to continue anyway - maybe we're already on a different page
            current_url = page.url
            logger.warning(f"Current URL: {current_url}")
            # Check if login=success is in URL (successful login)
            if "login=success" in current_url.lower():
                logger.info("✅ Already logged in (login=success in URL)")
                return True
            if "login" not in current_url.lower() and "einloggen" not in current_url.lower():
                logger.warning("Not on login page, might already be logged in or redirected")
                return True
            return False
        
        # Wait exactly 1 second before filling password
        logger.info("Waiting 1 second before password...")
        await page.wait_for_timeout(1000)
        
        # Fill password - with 1 second delay after email
        logger.info("Filling password...")
        password_filled = await safe_fill(
            page,
            PASSWORD_FIELD,
            password,
            timeout=10,
            description="password field"
        )
        
        if not password_filled:
            # Try alternative: find any password input
            logger.warning("Standard password field not found, trying alternative selectors...")
            try:
                password_input = await page.wait_for_selector("input[type='password']", timeout=5000)
                if password_input:
                    await password_input.fill(password)
                    logger.info("Password filled using alternative selector")
                    password_filled = True
            except:
                pass
        
        if not password_filled:
            logger.error("Failed to find password field")
            await take_screenshot(page, prefix="login_password_error")
            return False
        
        # Wait 2 seconds before clicking login button (1s more as requested)
        logger.info("Waiting 2 seconds before clicking login button...")
        await page.wait_for_timeout(2000)
        
        # Submit login form - try multiple approaches with better error handling
        logger.info("Submitting login form...")
        
        # First, try standard selectors
        submit_clicked = False
        for selector in LOGIN_SUBMIT:
            try:
                logger.debug(f"Trying submit selector: {selector}")
                submit_button = await page.wait_for_selector(selector, timeout=5000, state="visible")
                if submit_button:
                    is_visible = await submit_button.is_visible()
                    is_enabled = await submit_button.is_enabled()
                    logger.debug(f"Submit button found - visible: {is_visible}, enabled: {is_enabled}")
                    
                    if is_visible and is_enabled:
                        await submit_button.scroll_into_view_if_needed()
                        # No additional delay - already waited 1 second before
                        
                        # Try multiple click methods
                        try:
                            # First try: Normal click
                            await submit_button.click(timeout=5000, force=False)
                            logger.info(f"✅ Submit button clicked with: {selector}")
                            submit_clicked = True
                            break
                        except Exception as e:
                            logger.debug(f"Normal click failed: {e}, trying JavaScript click...")
                            try:
                                # Second try: JavaScript click (more reliable)
                                await submit_button.evaluate("el => { el.focus(); el.click(); }")
                                logger.info(f"✅ Submit button clicked via JavaScript: {selector}")
                                submit_clicked = True
                                break
                            except Exception as e2:
                                logger.debug(f"JavaScript click also failed: {e2}, trying force click...")
                                try:
                                    # Third try: Force click
                                    await submit_button.click(timeout=5000, force=True)
                                    logger.info(f"✅ Submit button clicked with force: {selector}")
                                    submit_clicked = True
                                    break
                                except Exception as e3:
                                    logger.debug(f"Force click also failed: {e3}")
                                    continue
            except Exception as e:
                logger.debug(f"Submit selector failed: {selector} - {e}")
                continue
        
        # If standard selectors failed, try alternatives
        if not submit_clicked:
            logger.warning("Standard submit button not found, trying alternatives...")
            
            # Try 1: Press Enter on password field
            try:
                password_input = await page.wait_for_selector("input[type='password']", timeout=3000)
                if password_input:
                    logger.info("Pressing Enter on password field...")
                    await password_input.press("Enter")
                    logger.info("✅ Pressed Enter on password field")
                    submit_clicked = True
            except Exception as e:
                logger.debug(f"Enter on password field failed: {e}")
            
            # Try 2: Find any button with "Anmelden" text
            if not submit_clicked:
                try:
                    submit_button = await page.wait_for_selector(
                        "button:has-text('Anmelden'), input[value*='Anmelden'], button[type='submit']",
                        timeout=3000
                    )
                    if submit_button:
                        await submit_button.scroll_into_view_if_needed()
                        await page.wait_for_timeout(500)
                        await submit_button.click(timeout=5000)
                        logger.info("✅ Clicked alternative submit button")
                        submit_clicked = True
                except Exception as e:
                    logger.debug(f"Alternative submit button failed: {e}")
            
            # Try 3: JavaScript click on any submit button
            if not submit_clicked:
                try:
                    all_submit_buttons = await page.query_selector_all("button[type='submit'], input[type='submit']")
                    for btn in all_submit_buttons:
                        try:
                            is_visible = await btn.is_visible()
                            if is_visible:
                                await btn.evaluate("el => el.click()")
                                logger.info("✅ Clicked submit button via JavaScript")
                                submit_clicked = True
                                break
                        except:
                            continue
                except Exception as e:
                    logger.debug(f"JavaScript submit search failed: {e}")
        
        # Last resort: Press Enter key
        if not submit_clicked:
            logger.warning("All submit methods failed, trying Enter key as last resort...")
            try:
                await page.keyboard.press("Enter")
                logger.info("✅ Pressed Enter as last resort")
                submit_clicked = True
                await page.wait_for_timeout(2000)
            except Exception as e:
                logger.debug(f"Enter key failed: {e}")
        
        if not submit_clicked:
            logger.error("❌ Failed to submit login form")
            await take_screenshot(page, prefix="login_submit_error")
            return False
        
        # Wait for redirect or login completion
        logger.info("Waiting for login to complete...")
        await page.wait_for_timeout(2000)  # Initial wait
        
        # Wait for navigation or page change - check more frequently and longer
        initial_url = page.url
        logger.debug(f"Initial URL: {initial_url}")
        
        url_changed = False
        for i in range(20):  # Check 20 times over 10 seconds
            await page.wait_for_timeout(500)
            current_url = page.url
            if current_url != initial_url:
                logger.info(f"✅ URL changed: {initial_url} → {current_url}")
                url_changed = True
                break
            # Also check if we're redirected to home page or dashboard
            # login=success in URL is a success indicator, not a login page
            if "kleinanzeigen.de" in current_url and "einloggen" not in current_url.lower() and ("login" not in current_url.lower() or "login=success" in current_url.lower()):
                logger.info(f"✅ Redirected away from login page: {current_url}")
                url_changed = True
                break
        
        # Wait a bit more for page to settle after redirect
        if url_changed:
            await page.wait_for_timeout(3000)
        else:
            logger.warning("URL did not change after login attempt")
            await page.wait_for_timeout(2000)
        
        # Try to wait for load state, but don't fail if it times out
        try:
            await page.wait_for_load_state("domcontentloaded", timeout=5000)
        except:
            logger.debug("Load state timeout, continuing...")
        
        # Check for CAPTCHA
        captcha_indicators = [
            "iframe[src*='captcha']",
            "[class*='captcha']",
            "text=/captcha/i",
        ]
        
        for indicator in captcha_indicators:
            try:
                await page.wait_for_selector(indicator, timeout=2000)
                logger.warning("⚠️ CAPTCHA detected! Manual intervention needed.")
                await take_screenshot(page, prefix="captcha_detected")
                return False
            except:
                continue
        
        # Verify login success - check URL first
        current_url = page.url.lower()
        logger.info(f"Current URL after login attempt: {page.url}")
        
        # Check if URL contains login=success - this is a clear success indicator
        if "login=success" in current_url or "login=success" in page.url:
            logger.info("✅ Login successful! URL contains 'login=success'")
            return True
        
        # Check if we're actually logged in, even if still on login page
        # Sometimes the URL doesn't change but login is successful
        logger.info("Checking if login was successful (even if URL didn't change)...")
        
        # Check for logged-in indicators on the page
        logged_in_indicators = [
            "a[href*='/nachrichtenbox']",
            "a[href*='/meine-anzeigen']",
            "[class*='user-menu']",
            "a:has-text('Meine Anzeigen')",
            "a:has-text('Nachrichten')",
            "[data-testid*='user-menu']",
            "[data-qa*='user-menu']",
        ]
        
        login_successful = False
        for indicator in logged_in_indicators:
            try:
                element = await page.wait_for_selector(indicator, timeout=3000)
                if element:
                    is_visible = await element.is_visible()
                    if is_visible:
                        logger.info(f"✅ Login successful! Found logged-in indicator: {indicator}")
                        login_successful = True
                        break
            except:
                continue
        
        # If still on login page but no logged-in indicators found, check for errors
        # Exclude URLs with login=success (already handled above)
        if ("login" in current_url or "einloggen" in current_url) and "login=success" not in current_url:
            if not login_successful:
                logger.warning("Still on login page, checking if login actually failed...")
                
                # Check for error messages
                error_found = False
                error_selectors = [
                    "[class*='error']",
                    "[class*='alert']",
                    "[class*='warning']",
                    "[id*='error']",
                    "text=/fehler/i",
                    "text=/ungültig/i",
                    "text=/falsch/i",
                ]
                
                for selector in error_selectors:
                    try:
                        error_element = await page.wait_for_selector(selector, timeout=2000)
                        if error_element:
                            error_text = await error_element.text_content()
                            if error_text and len(error_text.strip()) > 0 and "fehler" in error_text.lower():
                                logger.error(f"❌ Login error detected: {error_text[:100]}")
                                await take_screenshot(page, prefix="login_error_detected")
                                error_found = True
                                break
                    except:
                        continue
                
                if error_found:
                    return False
                
                # If no error and no login indicators, might be CAPTCHA or slow redirect
                logger.warning("⚠️ No error found, but still on login page - might be CAPTCHA or slow redirect")
                await take_screenshot(page, prefix="login_still_on_page")
                return False
        
        # Check for logged-in indicators
        logger.info("Checking for logged-in indicators...")
        logged_in = False
        logged_in_selectors = [
            "a[href*='/nachrichtenbox']",
            "[class*='user-menu']",
            "a:has-text('Meine Anzeigen')",
            "[class*='account']",
            "a:has-text('Abmelden')",
        ]
        
        for selector in logged_in_selectors:
            try:
                await page.wait_for_selector(selector, timeout=3000)
                logger.info(f"✅ Found logged-in indicator: {selector}")
                logged_in = True
                break
            except:
                continue
        
        if logged_in:
            logger.info("✅ Login successful")
            return True
        else:
            logger.warning("Could not verify login with selectors, but URL changed - assuming success")
            await take_screenshot(page, prefix="login_unverified")
            return True
        
    except Exception as e:
        logger.error(f"Login failed with error: {e}")
        await take_screenshot(page, prefix="login_error")
        return False

