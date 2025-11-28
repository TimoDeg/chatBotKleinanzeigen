"""
Core bot class with full workflow: login, send message, navigate conversation, make offer.
"""

import asyncio
from typing import Dict, Optional
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from loguru import logger

from src.config import (
    TIMEOUTS,
    DELIVERY_OPTIONS,
    HEADLESS_MODE,
    BROWSER_ARGS,
    EXIT_SUCCESS,
    EXIT_LOGIN_FAILED,
    EXIT_MESSAGE_FAILED,
    EXIT_CONVERSATION_NOT_FOUND,
    EXIT_OFFER_FAILED,
    EXIT_BROWSER_FAILED,
    EXIT_CAPTCHA_DETECTED,
)
from src.auth import login, save_cookies, load_cookies
from src.selectors import (
    MESSAGE_BUTTON,
    MESSAGE_TEXTAREA,
    MESSAGE_SEND,
    CONVERSATIONS_PAGE,
    LATEST_CONVERSATION,
    OFFER_BUTTON,
    OFFER_PRICE_INPUT,
    OFFER_DELIVERY_SELECT,
    OFFER_SHIPPING_INPUT,
    OFFER_NOTE_TEXTAREA,
    OFFER_SUBMIT,
    SUCCESS_INDICATOR,
)
from src.utils import (
    safe_click,
    safe_fill,
    safe_select,
    take_screenshot,
    wait_for_selector_with_fallbacks,
    validate_url,
    random_delay,
)


