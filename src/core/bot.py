"""
Main bot orchestrator with human-like behavior and anti-detection.
"""

from typing import Dict, Optional

from playwright.async_api import Page
from loguru import logger

from src.core.browser import BrowserManager
from src.core.session import SessionManager
from src.stealth.human_behavior import HumanBehavior
# from src.stealth.vpn import vpn  # VPN disabled
from src.modules.auth import login
from src.modules.messaging import MessageManager
from src.modules.offers import OfferManager
from src.modules.navigation import NavigationManager
from src.config.settings import settings


class KleinanzeigenBot:
    """
    Main bot orchestrator with human-like behavior and anti-detection.
    """
    
    def __init__(self, email: str, password: str, headless: Optional[bool] = None):
        """
        Initialize KleinanzeigenBot.
        
        Args:
            email: User email
            password: User password
            headless: Override headless setting (None = use settings default)
        """
        self.email = email
        self.password = password
        
        # Use provided headless or fall back to settings
        headless_mode = headless if headless is not None else settings.headless
        self.browser_manager = BrowserManager(headless=headless_mode)
        self.session_manager = SessionManager(settings.cookies_path)
        self.human = HumanBehavior()
        
        self.browser = None
        self.context = None
        self.page: Optional[Page] = None
        self.message_manager: Optional[MessageManager] = None
        self.offer_manager: Optional[OfferManager] = None
        self.nav_manager: Optional[NavigationManager] = None
        self.cookies_loaded: bool = False
    
    async def setup(self) -> bool:
        """
        Initialize browser and load session.
        
        Returns:
            True if setup successful, False otherwise
        """
        try:
            # VPN rotation disabled
            # if await vpn.should_rotate():
            #     await vpn.rotate_ip()
            
            # Launch browser
            self.browser, self.context, self.page = await self.browser_manager.launch()
            
            # Load cookies and track if successful
            self.cookies_loaded = await self.session_manager.load_cookies(self.context)
            
            # Initialize managers
            self.message_manager = MessageManager(self.page, self.human)
            self.offer_manager = OfferManager(self.page, self.human)
            self.nav_manager = NavigationManager(self.page, self.human)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Setup failed: {e}")
            return False
    
    async def authenticate(self, force_fresh: bool = False) -> bool:
        """
        Login with human-like behavior.
        
        Args:
            force_fresh: Force fresh login even if cookies exist
            
        Returns:
            True if authenticated, False otherwise
        """
        if not self.page:
            logger.error("❌ Browser not initialized")
            return False
        
        # If cookies were loaded and not forcing fresh login, skip verification
        if self.cookies_loaded and not force_fresh:
            logger.info("✅ Cookies loaded - skipping login verification")
            return True
        
        # If no cookies loaded or force_fresh, perform login
        logger.info("🔐 Performing login...")
        return await login(self.page, self.email, self.password, self.human)
    
    async def execute_workflow(
        self,
        listing_url: str,
        message: str,
        price: float,
        delivery: str,
        shipping_cost: Optional[float] = None,
        note: Optional[str] = None,
        force_fresh_login: bool = False
    ) -> Dict:
        """
        Execute full workflow: message → navigate → offer.
        
        Args:
            listing_url: URL of the listing
            message: Message text to send
            price: Offer price
            delivery: Delivery method (pickup/shipping/both)
            shipping_cost: Optional shipping cost
            note: Optional note
            
        Returns:
            Dict with success status, steps completed, and errors
        """
        result = {
            "success": False,
            "steps_completed": [],
            "errors": []
        }
        
        try:
            # Step 1: Setup
            if not await self.setup():
                result["errors"].append("Setup failed")
                return result
            result["steps_completed"].append("setup")
            
            # Step 2: Authenticate
            if not await self.authenticate(force_fresh=force_fresh_login):
                result["errors"].append("Authentication failed")
                return result
            result["steps_completed"].append("auth")
            
            # Step 3: Send message
            msg_result = await self.message_manager.send_message(listing_url, message)
            if not msg_result["success"]:
                result["errors"].append("Message failed")
                return result
            result["steps_completed"].append("message")
            
            # Step 4: Navigate to conversation
            conv_url = msg_result.get("conversation_url")
            if not await self.nav_manager.navigate_to_conversation(conv_url):
                result["errors"].append("Navigation failed")
                return result
            result["steps_completed"].append("navigation")
            
            # Step 5: Make offer
            if not await self.offer_manager.make_offer(price, delivery, shipping_cost, note):
                result["errors"].append("Offer failed")
                return result
            result["steps_completed"].append("offer")
            
            # Success
            result["success"] = True
            await self.session_manager.save_cookies(self.context)
            logger.info("✅✅✅ Workflow completed successfully ✅✅✅")
            
        except Exception as e:
            logger.error(f"❌ Workflow exception: {e}")
            result["errors"].append(str(e))
        
        finally:
            await self.browser_manager.close()
        
        return result
    
    async def debug_page_elements(self) -> None:
        """
        Debug helper: Log all interactive elements on current page.
        Call this when selectors are not working to discover correct ones.
        """
        if not self.page:
            logger.error("Page not initialized")
            return
        
        logger.info("=" * 60)
        logger.info("🔍 PAGE ELEMENTS DEBUG")
        logger.info("=" * 60)
        
        # All buttons
        buttons = await self.page.query_selector_all("button")
        logger.info(f"BUTTONS: {len(buttons)} found")
        for i, btn in enumerate(buttons[:20]):  # Log first 20
            try:
                text = await btn.inner_text()
                id_attr = await btn.get_attribute("id")
                class_attr = await btn.get_attribute("class")
                type_attr = await btn.get_attribute("type")
                logger.info(f"  [{i}] text='{text[:30]}' id='{id_attr}' class='{class_attr}' type='{type_attr}'")
            except:
                continue
        
        logger.info("-" * 60)
        
        # All links
        links = await self.page.query_selector_all("a")
        logger.info(f"LINKS: {len(links)} found")
        for i, link in enumerate(links[:20]):  # Log first 20
            try:
                text = await link.inner_text()
                href = await link.get_attribute("href")
                id_attr = await link.get_attribute("id")
                class_attr = await link.get_attribute("class")
                logger.info(f"  [{i}] text='{text[:30]}' href='{href}' id='{id_attr}' class='{class_attr}'")
            except:
                continue
        
        logger.info("-" * 60)
        
        # All textareas
        textareas = await self.page.query_selector_all("textarea")
        logger.info(f"TEXTAREAS: {len(textareas)} found")
        for i, ta in enumerate(textareas):
            try:
                id_attr = await ta.get_attribute("id")
                name_attr = await ta.get_attribute("name")
                placeholder = await ta.get_attribute("placeholder")
                class_attr = await ta.get_attribute("class")
                logger.info(f"  [{i}] id='{id_attr}' name='{name_attr}' placeholder='{placeholder}' class='{class_attr}'")
            except:
                continue
        
        logger.info("=" * 60)

