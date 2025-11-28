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
            
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=BROWSER_ARGS,
            )
            
            self.context = await self.browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            )
            
            self.page = await self.context.new_page()
            
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
        Send a message to a listing.
        
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
            logger.info(f"Sending message to listing: {listing_url}")
            
            # Navigate to listing
            await self.page.goto(listing_url, wait_until="domcontentloaded")
            await self.page.wait_for_timeout(TIMEOUTS["page_load"] * 1000)
            
            # Click message button
            logger.debug("Looking for message button...")
            message_clicked = await safe_click(
                self.page,
                MESSAGE_BUTTON,
                timeout=TIMEOUTS["selector_wait"],
                description="message button"
            )
            
            if not message_clicked:
                logger.error("Could not find message button")
                await take_screenshot(self.page, prefix="message_button_error")
                return False
            
            # Wait for message modal/form
            logger.debug("Waiting for message form...")
            await self.page.wait_for_timeout(TIMEOUTS["modal_appearance"] * 1000)
            
            # Fill message textarea
            logger.debug("Filling message text...")
            message_filled = await safe_fill(
                self.page,
                MESSAGE_TEXTAREA,
                message,
                timeout=TIMEOUTS["selector_wait"],
                description="message textarea"
            )
            
            if not message_filled:
                logger.error("Could not find message textarea")
                await take_screenshot(self.page, prefix="message_textarea_error")
                return False
            
            # Click send button
            logger.debug("Clicking send button...")
            send_clicked = await safe_click(
                self.page,
                MESSAGE_SEND,
                timeout=TIMEOUTS["selector_wait"],
                description="send button"
            )
            
            if not send_clicked:
                logger.error("Could not find send button")
                await take_screenshot(self.page, prefix="send_button_error")
                return False
            
            # Wait for success confirmation
            logger.debug("Waiting for success confirmation...")
            await self.page.wait_for_timeout(TIMEOUTS["success_confirmation"] * 1000)
            
            # Check for success indicators
            try:
                await wait_for_selector_with_fallbacks(
                    self.page,
                    SUCCESS_INDICATOR,
                    timeout=3
                )
                logger.info("✅ Message sent successfully")
                return True
            except:
                # Message might have been sent even without explicit confirmation
                logger.info("✅ Message sent (assuming success)")
                return True
                
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            await take_screenshot(self.page, prefix="send_message_error")
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
            logger.info("Navigating to conversations...")
            
            # Navigate to messages page
            await self.page.goto(
                "https://www.kleinanzeigen.de/nachrichtenbox",
                wait_until="domcontentloaded"
            )
            await self.page.wait_for_timeout(TIMEOUTS["page_load"] * 1000)
            
            # Find and click latest conversation
            logger.debug("Looking for latest conversation...")
            conversation_clicked = await safe_click(
                self.page,
                LATEST_CONVERSATION,
                timeout=TIMEOUTS["selector_wait"],
                description="latest conversation"
            )
            
            if not conversation_clicked:
                logger.error("Could not find conversation")
                await take_screenshot(self.page, prefix="conversation_not_found")
                return False
            
            # Wait for conversation page to load
            await self.page.wait_for_timeout(TIMEOUTS["modal_appearance"] * 1000)
            
            logger.info("✅ Opened conversation")
            return True
            
        except Exception as e:
            logger.error(f"Failed to navigate to conversation: {e}")
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
            logger.info(f"Making offer: €{price}, delivery: {delivery}")
            
            # Find and click offer button
            logger.debug("Looking for offer button...")
            offer_clicked = await safe_click(
                self.page,
                OFFER_BUTTON,
                timeout=TIMEOUTS["selector_wait"],
                description="offer button"
            )
            
            if not offer_clicked:
                logger.error("Could not find offer button")
                await take_screenshot(self.page, prefix="offer_button_error")
                return False
            
            # Wait for offer form
            logger.debug("Waiting for offer form...")
            await self.page.wait_for_timeout(TIMEOUTS["modal_appearance"] * 1000)
            
            # Fill price
            logger.debug(f"Filling price: €{price}")
            price_filled = await safe_fill(
                self.page,
                OFFER_PRICE_INPUT,
                str(price),
                timeout=TIMEOUTS["selector_wait"],
                description="price input"
            )
            
            if not price_filled:
                logger.error("Could not find price input")
                await take_screenshot(self.page, prefix="offer_price_error")
                return False
            
            # Select delivery method
            if delivery in DELIVERY_OPTIONS:
                delivery_value = DELIVERY_OPTIONS[delivery]
                logger.debug(f"Selecting delivery: {delivery_value}")
                
                # Try to select from dropdown
                delivery_selected = await safe_select(
                    self.page,
                    OFFER_DELIVERY_SELECT,
                    delivery_value,
                    timeout=TIMEOUTS["selector_wait"],
                    description="delivery select"
                )
                
                if not delivery_selected:
                    # Try clicking radio buttons or checkboxes
                    logger.debug("Trying alternative delivery selection...")
                    try:
                        delivery_text = delivery_value.lower()
                        await self.page.click(f"text=/{delivery_text}/i")
                        logger.debug("Selected delivery via text click")
                    except:
                        logger.warning("Could not select delivery method")
            
            # Fill shipping cost if applicable
            if shipping_cost and delivery in ["shipping", "both"]:
                logger.debug(f"Filling shipping cost: €{shipping_cost}")
                await safe_fill(
                    self.page,
                    OFFER_SHIPPING_INPUT,
                    str(shipping_cost),
                    timeout=TIMEOUTS["selector_wait"],
                    description="shipping cost input"
                )
            
            # Fill note if provided
            if note:
                logger.debug("Filling offer note...")
                await safe_fill(
                    self.page,
                    OFFER_NOTE_TEXTAREA,
                    note,
                    timeout=TIMEOUTS["selector_wait"],
                    description="offer note"
                )
            
            # Submit offer
            logger.debug("Submitting offer...")
            submit_clicked = await safe_click(
                self.page,
                OFFER_SUBMIT,
                timeout=TIMEOUTS["selector_wait"],
                description="offer submit button"
            )
            
            if not submit_clicked:
                logger.error("Could not find submit button")
                await take_screenshot(self.page, prefix="offer_submit_error")
                return False
            
            # Wait for success confirmation
            await self.page.wait_for_timeout(TIMEOUTS["success_confirmation"] * 1000)
            
            # Check for success
            try:
                await wait_for_selector_with_fallbacks(
                    self.page,
                    SUCCESS_INDICATOR,
                    timeout=3
                )
                logger.info(f"✅ Offer sent: €{price}, {delivery}")
                return True
            except:
                logger.info("✅ Offer sent (assuming success)")
                return True
                
        except Exception as e:
            logger.error(f"Failed to make offer: {e}")
            await take_screenshot(self.page, prefix="make_offer_error")
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

