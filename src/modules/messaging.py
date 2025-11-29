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
        Send message to listing with improved modal handling and debugging.
        
        Args:
            listing_url: URL of the listing
            message: Message text to send
            
        Returns:
            Dict with success status and conversation URL
        """
        logger.info(f"💬 Sending message to: {listing_url}")
        
        try:
            # 1. Navigate to listing
            logger.info("Navigating to listing...")
            await self.page.goto(listing_url, wait_until="domcontentloaded")
            await self.human.delay("navigating")
            
            # 2. Scroll down to trigger lazy-loading (IMPORTANT!)
            logger.info("Scrolling to load dynamic content...")
            await self.page.evaluate("window.scrollBy(0, 300)")
            await self.human.delay("default")
            
            # 3. Find message button
            logger.info("Searching for message button...")
            msg_btn = await self.selectors.find(
                self.page,
                "MESSAGE_BUTTON",
                timeout=15000
            )
            
            if not msg_btn:
                logger.error("❌ Message button not found")
                await take_screenshot(self.page, "error_message_button_not_found")
                
                # DEBUG: Call debug_page_elements if available
                try:
                    # Try to get bot instance to call debug method
                    # This is a workaround - we'll do manual debugging here
                    logger.warning("🔍 DEBUG: Analyzing page elements...")
                    
                    # Get all buttons and links
                    all_links = await self.page.query_selector_all("a, button")
                    logger.warning(f"Found {len(all_links)} total links/buttons on page")
                    
                    # Search for elements with "nachricht" or "contact"
                    nachricht_elements = []
                    contact_elements = []
                    
                    for link in all_links:
                        try:
                            text = await link.inner_text()
                            href = await link.get_attribute("href")
                            id_attr = await link.get_attribute("id")
                            class_attr = await link.get_attribute("class")
                            
                            if text:
                                text_lower = text.lower()
                                if "nachricht" in text_lower or "kontakt" in text_lower or "contact" in text_lower:
                                    nachricht_elements.append({
                                        "text": text.strip()[:50],
                                        "href": href,
                                        "id": id_attr,
                                        "class": class_attr
                                    })
                            
                            # Also check IDs and classes
                            if id_attr and ("contact" in id_attr.lower() or "nachricht" in id_attr.lower()):
                                contact_elements.append({
                                    "type": "id",
                                    "value": id_attr,
                                    "text": text.strip()[:50] if text else None,
                                    "href": href,
                                    "class": class_attr
                                })
                            
                            if class_attr and ("contact" in class_attr.lower() or "nachricht" in class_attr.lower()):
                                contact_elements.append({
                                    "type": "class",
                                    "value": class_attr,
                                    "text": text.strip()[:50] if text else None,
                                    "href": href,
                                    "id": id_attr
                                })
                        except:
                            continue
                    
                    if nachricht_elements:
                        logger.warning(f"Found {len(nachricht_elements)} elements with 'nachricht'/'kontakt' in text:")
                        for elem in nachricht_elements[:10]:
                            logger.warning(f"  - text='{elem['text']}' id='{elem['id']}' class='{elem['class']}' href='{elem['href']}'")
                    
                    if contact_elements:
                        logger.warning(f"Found {len(contact_elements)} elements with 'contact'/'nachricht' in id/class:")
                        for elem in contact_elements[:10]:
                            logger.warning(f"  - {elem['type']}='{elem['value']}' text='{elem['text']}' id='{elem.get('id')}' class='{elem.get('class')}'")
                    
                    if not nachricht_elements and not contact_elements:
                        logger.error("❌ No elements with 'nachricht', 'kontakt', or 'contact' found on page!")
                        logger.warning("🔍 Listing first 20 buttons/links for manual inspection:")
                        for i, link in enumerate(all_links[:20]):
                            try:
                                text = await link.inner_text()
                                href = await link.get_attribute("href")
                                id_attr = await link.get_attribute("id")
                                class_attr = await link.get_attribute("class")
                                logger.warning(f"  [{i}] text='{text[:30] if text else 'N/A'}' id='{id_attr}' class='{class_attr}' href='{href}'")
                            except:
                                continue
                    
                    # Keep browser open for 10 seconds for manual inspection
                    logger.warning("⏸️  Keeping browser open for 10 seconds for manual inspection...")
                    await self.page.wait_for_timeout(10000)
                    
                except Exception as debug_error:
                    logger.error(f"Debug analysis failed: {debug_error}")
                
                return {"success": False, "conversation_url": None}
            
            # 4. Click message button
            logger.info("✅ Message button found, clicking...")
            await self.human.scroll_into_view(self.page, msg_btn)
            await self.human.delay("default")
            await self.human.human_click(self.page, msg_btn)
            
            # 5. Wait for modal/form to appear
            logger.info("Waiting for message form to load...")
            await self.human.delay("navigating")
            
            # 6. Find textarea
            logger.info("Searching for message textarea...")
            textarea = await self.selectors.find(
                self.page,
                "MESSAGE_TEXTAREA",
                timeout=10000
            )
            
            if not textarea:
                logger.error("❌ Message textarea not found")
                await take_screenshot(self.page, "error_textarea_not_found")
                
                # DEBUG: Log all textareas
                logger.warning("🔍 DEBUG: Searching for all textareas...")
                all_textareas = await self.page.query_selector_all("textarea")
                logger.warning(f"Found {len(all_textareas)} textareas on page")
                
                for i, ta in enumerate(all_textareas):
                    try:
                        id_attr = await ta.get_attribute("id")
                        name_attr = await ta.get_attribute("name")
                        placeholder = await ta.get_attribute("placeholder")
                        logger.warning(f"  Textarea {i}: id='{id_attr}' name='{name_attr}' placeholder='{placeholder}'")
                    except:
                        continue
                
                return {"success": False, "conversation_url": None}
            
            # 7. Fill textarea
            logger.info("✅ Textarea found, filling message...")
            await self.human.scroll_into_view(self.page, textarea)
            await textarea.click()  # Focus first
            await self.human.delay("default")
            await self.human.human_type(textarea, message)
            await self.human.delay("thinking")
            
            # 8. Find and click send button
            logger.info("Searching for send button...")
            send_btn = await self.selectors.find(
                self.page,
                "MESSAGE_SEND",
                timeout=10000
            )
            
            if not send_btn:
                logger.warning("⚠️  Send button not found, trying Enter key fallback...")
                await take_screenshot(self.page, "warning_send_button_not_found")
                
                # Fallback: Press Enter
                await textarea.press("Enter")
                await self.page.wait_for_timeout(2000)
            else:
                logger.info("✅ Send button found, clicking...")
                await self.human.scroll_into_view(self.page, send_btn)
                await self.human.delay("default")
                await self.human.human_click(self.page, send_btn)
                await self.page.wait_for_timeout(2000)
            
            # 9. Verify message sent
            logger.info("Verifying message sent...")
            await self.human.delay("navigating")
            current_url = self.page.url
            logger.info(f"Current URL after send: {current_url}")
            
            # Check if redirected to nachrichtenbox
            if "nachricht" in current_url.lower() or "messages" in current_url.lower():
                logger.info("✅ Message sent successfully (URL redirect detected)")
                return {"success": True, "conversation_url": current_url}
            else:
                # Check for success indicators on page
                logger.info("Checking for success indicators...")
                success_selectors = [
                    "text=/erfolgreich/i",
                    "text=/gesendet/i",
                    "[class*='success']",
                    "[class*='confirmed']",
                ]
                
                for selector in success_selectors:
                    try:
                        element = await self.page.wait_for_selector(selector, timeout=2000)
                        if element:
                            logger.info(f"✅ Success indicator found: {selector}")
                            return {"success": True, "conversation_url": current_url}
                    except:
                        continue
                
                # Assume success if no errors
                logger.warning("⚠️  Could not verify success, assuming message sent")
                return {"success": True, "conversation_url": current_url}
            
        except Exception as e:
            logger.error(f"❌ Message sending failed: {e}")
            await take_screenshot(self.page, "error_send_message")
            
            # Log full traceback for debugging
            import traceback
            logger.debug(traceback.format_exc())
            
            return {"success": False, "conversation_url": None}

