"""
Session management with cookie persistence and expiration handling.
"""

import json
import time
from pathlib import Path
from typing import Optional

from playwright.async_api import BrowserContext
from loguru import logger


class SessionManager:
    """Manages browser session cookies with expiration handling."""
    
    def __init__(self, cookies_path: Path = Path("./cookies.json")):
        """
        Initialize SessionManager.
        
        Args:
            cookies_path: Path to cookies JSON file
        """
        self.cookies_path = cookies_path
    
    async def save_cookies(self, context: BrowserContext) -> bool:
        """
        Save browser cookies to JSON file with extended expiration.
        
        Extends cookie expiration to 30 days to keep sessions alive longer.
        
        Args:
            context: Playwright browser context
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            cookies = await context.cookies()
            
            if not cookies:
                logger.debug("No cookies to save")
                return False
            
            # Extend cookie expiration (30 days from now)
            extended_cookies = []
            current_time = time.time()
            expiration_extension = 30 * 24 * 60 * 60  # 30 days in seconds
            
            for cookie in cookies:
                # Extend expiration if it exists
                if 'expires' in cookie and cookie['expires'] > 0:
                    cookie['expires'] = int(current_time) + expiration_extension
                elif 'expires' not in cookie:
                    # Add expiration if missing (session cookie -> persistent)
                    cookie['expires'] = int(current_time) + expiration_extension
                
                extended_cookies.append(cookie)
            
            # Create directory if it doesn't exist
            self.cookies_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.cookies_path, "w", encoding="utf-8") as f:
                json.dump(extended_cookies, f, indent=2)
            
            logger.info(f"✅ Cookies saved: {len(extended_cookies)} cookies")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save cookies: {e}")
            return False
    
    async def load_cookies(self, context: BrowserContext) -> bool:
        """
        Load cookies from JSON file if it exists.
        
        Validates cookies and filters out expired ones.
        
        Args:
            context: Playwright browser context
            
        Returns:
            True if cookies loaded, False if file doesn't exist or all expired
        """
        if not self.cookies_path.exists():
            logger.debug("⚠️  No cookies file found")
            return False
        
        try:
            with open(self.cookies_path, "r", encoding="utf-8") as f:
                cookies = json.load(f)
            
            if not cookies:
                logger.debug("Cookie file is empty")
                return False
            
            # Filter out expired cookies and extend valid ones
            current_time = time.time()
            expiration_extension = 30 * 24 * 60 * 60  # 30 days
            
            valid_cookies = []
            for cookie in cookies:
                # Check if cookie is expired
                if 'expires' in cookie:
                    if cookie['expires'] <= current_time:
                        continue  # Skip expired cookies
                    # Extend expiration if it's expiring soon (within 7 days)
                    elif cookie['expires'] < current_time + (7 * 24 * 60 * 60):
                        cookie['expires'] = int(current_time) + expiration_extension
                else:
                    # Session cookie - add expiration
                    cookie['expires'] = int(current_time) + expiration_extension
                
                valid_cookies.append(cookie)
            
            if not valid_cookies:
                logger.debug("All cookies are expired")
                return False
            
            await context.add_cookies(valid_cookies)
            logger.info(f"✅ Cookies loaded: {len(valid_cookies)} valid cookies")
            return True
            
        except Exception as e:
            logger.warning(f"⚠️  Failed to load cookies: {e}")
            return False

