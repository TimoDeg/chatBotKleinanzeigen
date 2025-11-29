"""
General utility functions.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

from playwright.async_api import Page
from loguru import logger

from src.config.settings import settings


async def take_screenshot(page: Page, prefix: str = "error") -> Path:
    """
    Take a screenshot and save it to screenshots directory.
    
    Args:
        page: Playwright page object
        prefix: Prefix for auto-generated filename
        
    Returns:
        Path to saved screenshot
    """
    settings.screenshots_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{prefix}_{timestamp}.png"
    screenshot_path = settings.screenshots_dir / filename
    
    try:
        await page.screenshot(path=str(screenshot_path), full_page=True)
        logger.debug(f"Screenshot saved: {screenshot_path}")
        return screenshot_path
    except Exception as e:
        logger.error(f"Failed to take screenshot: {e}")
        return Path()


def validate_url(url: str) -> bool:
    """
    Validate that URL is a Kleinanzeigen listing URL.
    
    Args:
        url: URL to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not url:
        return False
    
    valid_domains = [
        "kleinanzeigen.de",
        "www.kleinanzeigen.de",
    ]
    
    return any(domain in url for domain in valid_domains)

