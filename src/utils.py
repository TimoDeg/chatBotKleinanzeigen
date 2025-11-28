"""
Utility functions for logging, screenshots, retries, and helpers.
"""

import os
import time
import random
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable, Any

from loguru import logger
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from src.config import LOGS_DIR, SCREENSHOTS_DIR, LOG_FILE, MAX_RETRIES, RETRY_BACKOFF


async def random_delay(min_seconds: float = 1.0, max_seconds: float = 3.0) -> None:
    """
    Random delay between actions to avoid bot detection.
    Uses human-like timing patterns.
    
    Args:
        min_seconds: Minimum delay in seconds
        max_seconds: Maximum delay in seconds
    """
    # Use slightly longer delays to appear more human
    delay = random.uniform(min_seconds, max_seconds)
    # Add occasional longer pauses (human behavior)
    if random.random() < 0.1:  # 10% chance
        delay += random.uniform(2, 5)
    logger.debug(f"⏳ Random delay: {delay:.2f}s")
    await asyncio.sleep(delay)


def setup_logging(debug: bool = False) -> None:
    """
    Configure loguru logger with file and console output.
    
    Args:
        debug: If True, set log level to DEBUG, otherwise INFO
    """
    # Create logs directory if it doesn't exist
    Path(LOGS_DIR).mkdir(parents=True, exist_ok=True)
    
    # Remove default handler
    logger.remove()
    
    # Add console handler
    log_level = "DEBUG" if debug else "INFO"
    logger.add(
        lambda msg: print(msg, end=""),
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> | <level>{message}</level>",
        level=log_level,
        colorize=True,
    )
    
    # Add file handler
    logger.add(
        LOG_FILE,
        format="{time:YYYY-MM-DDTHH:mm:ss} | {level: <8} | {name}:{function} | {message}",
        level=log_level,
        rotation="10 MB",
        retention="7 days",
        compression="zip",
    )
    
    logger.info("Logging initialized")


async def take_screenshot(
    page: Page,
    filename: Optional[str] = None,
    prefix: str = "error"
) -> str:
    """
    Take a screenshot and save it to screenshots directory.
    
    Args:
        page: Playwright page object
        filename: Optional custom filename, otherwise auto-generated
        prefix: Prefix for auto-generated filename
        
    Returns:
        Path to saved screenshot
    """
    Path(SCREENSHOTS_DIR).mkdir(parents=True, exist_ok=True)
    
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_{timestamp}.png"
    
    screenshot_path = os.path.join(SCREENSHOTS_DIR, filename)
    
    try:
        await page.screenshot(path=screenshot_path, full_page=True)
        logger.debug(f"Screenshot saved: {screenshot_path}")
        return screenshot_path
    except Exception as e:
        logger.error(f"Failed to take screenshot: {e}")
        return ""


async def wait_for_selector_with_fallbacks(
    page: Page,
    selectors: list,
    timeout: int = 10,
    state: str = "visible"
) -> Optional[Any]:
    """
    Try multiple selectors in order until one is found.
    
    Args:
        page: Playwright page object
        selectors: List of selector strings to try
        timeout: Maximum wait time per selector
        state: Element state to wait for (visible, hidden, attached, detached)
        
    Returns:
        ElementHandle if found, None otherwise
    """
    for selector in selectors:
        try:
            logger.debug(f"Trying selector: {selector}")
            element = await page.wait_for_selector(
                selector,
                timeout=timeout * 1000,  # Convert to milliseconds
                state=state
            )
            if element:
                logger.debug(f"Found element with selector: {selector}")
                return element
        except PlaywrightTimeoutError:
            logger.debug(f"Selector not found: {selector}")
            continue
        except Exception as e:
            logger.debug(f"Error with selector {selector}: {e}")
            continue
    
    logger.warning(f"None of the selectors matched: {selectors}")
    return None


async def retry_with_backoff(
    func: Callable,
    max_retries: int = MAX_RETRIES,
    backoff: int = RETRY_BACKOFF,
    *args,
    **kwargs
) -> Any:
    """
    Retry a function with exponential backoff.
    
    Args:
        func: Async function to retry
        max_retries: Maximum number of retry attempts
        backoff: Base backoff time in seconds
        *args: Positional arguments for func
        **kwargs: Keyword arguments for func
        
    Returns:
        Result of func if successful
        
    Raises:
        Exception: If all retries fail
    """
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            if attempt < max_retries - 1:
                wait_time = backoff * (2 ** attempt)
                logger.warning(
                    f"Attempt {attempt + 1}/{max_retries} failed: {e}. "
                    f"Retrying in {wait_time} seconds..."
                )
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"All {max_retries} attempts failed")
    
    raise last_exception


async def safe_click(
    page: Page,
    selectors: list,
    timeout: int = 10,
    description: str = "element"
) -> bool:
    """
    Safely click an element using fallback selectors.
    
    Args:
        page: Playwright page object
        selectors: List of selector strings to try
        timeout: Maximum wait time
        description: Description of element for logging
        
    Returns:
        True if clicked successfully, False otherwise
    """
    element = await wait_for_selector_with_fallbacks(page, selectors, timeout)
    
    if element:
        try:
            await element.click()
            logger.debug(f"Clicked {description}")
            return True
        except Exception as e:
            logger.error(f"Failed to click {description}: {e}")
            return False
    else:
        logger.error(f"Could not find {description} to click")
        return False


async def safe_fill(
    page: Page,
    selectors: list,
    text: str,
    timeout: int = 10,
    description: str = "input field"
) -> bool:
    """
    Safely fill an input field using fallback selectors.
    
    Args:
        page: Playwright page object
        selectors: List of selector strings to try
        text: Text to fill
        timeout: Maximum wait time
        description: Description of field for logging
        
    Returns:
        True if filled successfully, False otherwise
    """
    element = await wait_for_selector_with_fallbacks(page, selectors, timeout)
    
    if element:
        try:
            await element.fill(text)
            logger.debug(f"Filled {description} with: {text[:50]}...")
            return True
        except Exception as e:
            logger.error(f"Failed to fill {description}: {e}")
            return False
    else:
        logger.error(f"Could not find {description} to fill")
        return False


async def safe_select(
    page: Page,
    selectors: list,
    value: str,
    timeout: int = 10,
    description: str = "select field"
) -> bool:
    """
    Safely select an option in a dropdown using fallback selectors.
    
    Args:
        page: Playwright page object
        selectors: List of selector strings to try
        value: Value to select
        timeout: Maximum wait time
        description: Description of field for logging
        
    Returns:
        True if selected successfully, False otherwise
    """
    element = await wait_for_selector_with_fallbacks(page, selectors, timeout)
    
    if element:
        try:
            await element.select_option(value)
            logger.debug(f"Selected {value} in {description}")
            return True
        except Exception as e:
            logger.error(f"Failed to select in {description}: {e}")
            return False
    else:
        logger.error(f"Could not find {description} to select")
        return False


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


