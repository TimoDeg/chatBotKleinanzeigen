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
    
    def __init__(self, email: str, password: str):
        """
        Initialize KleinanzeigenBot.
        
        Args:
            email: User email
            password: User password
        """
        self.email = email
        self.password = password
        
        self.browser_manager = BrowserManager(headless=settings.headless)
        self.session_manager = SessionManager(settings.cookies_path)
        self.human = HumanBehavior()
        
        self.browser = None
        self.context = None
        self.page: Optional[Page] = None
        self.message_manager: Optional[MessageManager] = None
        self.offer_manager: Optional[OfferManager] = None
        self.nav_manager: Optional[NavigationManager] = None
    
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
            
            # Load cookies
            await self.session_manager.load_cookies(self.context)
            
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
        
        # Quick check if already logged in (if cookies loaded)
        if not force_fresh:
            try:
                logged_in = await self.page.wait_for_selector(
                    "a[href*='/nachrichtenbox'], [class*='user-menu'], a:has-text('Meine Anzeigen')",
                    timeout=2000
                )
                if logged_in:
                    logger.info("✅ Already authenticated")
                    return True
            except:
                pass
        
        # Perform login
        return await login(self.page, self.email, self.password, self.human)
    
    async def execute_workflow(
        self,
        listing_url: str,
        message: str,
        price: float,
        delivery: str,
        shipping_cost: Optional[float] = None,
        note: Optional[str] = None
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
            if not await self.authenticate():
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

