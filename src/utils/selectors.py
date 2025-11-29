"""
Centralized selector management with fallback logic.
"""

from typing import Optional

from playwright.async_api import Page, ElementHandle
from loguru import logger

from src.config.constants import ALL_SELECTORS


class SelectorManager:
    """Centralized selector management with fallback logic."""
    
    async def find(
        self,
        page: Page,
        selector_name: str,
        timeout: int = 5000
    ) -> Optional[ElementHandle]:
        """
        Find element using fallback selectors.
        
        Args:
            page: Playwright page
            selector_name: Name from constants (e.g., "MESSAGE_BUTTON")
            timeout: Timeout per selector in ms
            
        Returns:
            ElementHandle if found, None otherwise
        """
        selectors = ALL_SELECTORS.get(selector_name, [])
        
        if not selectors:
            logger.warning(f"Unknown selector name: {selector_name}")
            return None
        
        for i, selector in enumerate(selectors):
            try:
                element = await page.wait_for_selector(selector, timeout=timeout)
                if element:
                    logger.debug(f"Found: {selector_name} [{i+1}/{len(selectors)}]")
                    return element
            except Exception:
                continue
        
        logger.warning(f"Not found: {selector_name} (tried {len(selectors)} selectors)")
        return None

