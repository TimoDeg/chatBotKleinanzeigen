"""
Core bot class with full workflow: login, send message, navigate conversation, make offer.
"""

import json
import asyncio
from pathlib import Path
from typing import Dict, Optional
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from loguru import logger

from src.config import (
    TIMEOUTS,
    DELIVERY_OPTIONS,
    BROWSER_ARGS,
    EXIT_SUCCESS,
    EXIT_LOGIN_FAILED,
    EXIT_MESSAGE_FAILED,
    EXIT_CONVERSATION_NOT_FOUND,
    EXIT_OFFER_FAILED,
    EXIT_BROWSER_FAILED,
    EXIT_CAPTCHA_DETECTED,
    COOKIES_PATH,
)
from src.auth import login, save_cookies, load_cookies
from src.selectors import (
    MESSAGE_BUTTON_SELECTORS,
    MESSAGE_TEXTAREA_SELECTORS,
    MESSAGE_SEND_SELECTORS,
    CONVERSATIONS_PAGE_SELECTORS,
    LATEST_CONVERSATION_SELECTORS,
    OFFER_BUTTON_SELECTORS,
    OFFER_PRICE_INPUT_SELECTORS,
    OFFER_DELIVERY_SELECT_SELECTORS,
    OFFER_SHIPPING_INPUT_SELECTORS,
    OFFER_NOTE_TEXTAREA_SELECTORS,
    OFFER_SUBMIT_SELECTORS,
    SUCCESS_INDICATOR_SELECTORS,
)
from src.utils import (
    find_element_with_fallbacks,
    random_delay,
    take_screenshot,
    validate_url,
)


