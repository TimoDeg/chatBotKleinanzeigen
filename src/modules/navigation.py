"""
Navigation module for conversation management.
"""

from typing import Optional

from playwright.async_api import Page
from loguru import logger

from src.stealth.human_behavior import HumanBehavior
from src.utils.selectors import SelectorManager
from src.utils.helpers import take_screenshot


class NavigationManager:
    """Manages page navigation with human-like behavior."""
    
    def __init__(self, page: Page, human: HumanBehavior):
        """
        Initialize NavigationManager.
        
        Args:
            page: Playwright page
            human: HumanBehavior instance
        """
        self.page = page
        self.human = human
        self.selectors = SelectorManager()
    
    async def navigate_to_conversation(self, conversation_url: Optional[str] = None) -> bool:
        """
        Navigate to conversation.
        
        If URL provided, navigate there directly.
        Otherwise, go to nachrichtenbox and find latest conversation.
        
        Args:
            conversation_url: Optional direct URL to conversation
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if conversation_url:
                logger.info(f"📬 Navigating to conversation: {conversation_url}")
                await self.page.goto(conversation_url, wait_until="domcontentloaded")
                await self.human.delay("navigating")
                return True
            else:
                # Fallback: Go to nachrichtenbox
                logger.info("📬 Navigating to nachrichtenbox...")
                await self.page.goto("https://www.kleinanzeigen.de/nachrichtenbox", wait_until="domcontentloaded")
                await self.human.delay("navigating")
                
                # Find latest conversation
                latest_conv = await self.selectors.find(
                    self.page,
                    "LATEST_CONVERSATION",
                    timeout=10000
                )
                
                if not latest_conv:
                    logger.error("❌ Latest conversation not found")
                    await take_screenshot(self.page, "error_conversation_not_found")
                    return False
                
                await self.human.human_click(self.page, latest_conv)
                await self.human.delay("navigating")
                logger.info("✅ Conversation opened")
                return True
                
        except Exception as e:
            logger.error(f"❌ Navigation failed: {e}")
            await take_screenshot(self.page, "error_navigation")
            return False

