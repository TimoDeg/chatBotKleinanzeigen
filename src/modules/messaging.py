"""
Message sending module with human-like behavior.
"""

from typing import Dict, Optional

from playwright.async_api import Page
from loguru import logger

from src.stealth.human_behavior import HumanBehavior
from src.utils.selectors import SelectorManager
from src.utils.helpers import take_screenshot


class MessageManager:
    """Manages message sending with human-like behavior."""
    
    def __init__(self, page: Page, human: HumanBehavior):
        """
        Initialize MessageManager.
        
        Args:
            page: Playwright page
            human: HumanBehavior instance
        """
        self.page = page
        self.human = human
        self.selectors = SelectorManager()
    
    async def send_message(self, listing_url: str, message: str) -> Dict:
        """
        Send message to listing with human behavior.
        
        Args:
            listing_url: URL of the listing
            message: Message text to send
            
        Returns:
            Dict with success status and conversation URL
        """
        logger.info(f"💬 Sending message to: {listing_url}")
        
        try:
            # Navigate
            await self.page.goto(listing_url, wait_until="domcontentloaded")
            await self.human.delay("navigating")
            
            # Find message button
            msg_btn = await self.selectors.find(
                self.page,
                "MESSAGE_BUTTON",
                timeout=10000
            )
            if not msg_btn:
                logger.error("❌ Message button not found")
                await take_screenshot(self.page, "error_msg_button")
                return {"success": False, "conversation_url": None}
            
            # Scroll and click
            await self.human.scroll_into_view(self.page, msg_btn)
            await self.human.human_click(self.page, msg_btn)
            await self.human.delay("navigating")
            
            # Find textarea
            textarea = await self.selectors.find(self.page, "MESSAGE_TEXTAREA", timeout=10000)
            if not textarea:
                logger.error("❌ Message textarea not found")
                await take_screenshot(self.page, "error_textarea")
                return {"success": False, "conversation_url": None}
            
            # Type message
            await self.human.human_type(textarea, message)
            await self.human.delay("thinking")
            
            # Send
            send_btn = await self.selectors.find(self.page, "MESSAGE_SEND", timeout=10000)
            if not send_btn:
                logger.error("❌ Send button not found")
                await take_screenshot(self.page, "error_send_button")
                return {"success": False, "conversation_url": None}
            
            await self.human.human_click(self.page, send_btn)
            await self.page.wait_for_timeout(2000)
            
            logger.info("✅ Message sent")
            return {"success": True, "conversation_url": self.page.url}
            
        except Exception as e:
            logger.error(f"❌ Message sending failed: {e}")
            await take_screenshot(self.page, "error_send_message")
            return {"success": False, "conversation_url": None}

