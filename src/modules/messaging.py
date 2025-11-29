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
        Send message with offer via modal.

        Complete workflow:
        1. Click "Nachricht schreiben" button
        2. Modal opens "Verkäufer kontaktieren"
        3. Fill all modal fields (Nachricht, Profilname, Betrag, Versandmethode)
        4. Click "Senden" in modal
        """
        result: Dict[str, object] = {
            "success": False,
            "message_sent": False,
            "offer_made": False,
        }

        try:
            logger.info(f"💬 Sending message with offer to: {listing_url}")

            # ============================================================
            # STEP 1: Navigate to listing
            # ============================================================
            logger.info("Navigating to listing...")
            await self.page.goto(listing_url, wait_until="domcontentloaded")
            await self.human.delay("navigating", fast_mode=fast_mode)

            await self.page.evaluate("window.scrollBy(0, 300)")
            await self.human.delay("default", fast_mode=fast_mode)

            # ============================================================
            # STEP 2: Click "Nachricht schreiben" button
            # ============================================================
            logger.info("Searching for 'Nachricht schreiben' button...")
            msg_btn = None

            try:
                # Try role-based locator
                locator = self.page.get_by_role("button", name="Nachricht schreiben")
                await locator.first.wait_for(timeout=5000)
                msg_btn = locator.first
                logger.info("✅ Found button via role locator")
            except Exception:
                # Fallback to selectors
                msg_btn = await self.selectors.find(
                    self.page,
                    "MESSAGE_BUTTON",
                    timeout=5000,
                )

            if not msg_btn:
                logger.error("❌ 'Nachricht schreiben' button not found")
                await take_screenshot(self.page, "error_message_button")
                return result

            logger.info("✅ Clicking 'Nachricht schreiben'...")
            await msg_btn.scroll_into_view_if_needed()
            await self.human.delay("default", fast_mode=fast_mode)
            await msg_btn.click()

            # Wait for modal to appear
            logger.info("Waiting for modal to open...")
            await self.page.wait_for_timeout(1500)

            # ============================================================
            # STEP 3: Wait for modal to be fully loaded
            # ============================================================
            try:
                await self.page.wait_for_selector(
                    "div[role='dialog']",
                    state="visible",
                    timeout=3000,
                )
                logger.info("✅ Modal opened")
            except Exception:
                logger.warning("⚠️  Modal not detected by role=dialog, continuing...")

            await self.human.delay("default", fast_mode=fast_mode)

            # ============================================================
            # STEP 4: Fill "Nachricht*" textarea in modal
            # ============================================================
            logger.info("Filling 'Nachricht*' field...")

            textarea = None
            try:
                textarea = await self.page.wait_for_selector(
                    "textarea#message-textarea-input",
                    state="visible",
                    timeout=3000,
                )
                logger.info("✅ Found textarea by ID")
            except Exception:
                try:
                    textarea = await self.page.wait_for_selector(
                        "div[role='dialog'] textarea",
                        state="visible",
                        timeout=3000,
                    )
                    logger.info("✅ Found textarea in dialog")
                except Exception:
                    logger.error("❌ Nachricht textarea not found")
                    await take_screenshot(self.page, "error_modal_textarea")
                    return result

            # Fill message
            try:
                await textarea.click(force=True)
                await self.human.delay("default", fast_mode=fast_mode)
                await textarea.fill(message)
            except Exception:
                # Fallback: JavaScript fill
                logger.debug("Click failed, using JS fill...")
                await textarea.evaluate(
                    "el => { el.value = arguments[0]; el.dispatchEvent(new Event('input', { bubbles: true })); }",
                    message,
                )

            await self.human.delay("default", fast_mode=fast_mode)
            logger.info("✅ Nachricht filled")

            # ============================================================
            # STEP 5: Fill "Profilname*" input
            # ============================================================
            logger.info("Filling 'Profilname*' field...")
            try:
                profile_input = await self.page.wait_for_selector(
                    "input[placeholder*='Profilname'], input[id*='profile'], div[role='dialog'] input[type='text']",
                    state="visible",
                    timeout=2000,
                )
                if profile_input:
                    await profile_input.click(force=True)
                    await profile_input.fill(profile_name)
                    logger.info(f"✅ Profilname: {profile_name}")
            except Exception:
                logger.debug("Profilname field not found or already filled")

            await self.human.delay("default", fast_mode=fast_mode)

            # ============================================================
            # STEP 6: Enable "Preisangebot mit Käuferschutz" toggle
            # ============================================================
            if enable_buyer_protection:
                logger.info("Enabling 'Preisangebot mit Käuferschutz'...")
                try:
                    # Specific toggle button from HTML: role="switch", name="MessageOfferCombined__toggle"
                    toggle = await self.page.wait_for_selector(
                        "button[name='MessageOfferCombined__toggle'], [role='switch'][name='MessageOfferCombined__toggle']",
                        state="visible",
                        timeout=3000,
                    )
                    if toggle:
                        aria_checked = await toggle.get_attribute("aria-checked")
                        is_checked = aria_checked == "true"
                        if not is_checked:
                            await toggle.click(force=True)
                            logger.info("✅ Käuferschutz toggle enabled")
                        else:
                            logger.info("✅ Käuferschutz already enabled")
                except Exception:
                    logger.debug("Käuferschutz toggle not found or already enabled")

            await self.human.delay("default", fast_mode=fast_mode)

            # ============================================================
            # STEP 7: Fill "Betrag" (price) input
            # ============================================================
            logger.info("Filling 'Betrag' field...")

            amount_input = None
            try:
                amount_input = await self.page.wait_for_selector(
                    "input[placeholder*='Betrag'], input[id*='price'], input[id*='amount'], div[role='dialog'] input[type='number']",
                    state="visible",
                    timeout=3000,
                )
            except Exception:
                try:
                    amount_input = await self.page.wait_for_selector(
                        "div[role='dialog'] input[type='number']",
                        state="visible",
                        timeout=2000,
                    )
                except Exception:
                    logger.error("❌ Betrag input not found")
                    await take_screenshot(self.page, "error_betrag_input")
                    return result

            await amount_input.click(force=True)
            await amount_input.fill("")
            await self.human.delay("default", fast_mode=fast_mode)

            amount_str = f"{offer_price:.2f}".replace(".", ",")
            await amount_input.fill(amount_str)
            logger.info(f"✅ Betrag: {amount_str} €")

            await self.human.delay("default", fast_mode=fast_mode)

            # ============================================================
            # STEP 8: Select "Versandmethode*" (first real option)
            # ============================================================
            if delivery in ["shipping", "both"]:
                logger.info("Selecting 'Versandmethode*' (first option)...")
                try:
                    # Your HTML: <select id="shipping-select"> with several options
                    shipping_select = await self.page.wait_for_selector(
                        "select#shipping-select, div[role='dialog'] select#shipping-select, div[role='dialog'] select",
                        state="visible",
                        timeout=3000,
                    )
                    if shipping_select:
                        # Prefer first non-placeholder option by index
                        # Index 0: "Bitte auswählen" (disabled)
                        # Index 1: empty filler, Index 2+: real options
                        try:
                            await shipping_select.select_option(index=2)
                            logger.info("✅ Versandmethode: first real option selected (index 2)")
                        except Exception:
                            # Fallback: any value except -1 / empty
                            options = await shipping_select.evaluate(
                                """(el) => Array.from(el.options)
                                .map(o => ({ value: o.value, disabled: o.disabled }))"""
                            )
                            valid_values = [
                                o["value"]
                                for o in options
                                if o["value"] not in ("", "-1") and not o["disabled"]
                            ]
                            if valid_values:
                                await shipping_select.select_option(valid_values[0])
                                logger.info(f"✅ Versandmethode selected value='{valid_values[0]}'")
                            else:
                                logger.warning("⚠️  No valid shipping options found")
                except Exception:
                    logger.warning("⚠️  Versandmethode dropdown not found")

            await self.human.delay("thinking", fast_mode=fast_mode)

            # ============================================================
            # STEP 9: Click "Senden" button in modal
            # ============================================================
            logger.info("Searching for final 'Senden' button in modal...")
            send_btn = None
            try:
                # Most specific: your button with id + data-testid
                send_btn = await self.page.wait_for_selector(
                    "button#message-submit-button[data-testid='message-submit-button']",
                    state="visible",
                    timeout=3000,
                )
                logger.info("✅ Found 'Senden' button via ID+data-testid")
            except Exception:
                try:
                    locator = self.page.get_by_role("button", name="Senden")
                    await locator.first.wait_for(state="visible", timeout=3000)
                    send_btn = locator.first
                    logger.info("✅ Found 'Senden' button via role locator")
                except Exception:
                    try:
                        send_btn = await self.page.wait_for_selector(
                            "div[role='dialog'] button:has-text('Senden')",
                            state="visible",
                            timeout=3000,
                        )
                        logger.info("✅ Found 'Senden' button in dialog via text")
                    except Exception:
                        logger.error("❌ 'Senden' button not found in modal")
                        await take_screenshot(self.page, "error_send_button_modal")
                        return result

            logger.info("✅ Clicking final 'Senden' button to submit offer...")
            await send_btn.scroll_into_view_if_needed()
            await self.human.delay("default", fast_mode=fast_mode)
            await send_btn.click(force=True)

            # Wait for submission / modal close
            await self.page.wait_for_timeout(2000)

            logger.info("✅ Message + offer successfully submitted via modal")
            logger.info("✅✅✅ Full modal workflow completed ✅✅✅")
            result["success"] = True
            result["message_sent"] = True
            result["offer_made"] = True

            return result

        except Exception as e:
            logger.error(f"❌ Exception in send_message: {e}")
            await take_screenshot(self.page, "error_send_message_exception")
            import traceback
            logger.debug(traceback.format_exc())
            return result


