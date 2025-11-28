"""
Authentication and session management with cookie persistence.
"""

import json
import os
from typing import Optional
from pathlib import Path

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
from src.utils import safe_click, safe_fill, take_screenshot


async def save_cookies(context: BrowserContext) -> bool:
    """
    Save browser cookies to JSON file for persistent sessions.
    
    Args:
        context: Playwright browser context
        
    Returns:
        True if saved successfully, False otherwise
    """
    try:
        cookies = await context.cookies()
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(COOKIES_PATH) or ".", exist_ok=True)
        
        with open(COOKIES_PATH, "w", encoding="utf-8") as f:
            json.dump(cookies, f, indent=2)
        
        logger.info(f"Cookies saved to {COOKIES_PATH}")
        return True
    except Exception as e:
        logger.error(f"Failed to save cookies: {e}")
        return False


async def load_cookies(context: BrowserContext) -> bool:
    """
    Load cookies from JSON file if it exists.
    
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
        
        await context.add_cookies(cookies)
        logger.info(f"Cookies loaded from {COOKIES_PATH}")
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
        
        # Navigate to Kleinanzeigen
        logger.debug("Navigating to Kleinanzeigen...")
        await page.goto("https://www.kleinanzeigen.de", wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)  # Wait for page to settle
        
        # Accept cookie banner
        await accept_cookie_banner(page)
        
        # Check if already logged in (by checking for user menu or messages link)
        if not force_fresh:
            try:
                # Check for logged-in indicators
                logged_in_indicators = [
                    "a[href*='/nachrichtenbox']",
                    "[class*='user-menu']",
                    "a:has-text('Meine Anzeigen')",
                ]
                
                for indicator in logged_in_indicators:
                    try:
                        await page.wait_for_selector(indicator, timeout=3000)
                        logger.info("Already logged in (cookies valid)")
                        return True
                    except:
                        continue
            except:
                pass
        
        # Try to find and click login link, but don't wait too long
        logger.info("Looking for login link...")
        login_clicked = False
        
        # Try clicking login link with shorter timeout
        try:
            login_clicked = await safe_click(
                page,
                LOGIN_LINK,
                timeout=5,  # Short timeout
                description="login link"
            )
        except Exception as e:
            logger.debug(f"Login link click failed: {e}")
        
        # If login link not found, navigate directly to login page
        if not login_clicked:
            logger.info("Login link not found, navigating directly to login page...")
            try:
                await page.goto("https://www.kleinanzeigen.de/m-einloggen.html", wait_until="domcontentloaded", timeout=15000)
                await page.wait_for_timeout(3000)
                logger.info("Navigated to login page")
            except Exception as e:
                logger.error(f"Failed to navigate to login page: {e}")
                await take_screenshot(page, prefix="login_navigation_error")
                return False
        
        # Fill email - try multiple approaches
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
            if "login" not in current_url.lower() and "einloggen" not in current_url.lower():
                logger.warning("Not on login page, might already be logged in or redirected")
                return True
            return False
        
        # Fill password - try multiple approaches
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
        
        # Submit login form - try multiple approaches
        logger.info("Submitting login form...")
        submit_clicked = await safe_click(
            page,
            LOGIN_SUBMIT,
            timeout=10,
            description="login submit button"
        )
        
        if not submit_clicked:
            # Try alternative: press Enter on password field or find any submit button
            logger.warning("Standard submit button not found, trying alternatives...")
            try:
                # Try pressing Enter on password field
                password_input = await page.wait_for_selector("input[type='password']", timeout=3000)
                if password_input:
                    await password_input.press("Enter")
                    logger.info("Pressed Enter on password field")
                    submit_clicked = True
            except:
                # Try finding any button with "Anmelden" text
                try:
                    submit_button = await page.wait_for_selector("button:has-text('Anmelden'), input[value*='Anmelden']", timeout=3000)
                    if submit_button:
                        await submit_button.click()
                        logger.info("Clicked alternative submit button")
                        submit_clicked = True
                except:
                    pass
        
        if not submit_clicked:
            logger.error("Failed to find submit button")
            await take_screenshot(page, prefix="login_submit_error")
            # Try pressing Enter anyway
            try:
                await page.keyboard.press("Enter")
                logger.info("Pressed Enter as last resort")
                await page.wait_for_timeout(2000)
            except:
                pass
        
        # Wait for redirect or login completion
        logger.info("Waiting for login to complete...")
        await page.wait_for_timeout(5000)
        
        # Wait for navigation or page change
        try:
            await page.wait_for_load_state("networkidle", timeout=10000)
        except:
            logger.debug("Network idle timeout, continuing...")
        
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
        
        # If we're still on login page, login likely failed
        if "login" in current_url or "einloggen" in current_url:
            logger.warning("Still on login page, checking if login actually failed...")
            # Check if there's an error message
            try:
                error_element = await page.wait_for_selector(
                    "[class*='error'], [class*='alert'], text=/fehler|ungültig|falsch/i",
                    timeout=3000
                )
                if error_element:
                    error_text = await error_element.text_content()
                    logger.error(f"Login error detected: {error_text}")
                    await take_screenshot(page, prefix="login_error_detected")
                    return False
            except:
                pass
            
            # If no error, might be a different login page layout
            logger.warning("No error found, but still on login page")
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

