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
    
    async def send_message(
        self,
        listing_url: str,
        message: str,
        offer_price: float,
        delivery: str,
        profile_name: str = "User",
        shipping_cost: Optional[float] = None,
        enable_buyer_protection: bool = True,
        fast_mode: bool = True,
    ) -> Dict:
        """
        Send message with offer via modal dialog.
        """
        result: Dict[str, Optional[str]] = {"success": False, "message_sent": False}
        
        try:
            logger.info(f"💬 Sending message to: {listing_url}")
            
            # Navigate
            logger.info("Navigating...")
            await self.page.goto(listing_url, wait_until="domcontentloaded")
            await self.human.delay("navigating", fast_mode=fast_mode)
            
            # Scroll
            await self.page.evaluate("window.scrollBy(0, 300)")
            await self.human.delay("default", fast_mode=fast_mode)
            
            # Find message button
            logger.info("Searching for message button...")
            msg_btn = await self.selectors.find(
                self.page,
                "MESSAGE_BUTTON",
                timeout=10000,
            )
            
            if not msg_btn:
                logger.error("❌ Message button not found")
                await take_screenshot(self.page, "error_message_button")
                return result
            
            logger.info("✅ Button found, clicking...")
            await msg_btn.scroll_into_view_if_needed()
            await self.human.delay("default", fast_mode=fast_mode)
            await msg_btn.click()
            
            # Wait for modal
            logger.info("Waiting for modal...")
            await self.human.delay("navigating", fast_mode=fast_mode)
            
            modal = await self.selectors.find(
                self.page,
                "MODAL_CONTAINER",
                timeout=5000,
            )
            
            if modal:
                logger.info("✅ Modal detected")
            else:
                logger.warning("⚠️  Modal not detected, continuing...")
            
            # Fill message textarea IN MODAL
            logger.info("Filling message...")
            textarea = await self.selectors.find(
                self.page,
                "MODAL_MESSAGE_TEXTAREA",
                timeout=5000,
            )
            
            if not textarea:
                logger.error("❌ Textarea not found in modal")
                await take_screenshot(self.page, "error_modal_textarea")
                return result
            
            await textarea.click()
            await self.human.delay("default", fast_mode=fast_mode)
            await self.human.human_type(textarea, message)
            await self.human.delay("default", fast_mode=fast_mode)
            logger.info("✅ Message filled")
            
            # Fill profile name
            try:
                profile_input = await self.selectors.find(
                    self.page,
                    "MODAL_PROFILE_NAME_INPUT",
                    timeout=2000,
                )
                if profile_input:
                    await profile_input.fill(profile_name)
                    logger.info(f"✅ Profile name: {profile_name}")
            except Exception:
                logger.debug("Profile name field not required")
            
            # Fill offer amount
            logger.info("Filling offer amount...")
            amount_input = await self.selectors.find(
                self.page,
                "MODAL_OFFER_AMOUNT_INPUT",
                timeout=5000,
            )
            
            if not amount_input:
                logger.error("❌ Amount input not found")
                await take_screenshot(self.page, "error_modal_amount")
                return result
            
            await amount_input.click()
            await amount_input.fill("")
            await self.human.delay("default", fast_mode=fast_mode)
            
            # German format: 100,00
            amount_str = f"{offer_price:.2f}".replace(".", ",")
            await amount_input.fill(amount_str)
            logger.info(f"✅ Amount: {amount_str} €")
            
            # Select shipping if needed
            if delivery in ["shipping", "both"] and shipping_cost:
                try:
                    shipping_select = await self.selectors.find(
                        self.page,
                        "MODAL_SHIPPING_SELECT",
                        timeout=3000,
                    )
                    if shipping_select:
                        await shipping_select.select_option(index=1)
                        logger.info("✅ Shipping selected")
                except Exception:
                    logger.warning("⚠️  Shipping selection failed")
            
            # Toggle buyer protection
            if enable_buyer_protection:
                try:
                    toggle = await self.selectors.find(
                        self.page,
                        "MODAL_BUYER_PROTECTION_TOGGLE",
                        timeout=2000,
                    )
                    if toggle:
                        is_checked = await toggle.is_checked()
                        if not is_checked:
                            await toggle.click()
                            logger.info("✅ Käuferschutz enabled")
                except Exception:
                    logger.debug("Buyer protection not found")
            
            # Wait before submit
            await self.human.delay("thinking", fast_mode=fast_mode)
            
            # Click send in modal
            logger.info("Clicking send button...")
            send_btn = await self.selectors.find(
                self.page,
                "MODAL_SEND_BUTTON",
                timeout=5000,
            )
            
            if not send_btn:
                logger.error("❌ Send button not found")
                await take_screenshot(self.page, "error_modal_send_button")
                return result
            
            await send_btn.scroll_into_view_if_needed()
            await self.human.delay("default", fast_mode=fast_mode)
            await send_btn.click()
            
            await self.page.wait_for_timeout(2000)
            
            logger.info("✅ Message with offer sent!")
            result["success"] = True
            result["message_sent"] = True
            
            return result
        
        except Exception as e:
            logger.error(f"❌ Exception: {e}")
            await take_screenshot(self.page, "error_send_exception")
            import traceback
            logger.debug(traceback.format_exc())
            return result