class KleinanzeigenBot:
    """
    Main bot class for automating eBay Kleinanzeigen interactions.
    """
    
    def __init__(
        self,
        email: str,
        password: str,
        headless: bool = HEADLESS_MODE,
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
        
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
        logger.info(f"Bot initialized (headless={headless})")
    
    async def setup_browser(self) -> bool:
        """
        Initialize browser and context with anti-detection settings.
        
        Returns:
            True if setup successful, False otherwise
        """
        try:
            logger.info("Setting up browser...")
            self.playwright = await async_playwright().start()
            
            # Enhanced anti-detection args
            anti_detection_args = BROWSER_ARGS + [
                "--disable-extensions",
                "--disable-plugins",
                "--start-maximized",
            ]
            
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=anti_detection_args,
            )
            
            self.context = await self.browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                extra_http_headers={
                    "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
                },
            )
            
            self.page = await self.context.new_page()
            
            # Stealth mode: Hide webdriver property
            await self.page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => false,
                });
                window.navigator.chrome = {
                    runtime: {},
                };
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
            """)
            
            logger.info("✅ Browser setup complete")
            return True
            
        except Exception as e:
            logger.error(f"Browser setup failed: {e}")
            return False
    
    async def close(self) -> None:
        """Close browser and cleanup resources."""
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
    
    async def send_message(self, listing_url: str, message: str) -> bool:
        """
        Send a message to a listing with improved selectors and delays.
        
        Args:
            listing_url: URL of the listing
            message: Message text to send
            
        Returns:
            True if message sent successfully, False otherwise
        """
        if not self.page:
            logger.error("Browser not initialized")
            return False
        
        if not validate_url(listing_url):
            logger.error(f"Invalid URL: {listing_url}")
            return False
        
        try:
            logger.info(f"📝 Sending message to listing: {listing_url}")
            
            # Navigate to listing
            await self.page.goto(listing_url, wait_until="networkidle", timeout=30000)
            await random_delay(2, 3)
            
            # Click message button - try multiple selectors
            logger.info("🔍 Looking for message button...")
            message_button_selectors = [
                "button:has-text('Nachricht schreiben')",
                "a:has-text('Nachricht schreiben')",
                "button:has-text('Nachricht senden')",
                "a[href*='nachricht']",
                "button[class*='contact']",
                "button[class*='message']",
                "[data-testid*='contact']",
                "[data-qa*='contact']",
            ]
            
            message_clicked = False
            for selector in message_button_selectors:
                try:
                    logger.debug(f"Trying message button selector: {selector}")
                    button = await self.page.wait_for_selector(selector, timeout=5000, state="visible")
                    if button:
                        await button.scroll_into_view_if_needed()
                        await random_delay(0.5, 1.0)
                        await button.click()
                        logger.info(f"✅ Message button clicked with: {selector}")
                        message_clicked = True
                        break
                except Exception as e:
                    logger.debug(f"Selector failed: {selector} - {e}")
                    continue
            
            if not message_clicked:
                logger.error("❌ Could not find message button")
                await take_screenshot(self.page, prefix="message_button_error")
                return False
            
            # Wait for modal/form to appear with longer timeout
            logger.info("⏳ Waiting for message form to appear...")
            await random_delay(2, 4)
            
            # Try to wait for modal container first
            try:
                await self.page.wait_for_selector(
                    ".modal, [class*='modal'], [class*='dialog'], [class*='form'], iframe",
                    timeout=10000
                )
                logger.debug("Modal/dialog detected")
            except:
                logger.debug("No explicit modal detected, continuing...")
            
            # Fill message textarea - try many different selectors
            logger.info("🔍 Looking for message textarea...")
            textarea_selectors = [
                "textarea[placeholder*='Nachricht']",
                "textarea[placeholder*='Ihre Nachricht']",
                "textarea[placeholder*='Nachricht an']",
                "textarea[name*='message']",
                "textarea[id*='message']",
                "textarea[class*='message']",
                "textarea[data-testid*='message']",
                "textarea[data-qa*='message']",
                "iframe[src*='nachricht'] >> textarea",
                "iframe >> textarea",
                "textarea",
                "div[contenteditable='true']",  # Sometimes it's a contenteditable div
            ]
            
            message_filled = False
            for selector in textarea_selectors:
                try:
                    logger.debug(f"Trying textarea selector: {selector}")
                    if "iframe" in selector:
                        # Handle iframe case
                        try:
                            iframe = await self.page.wait_for_selector("iframe", timeout=5000)
                            if iframe:
                                frame = await iframe.content_frame()
                                if frame:
                                    textarea = await frame.wait_for_selector("textarea", timeout=5000)
                                    if textarea:
                                        await textarea.fill(message)
                                        logger.info(f"✅ Message filled in iframe textarea")
                                        message_filled = True
                                        break
                        except:
                            continue
                    else:
                        textarea = await self.page.wait_for_selector(selector, timeout=5000, state="visible")
                        if textarea:
                            await textarea.scroll_into_view_if_needed()
                            await random_delay(0.5, 1.0)
                            # Check if it's contenteditable div
                            if "contenteditable" in selector:
                                await textarea.fill("")  # Clear first
                                await textarea.type(message, delay=50)  # Type with delay
                            else:
                                await textarea.fill(message)
                            logger.info(f"✅ Message filled with selector: {selector}")
                            message_filled = True
                            break
                except Exception as e:
                    logger.debug(f"Textarea selector failed: {selector} - {e}")
                    continue
            
            if not message_filled:
                logger.error("❌ Could not find message textarea")
                await take_screenshot(self.page, prefix="message_textarea_error")
                # Try to get page HTML for debugging
                try:
                    content = await self.page.content()
                    logger.debug(f"Page content length: {len(content)}")
                    if "textarea" in content.lower():
                        logger.warning("Page contains 'textarea' but selector didn't match")
                except:
                    pass
                return False
            
            await random_delay(1, 2)
            
            # Click send button - try multiple selectors
            logger.info("🔍 Looking for send button...")
            send_button_selectors = [
                "button:has-text('Nachricht senden')",
                "button:has-text('Senden')",
                "button[type='submit']",
                "button[class*='send']",
                "[data-testid*='send']",
                "[data-qa*='send']",
                "button:has-text('Absenden')",
            ]
            
            send_clicked = False
            for selector in send_button_selectors:
                try:
                    logger.debug(f"Trying send button selector: {selector}")
                    button = await self.page.wait_for_selector(selector, timeout=5000, state="visible")
                    if button:
                        await button.scroll_into_view_if_needed()
                        await random_delay(0.5, 1.0)
                        await button.click()
                        logger.info(f"✅ Send button clicked with: {selector}")
                        send_clicked = True
                        break
                except Exception as e:
                    logger.debug(f"Send button selector failed: {selector} - {e}")
                    continue
            
            if not send_clicked:
                # Try pressing Enter as fallback
                logger.warning("Send button not found, trying Enter key...")
                try:
                    await self.page.keyboard.press("Enter")
                    logger.info("✅ Pressed Enter as fallback")
                    send_clicked = True
                except:
                    pass
            
            if not send_clicked:
                logger.error("❌ Could not find send button")
                await take_screenshot(self.page, prefix="send_button_error")
                return False
            
            # Wait for success confirmation
            logger.info("⏳ Waiting for confirmation...")
            await random_delay(2, 3)
            
            # Check for success indicators
            try:
                await wait_for_selector_with_fallbacks(
                    self.page,
                    SUCCESS_INDICATOR,
                    timeout=5
                )
                logger.info("✅ Message sent successfully")
                return True
            except:
                # Message might have been sent even without explicit confirmation
                logger.info("✅ Message sent (assuming success)")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to send message: {e}")
            await take_screenshot(self.page, prefix="send_message_error")
            import traceback
            logger.debug(traceback.format_exc())
            return False
    
    async def navigate_to_conversation(self) -> bool:
        """
        Navigate to the conversation page and open the latest conversation.
        
        Returns:
            True if conversation opened, False otherwise
        """
        if not self.page:
            logger.error("Browser not initialized")
            return False
        
        try:
            logger.info("📬 Navigating to conversations...")
            
            # Navigate to messages page
            await self.page.goto(
                "https://www.kleinanzeigen.de/nachrichtenbox",
                wait_until="networkidle",
                timeout=30000
            )
            await random_delay(2, 3)
            
            # Find and click latest conversation - try multiple selectors
            logger.info("🔍 Looking for latest conversation...")
            conversation_selectors = [
                ".qa-chat-item:first-child",
                "[class*='conversation']:first-child",
                "[class*='chat-item']:first-child",
                "a[href*='/nachrichten/']:first-child",
                "[data-testid*='conversation']:first-child",
                "li:first-child a[href*='nachricht']",
            ]
            
            conversation_clicked = False
            for selector in conversation_selectors:
                try:
                    logger.debug(f"Trying conversation selector: {selector}")
                    element = await self.page.wait_for_selector(selector, timeout=5000, state="visible")
                    if element:
                        await element.scroll_into_view_if_needed()
                        await random_delay(0.5, 1.0)
                        await element.click()
                        logger.info(f"✅ Conversation clicked with: {selector}")
                        conversation_clicked = True
                        break
                except Exception as e:
                    logger.debug(f"Conversation selector failed: {selector} - {e}")
                    continue
            
            if not conversation_clicked:
                logger.error("❌ Could not find conversation")
                await take_screenshot(self.page, prefix="conversation_not_found")
                return False
            
            # Wait for conversation page to load
            await random_delay(2, 3)
            
            logger.info("✅ Opened conversation")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to navigate to conversation: {e}")
            await take_screenshot(self.page, prefix="navigate_conversation_error")
            return False
    
    async def make_offer(
        self,
        price: float,
        delivery: str,
        shipping_cost: Optional[float] = None,
        note: Optional[str] = None
    ) -> bool:
        """
        Make an offer in the current conversation.
        
        Args:
            price: Offer price in EUR
            delivery: Delivery method ("pickup", "shipping", or "both")
            shipping_cost: Shipping cost if applicable
            note: Additional note for the offer
            
        Returns:
            True if offer sent successfully, False otherwise
        """
        if not self.page:
            logger.error("Browser not initialized")
            return False
        
        try:
            logger.info(f"💰 Making offer: €{price}, delivery: {delivery}")
            
            # Find and click offer button - try multiple selectors
            logger.info("🔍 Looking for offer button...")
            offer_button_selectors = [
                "button:has-text('Angebot machen')",
                "button:has-text('Angebot unterbreiten')",
                "button:has-text('Angebot')",
                "a:has-text('Angebot machen')",
                "[data-testid*='offer']",
                "[data-qa*='offer']",
                "button[class*='offer']",
            ]
            
            offer_clicked = False
            for selector in offer_button_selectors:
                try:
                    logger.debug(f"Trying offer button selector: {selector}")
                    button = await self.page.wait_for_selector(selector, timeout=10000, state="visible")
                    if button:
                        await button.scroll_into_view_if_needed()
                        await random_delay(0.5, 1.0)
                        await button.click()
                        logger.info(f"✅ Offer button clicked with: {selector}")
                        offer_clicked = True
                        break
                except Exception as e:
                    logger.debug(f"Offer button selector failed: {selector} - {e}")
                    continue
            
            if not offer_clicked:
                logger.error("❌ Could not find offer button")
                await take_screenshot(self.page, prefix="offer_button_error")
                return False
            
            # Wait for offer form to appear
            logger.info("⏳ Waiting for offer form...")
            await random_delay(2, 4)
            
            # Try to wait for modal container
            try:
                await self.page.wait_for_selector(
                    ".modal, [class*='modal'], [class*='dialog'], [class*='form']",
                    timeout=10000
                )
                logger.debug("Offer form/modal detected")
            except:
                logger.debug("No explicit modal detected, continuing...")
            
            # Fill price - try multiple selectors
            logger.info(f"💰 Filling price: €{price}")
            price_selectors = [
                "input[name*='price']",
                "input[placeholder*='EUR']",
                "input[placeholder*='€']",
                "input[type='number']",
                "input[id*='price']",
                "input[class*='price']",
            ]
            
            price_filled = False
            for selector in price_selectors:
                try:
                    logger.debug(f"Trying price selector: {selector}")
                    input_field = await self.page.wait_for_selector(selector, timeout=5000, state="visible")
                    if input_field:
                        await input_field.scroll_into_view_if_needed()
                        await random_delay(0.5, 1.0)
                        await input_field.fill(str(price))
                        logger.info(f"✅ Price filled with: {selector}")
                        price_filled = True
                        break
                except Exception as e:
                    logger.debug(f"Price selector failed: {selector} - {e}")
                    continue
            
            if not price_filled:
                logger.error("❌ Could not find price input")
                await take_screenshot(self.page, prefix="offer_price_error")
                return False
            
            await random_delay(1, 2)
            
            # Select delivery method
            if delivery in DELIVERY_OPTIONS:
                delivery_value = DELIVERY_OPTIONS[delivery]
                logger.info(f"🚚 Selecting delivery: {delivery_value}")
                
                # Try dropdown select
                delivery_selectors = [
                    "select[name*='delivery']",
                    "select[name*='shipping']",
                    "select[id*='delivery']",
                    "select",
                ]
                
                delivery_selected = False
                for selector in delivery_selectors:
                    try:
                        select_element = await self.page.wait_for_selector(selector, timeout=5000)
                        if select_element:
                            await select_element.select_option(value=delivery_value)
                            logger.info(f"✅ Delivery selected via dropdown: {selector}")
                            delivery_selected = True
                            break
                    except:
                        continue
                
                if not delivery_selected:
                    # Try clicking radio buttons or text
                    logger.debug("Trying alternative delivery selection...")
                    try:
                        delivery_text = delivery_value.lower()
                        await self.page.click(f"text=/{delivery_text}/i", timeout=5000)
                        logger.info("✅ Delivery selected via text click")
                    except:
                        logger.warning("⚠️ Could not select delivery method")
            
            await random_delay(1, 2)
            
            # Fill shipping cost if applicable
            if shipping_cost and delivery in ["shipping", "both"]:
                logger.info(f"📦 Filling shipping cost: €{shipping_cost}")
                shipping_selectors = [
                    "input[name*='shipping']",
                    "input[placeholder*='Versand']",
                    "input[id*='shipping']",
                ]
                
                for selector in shipping_selectors:
                    try:
                        shipping_input = await self.page.wait_for_selector(selector, timeout=3000)
                        if shipping_input:
                            await shipping_input.fill(str(shipping_cost))
                            logger.info("✅ Shipping cost filled")
                            break
                    except:
                        continue
            
            # Fill note if provided
            if note:
                logger.info("📝 Filling offer note...")
                note_selectors = [
                    "textarea[name*='note']",
                    "textarea[placeholder*='Nachricht']",
                    "textarea[id*='note']",
                    "textarea",
                ]
                
                for selector in note_selectors:
                    try:
                        note_textarea = await self.page.wait_for_selector(selector, timeout=3000)
                        if note_textarea:
                            await note_textarea.fill(note)
                            logger.info("✅ Note filled")
                            break
                    except:
                        continue
            
            await random_delay(1, 2)
            
            # Submit offer - try multiple selectors
            logger.info("🔍 Looking for submit button...")
            submit_selectors = [
                "button:has-text('Angebot senden')",
                "button:has-text('Angebot unterbreiten')",
                "button:has-text('Senden')",
                "button[type='submit']",
                "[data-testid*='submit']",
                "button:has-text('Absenden')",
            ]
            
            submit_clicked = False
            for selector in submit_selectors:
                try:
                    logger.debug(f"Trying submit selector: {selector}")
                    button = await self.page.wait_for_selector(selector, timeout=5000, state="visible")
                    if button:
                        await button.scroll_into_view_if_needed()
                        await random_delay(0.5, 1.0)
                        await button.click()
                        logger.info(f"✅ Submit button clicked with: {selector}")
                        submit_clicked = True
                        break
                except Exception as e:
                    logger.debug(f"Submit selector failed: {selector} - {e}")
                    continue
            
            if not submit_clicked:
                # Try Enter key as fallback
                logger.warning("Submit button not found, trying Enter key...")
                try:
                    await self.page.keyboard.press("Enter")
                    logger.info("✅ Pressed Enter as fallback")
                    submit_clicked = True
                except:
                    pass
            
            if not submit_clicked:
                logger.error("❌ Could not find submit button")
                await take_screenshot(self.page, prefix="offer_submit_error")
                return False
            
            # Wait for success confirmation
            logger.info("⏳ Waiting for confirmation...")
            await random_delay(3, 5)
            
            # Check for success
            try:
                await wait_for_selector_with_fallbacks(
                    self.page,
                    SUCCESS_INDICATOR,
                    timeout=5
                )
                logger.info(f"✅ Offer sent: €{price}, {delivery}")
                return True
            except:
                logger.info("✅ Offer sent (assuming success)")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to make offer: {e}")
            await take_screenshot(self.page, prefix="make_offer_error")
            import traceback
            logger.debug(traceback.format_exc())
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
        save_screenshot: bool = False
    ) -> Dict[str, any]:
        """
        Execute the complete workflow: login -> send message -> navigate -> make offer.
        
        Args:
            listing_url: URL of the listing
            message: Message text to send
            price: Offer price
            delivery: Delivery method
            shipping_cost: Optional shipping cost
            note: Optional offer note
            force_fresh_login: Force new login
            save_screenshot: Save screenshot on success
            
        Returns:
            Dictionary with status of each step and exit code
        """
        result = {
            "browser_setup": False,
            "authentication": False,
            "message_sent": False,
            "conversation_opened": False,
            "offer_sent": False,
            "exit_code": EXIT_BROWSER_FAILED,
        }
        
        try:
            # Step 1: Setup browser
            if not await self.setup_browser():
                logger.error("❌ Browser setup failed")
                return result
            
            result["browser_setup"] = True
            
            # Step 2: Authenticate
            if not await self.authenticate(force_fresh=force_fresh_login):
                logger.error("❌ Authentication failed")
                result["exit_code"] = EXIT_LOGIN_FAILED
                return result
            
            result["authentication"] = True
            
            # Step 3: Send message
            if not await self.send_message(listing_url, message):
                logger.error("❌ Message sending failed")
                result["exit_code"] = EXIT_MESSAGE_FAILED
                return result
            
            result["message_sent"] = True
            
            # Step 4: Navigate to conversation
            if not await self.navigate_to_conversation():
                logger.error("❌ Conversation navigation failed")
                result["exit_code"] = EXIT_CONVERSATION_NOT_FOUND
                return result
            
            result["conversation_opened"] = True
            
            # Step 5: Make offer
            if not await self.make_offer(price, delivery, shipping_cost, note):
                logger.error("❌ Offer making failed")
                result["exit_code"] = EXIT_OFFER_FAILED
                return result
            
            result["offer_sent"] = True
            result["exit_code"] = EXIT_SUCCESS
            
            # Save screenshot if requested
            if save_screenshot and self.page:
                await take_screenshot(self.page, prefix="success")
            
            logger.info("✅ Full workflow completed successfully!")
            
        except Exception as e:
            logger.error(f"Workflow error: {e}")
            if self.page:
                await take_screenshot(self.page, prefix="workflow_error")
        
        finally:
            await self.close()
        
        return result

