"""
Offer making module with human-like behavior.
"""

from typing import Optional

from playwright.async_api import Page
from loguru import logger

from src.stealth.human_behavior import HumanBehavior
from src.utils.selectors import SelectorManager
from src.utils.helpers import take_screenshot
from src.config.constants import DELIVERY_OPTIONS


class OfferManager:
    """Manages offer making with human-like behavior."""
    
    def __init__(self, page: Page, human: HumanBehavior):
        """
        Initialize OfferManager.
        
        Args:
            page: Playwright page
            human: HumanBehavior instance
        """
        self.page = page
        self.human = human
        self.selectors = SelectorManager()
    
    async def make_offer(
        self,
        price: float,
        delivery: str,
        shipping_cost: Optional[float] = None,
        note: Optional[str] = None
    ) -> bool:
        """
        Make offer with human-like behavior.
        
        Args:
            price: Offer price
            delivery: Delivery method (pickup/shipping/both)
            shipping_cost: Optional shipping cost
            note: Optional note
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"💰 Making offer: €{price}, {delivery}")
        
        try:
            await self.human.delay("thinking")
            
            # Find offer button
            offer_btn = await self.selectors.find(
                self.page,
                "OFFER_BUTTON",
                timeout=15000
            )
            if not offer_btn:
                logger.error("❌ Offer button not found")
                await take_screenshot(self.page, "error_offer_button")
                return False
            
            await self.human.human_click(self.page, offer_btn)
            await self.human.delay("navigating")
            
            # Fill price
            price_input = await self.selectors.find(
                self.page,
                "OFFER_PRICE_INPUT",
                timeout=10000
            )
            if not price_input:
                logger.error("❌ Price input not found")
                await take_screenshot(self.page, "error_price_input")
                return False
            
            await self.human.human_type(price_input, str(price))
            await self.human.delay("default")
            logger.info(f"✅ Price entered: €{price}")
            
            # Select delivery
            try:
                delivery_select = await self.selectors.find(
                    self.page,
                    "OFFER_DELIVERY_SELECT",
                    timeout=10000
                )
                if delivery_select:
                    delivery_value = DELIVERY_OPTIONS.get(delivery, delivery)
                    await delivery_select.select_option(label=delivery_value)
                    await self.human.delay("default")
                    logger.info(f"✅ Delivery selected: {delivery_value}")
            except Exception as e:
                logger.warning(f"⚠️  Could not set delivery: {e}")
            
            # Fill shipping cost (optional)
            if shipping_cost and delivery in ["shipping", "both"]:
                try:
                    shipping_input = await self.selectors.find(
                        self.page,
                        "OFFER_SHIPPING_INPUT",
                        timeout=10000
                    )
                    if shipping_input:
                        await self.human.human_type(shipping_input, str(shipping_cost))
                        await self.human.delay("default")
                        logger.info(f"✅ Shipping cost entered: €{shipping_cost}")
                except Exception as e:
                    logger.warning(f"⚠️  Could not set shipping cost: {e}")
            
            # Fill note (optional)
            if note:
                try:
                    note_textarea = await self.selectors.find(
                        self.page,
                        "OFFER_NOTE_TEXTAREA",
                        timeout=10000
                    )
                    if note_textarea:
                        await self.human.human_type(note_textarea, note)
                        await self.human.delay("default")
                        logger.info("✅ Note added")
                except Exception as e:
                    logger.warning(f"⚠️  Could not add note: {e}")
            
            # Submit offer
            await self.human.delay("thinking")
            submit_btn = await self.selectors.find(
                self.page,
                "OFFER_SUBMIT",
                timeout=10000
            )
            if not submit_btn:
                logger.error("❌ Submit button not found")
                await take_screenshot(self.page, "error_submit_button")
                return False
            
            await self.human.human_click(self.page, submit_btn)
            await self.page.wait_for_timeout(3000)
            
            logger.info("✅ Offer sent")
            return True
            
        except Exception as e:
            logger.error(f"❌ Offer failed: {e}")
            await take_screenshot(self.page, "error_make_offer")
            return False