class KleinanzeigenBot:
    """
    Main bot class for automating eBay Kleinanzeigen interactions.
    """
    
    def __init__(
        self,
        email: str,
        password: str,
        headless: bool = True,
        timeout: int = 30
    ):
        """
        Initialize the bot.
        
        Args:
            email: Kleinanzeigen email
            password: Kleinanzeigen password
            headless: Run browser in headless mode
            timeout: Default timeout for actions
        """
        self.email = email
        self.password = password
        self.headless = headless
        self.timeout = timeout
        self.debug_mode = False
        
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.cookies_file = Path(COOKIES_PATH)
        
        logger.info(f"Bot initialized (headless={headless})")
    
    async def _random_delay(self, min_s: float = 1, max_s: float = 3):
        """Wrapper for random_delay"""
        await random_delay(min_s, max_s)
    
    async def _take_screenshot(self, prefix: str = "error"):
        """Wrapper for take_screenshot"""
        if self.page:
            await take_screenshot(self.page, prefix=prefix)
    
    async def setup_browser(self) -> bool:
        """
        Initialize browser and context with enhanced anti-detection settings.
        
        Returns:
            True if setup successful, False otherwise
        """
        try:
            logger.info("Setting up browser with anti-detection...")
            self.playwright = await async_playwright().start()
            
            # Enhanced anti-detection args
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-blink-features=AutomationControlled",  # WICHTIG
                    "--disable-extensions",
                    "--disable-plugins",
                    "--start-maximized",
                ],
            )
            
            self.context = await self.browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                extra_http_headers={
                    "Accept-Language": "de-DE,de;q=0.9,de;q=0.8",
                },
            )
            
            # Stealth-Mode JavaScript
            await self.context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => false,
                });
            """)
            
            # Load cookies if available
            if self.cookies_file.exists():
                try:
                    with open(self.cookies_file) as f:
                        cookies = json.load(f)
                        await self.context.add_cookies(cookies)
                        logger.info("✅ Cookies geladen")
                except Exception as e:
                    logger.warning(f"⚠️ Cookie-Load fehlgeschlagen: {e}")
            
            self.page = await self.context.new_page()
            logger.info("✅ Browser setup erfolgreich")
            return True
            
        except Exception as e:
            logger.error(f"❌ Browser setup fehlgeschlagen: {e}")
            return False
    
    async def close(self) -> None:
        """Close browser and cleanup"""
        try:
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            logger.info("Browser closed")
        except Exception as e:
            logger.error(f"Error closing browser: {e}")
    
    async def authenticate(self, force_fresh: bool = False) -> bool:
        """
        Authenticate user (load cookies or perform login).
        
        Args:
            force_fresh: Force new login even if cookies exist
            
        Returns:
            True if authenticated, False otherwise
        """
        if not self.page:
            logger.error("Browser not initialized")
            return False
        
        # Try to load cookies first
        if not force_fresh:
            cookies_loaded = await load_cookies(self.context)
            if cookies_loaded:
                # Navigate to check if cookies are valid
                await self.page.goto("https://www.kleinanzeigen.de", wait_until="domcontentloaded")
                await self.page.wait_for_timeout(2000)
                
                # Check if already logged in
                try:
                    await self.page.wait_for_selector(
                        "a[href*='/nachrichtenbox'], [class*='user-menu']",
                        timeout=3000
                    )
                    logger.info("✅ Authenticated via cookies")
                    return True
                except:
                    logger.debug("Cookies invalid, performing fresh login...")
        
        # Perform login
        login_success = await login(self.page, self.email, self.password, force_fresh)
        
        if login_success:
            # Save cookies for next time
            await save_cookies(self.context)
            return True
        else:
            logger.error("❌ Authentication failed")
            return False
    
    async def send_message(self, listing_url: str, message: str) -> Dict:
        """
        Sendet Nachricht und returnt Conversation-Info
        
        Args:
            listing_url: URL of the listing
            message: Message text to send
            
        Returns:
            Dict with success status and conversation info
        """
        conversation_data = {
            "success": False,
            "message_sent": False,
            "conversation_url": None,
            "conversation_id": None
        }
        
        if not self.page:
            logger.error("Browser not initialized")
            return conversation_data
        
        if not validate_url(listing_url):
            logger.error(f"Invalid URL: {listing_url}")
            return conversation_data
        
        try:
            logger.info(f"📝 Sending message to listing: {listing_url}")
            
            # Navigate to listing
            await self.page.goto(listing_url, wait_until="networkidle")
            await self._random_delay(1, 2)
            
            # Message Button mit Fallbacks
            msg_btn = await find_element_with_fallbacks(
                self.page,
                MESSAGE_BUTTON_SELECTORS,
                timeout=10000,
                logger_instance=logger
            )
            if not msg_btn:
                logger.error("Message Button nicht gefunden")
                await self._take_screenshot("error_message_button")
                return conversation_data
            
            await msg_btn.click()
            await self._random_delay(2, 3)
            
            # Textarea mit Fallbacks
            textarea = await find_element_with_fallbacks(
                self.page,
                MESSAGE_TEXTAREA_SELECTORS,
                timeout=5000,
                logger_instance=logger
            )
            if not textarea:
                logger.error("Message Textarea nicht gefunden")
                await self._take_screenshot("error_textarea")
                return conversation_data
            
            await textarea.fill(message)
            await self._random_delay(1, 2)
            
            # Send Button mit Fallbacks
            send_btn = await find_element_with_fallbacks(
                self.page,
                MESSAGE_SEND_SELECTORS,
                timeout=5000,
                logger_instance=logger
            )
            if not send_btn:
                logger.error("Send Button nicht gefunden")
                await self._take_screenshot("error_send_button")
                return conversation_data
            
            await send_btn.click()
            await self.page.wait_for_timeout(2000)
            
            logger.info("✅ Nachricht erfolgreich gesendet")
            conversation_data["message_sent"] = True
            conversation_data["success"] = True
            
            # Nach Nachricht-Versand: Schaue welche URL wir haben
            current_url = self.page.url
            logger.info(f"Nach Nachricht: URL = {current_url}")
            
            # Versuche Conversation-Link zu finden
            conv_link = await find_element_with_fallbacks(
                self.page,
                [
                    "a[href*='nachrichtenbox']",
                    "a[href*='/messages/']",
                    "button:has-text('Nachricht')"
                ],
                timeout=5000,
                logger_instance=logger
            )
            
            if conv_link:
                conv_url = await conv_link.get_attribute("href")
                conversation_data["conversation_url"] = conv_url
                logger.info(f"✅ Conversation-Link gefunden: {conv_url}")
            
            return conversation_data
                
        except Exception as e:
            logger.error(f"❌ send_message exception: {e}")
            await self._take_screenshot("error_send_message_exception")
            return conversation_data
    
    async def navigate_to_conversation(self, conversation_url: str = None) -> bool:
        """Navigiere zur Conversation"""
        try:
            if not conversation_url:
                # Fallback: Gehe zur Nachrichtenbox
                conversation_url = "https://www.kleinanzeigen.de/nachrichtenbox"
        
            logger.info(f"📬 Navigiere zu: {conversation_url}")
            await self.page.goto(conversation_url, wait_until="networkidle")
            await self._random_delay(2, 3)
            
            # Versuche neueste Conversation zu finden
            latest_conv = await find_element_with_fallbacks(
                self.page,
                LATEST_CONVERSATION_SELECTORS,
                timeout=5000,
                logger_instance=logger
            )
            
            if latest_conv:
                await latest_conv.click()
                await self._random_delay(2, 3)
                logger.info("✅ Conversation geöffnet")
                return True
            else:
                logger.error("Neueste Conversation nicht gefunden")
                await self._take_screenshot("error_conversation_not_found")
                return False
                
        except Exception as e:
            logger.error(f"❌ navigate_to_conversation fehlgeschlagen: {e}")
            await self._take_screenshot("error_navigate_conversation")
            return False
    
    async def make_offer(
        self,
        price: float,
        delivery: str,
        shipping_cost: Optional[float] = None,
        note: Optional[str] = None
    ) -> bool:
        """Macht Angebot mit Fallback-Selektoren"""
        try:
            logger.info(f"💰 Mache Angebot: €{price}, {delivery}")
            await self._random_delay(2, 3)
            
            # 1. Offer-Button finden
            offer_btn = await find_element_with_fallbacks(
                self.page,
                OFFER_BUTTON_SELECTORS,
                timeout=15000,
                logger_instance=logger
            )
            
            if not offer_btn:
                logger.error("Angebot-Button nicht gefunden")
                await self._take_screenshot("error_offer_button_not_found")
                return False
            
            await offer_btn.click()
            await self._random_delay(2, 3)
            
            # 2. Preis-Input
            price_input = await find_element_with_fallbacks(
                self.page,
                OFFER_PRICE_INPUT_SELECTORS,
                timeout=5000,
                logger_instance=logger
            )
            
            if not price_input:
                logger.error("Preis-Input nicht gefunden")
                await self._take_screenshot("error_price_input")
                return False
            
            await price_input.fill(str(price))
            await self._random_delay(1, 2)
            logger.info(f"✅ Preis eingegeben: €{price}")
            
            # 3. Lieferart-Select
            try:
                delivery_select = await find_element_with_fallbacks(
                    self.page,
                    OFFER_DELIVERY_SELECT_SELECTORS,
                    timeout=5000,
                    logger_instance=logger
                )
                
                if delivery_select:
                    delivery_value = {
                        "pickup": "Abholung",
                        "shipping": "Versand",
                        "both": "Beides"
                    }.get(delivery, delivery)
                    
                    await delivery_select.select_option(label=delivery_value)
                    await self._random_delay(1, 2)
                    logger.info(f"✅ Lieferart gewählt: {delivery_value}")
            except Exception as e:
                logger.warning(f"⚠️ Lieferart konnte nicht gesetzt werden: {e}")
            
            # 4. Versandkosten (optional)
            if shipping_cost and delivery in ["shipping", "both"]:
                try:
                    shipping_input = await find_element_with_fallbacks(
                        self.page,
                        OFFER_SHIPPING_INPUT_SELECTORS,
                        timeout=5000,
                        logger_instance=logger
                    )
                    
                    if shipping_input:
                        await shipping_input.fill(str(shipping_cost))
                        await self._random_delay(1, 2)
                        logger.info(f"✅ Versandkosten eingegeben: €{shipping_cost}")
                except Exception as e:
                    logger.warning(f"⚠️ Versandkosten konnte nicht gesetzt werden: {e}")
            
            # 5. Notiz (optional)
            if note:
                try:
                    note_textarea = await find_element_with_fallbacks(
                        self.page,
                        OFFER_NOTE_TEXTAREA_SELECTORS,
                        timeout=5000,
                        logger_instance=logger
                    )
                    
                    if note_textarea:
                        await note_textarea.fill(note)
                        await self._random_delay(1, 2)
                        logger.info("✅ Notiz hinzugefügt")
                except Exception as e:
                    logger.warning(f"⚠️ Notiz konnte nicht hinzugefügt werden: {e}")
            
            # 6. Angebot absenden
            await self._random_delay(2, 3)
            
            submit_btn = await find_element_with_fallbacks(
                self.page,
                OFFER_SUBMIT_SELECTORS,
                timeout=5000,
                logger_instance=logger
            )
            
            if not submit_btn:
                logger.error("Submit-Button nicht gefunden")
                await self._take_screenshot("error_submit_button")
                return False
            
            await submit_btn.click()
            await self.page.wait_for_timeout(3000)
            
            logger.info("✅ Angebot erfolgreich gesendet")
            return True
                
        except Exception as e:
            logger.error(f"❌ make_offer exception: {e}")
            await self._take_screenshot("error_make_offer_exception")
            return False
    
    async def execute_full_workflow(
        self,
        listing_url: str,
        message: str,
        price: float,
        delivery: str,
        shipping_cost: Optional[float] = None,
        note: Optional[str] = None,
        force_fresh_login: bool = False,
        save_screenshot: bool = False,
        debug_mode: bool = False
    ) -> Dict:
        """Kompletter Workflow mit robustem Error-Handling"""
        result = {
            "success": False,
            "steps_completed": [],
            "errors": []
        }
        
        try:
            # Step 1: Browser Setup
            if not await self.setup_browser():
                result["errors"].append("Browser setup fehlgeschlagen")
                return result
            result["steps_completed"].append("browser_setup")
            
            # Step 2: Login
            if not await self.authenticate(force_fresh=force_fresh_login):
                result["errors"].append("Login fehlgeschlagen")
                return result
            result["steps_completed"].append("login")
            
            # Step 3: Send Message
            msg_result = await self.send_message(listing_url, message)
            if not msg_result.get("message_sent"):
                result["errors"].append("Message senden fehlgeschlagen")
                return result
            result["steps_completed"].append("message_sent")
            
            # Step 4: Navigate to Conversation
            conv_url = msg_result.get("conversation_url")
            if not await self.navigate_to_conversation(conv_url):
                result["errors"].append("Conversation navigation fehlgeschlagen")
                return result
            result["steps_completed"].append("conversation_opened")
            
            # Step 5: Make Offer
            if not await self.make_offer(price, delivery, shipping_cost, note):
                result["errors"].append("Angebot machen fehlgeschlagen")
                return result
            result["steps_completed"].append("offer_made")
            
            # Success!
            result["success"] = True
            logger.info(f"✅✅✅ KOMPLETTER WORKFLOW ERFOLGREICH ✅✅✅")
            
        except Exception as e:
            logger.error(f"❌ Workflow exception: {e}")
            result["errors"].append(str(e))
        
        finally:
            await self.close()
        
        return result

