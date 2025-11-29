"""
Browser management with advanced anti-detection features.
"""

import random
from typing import Optional, Tuple

from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from loguru import logger

from src.config.settings import settings
from src.config.constants import USER_AGENTS


class BrowserManager:
    """Manages browser instance with anti-detection features."""
    
    def __init__(self, headless: bool = False):
        """
        Initialize BrowserManager.
        
        Args:
            headless: Run browser in headless mode (default: False for better anti-detection)
        """
        self.headless = headless
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
    
    async def launch(self) -> Tuple[Browser, BrowserContext, Page]:
        """
        Launch browser with anti-detection settings.
        
        Returns:
            Tuple of (Browser, BrowserContext, Page)
        """
        try:
            logger.info("🔧 Setting up browser with anti-detection...")
            self.playwright = await async_playwright().start()
            
            # Random viewport size (realistic ranges)
            viewport_width = random.randint(1200, 1600)
            viewport_height = random.randint(800, 1000)
            
            # Random user agent
            user_agent = random.choice(USER_AGENTS)
            
            # Enhanced anti-detection args
            browser_args = [
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",  # WICHTIG
                "--disable-extensions",
                "--disable-plugins",
                "--start-maximized",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process",
            ]
            
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=browser_args,
            )
            
            # Create context with realistic settings
            self.context = await self.browser.new_context(
                user_agent=user_agent,
                viewport={"width": viewport_width, "height": viewport_height},
                locale="de-DE",
                timezone_id="Europe/Berlin",
                extra_http_headers={
                    "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "none",
                    "Sec-Fetch-User": "?1",
                },
            )
            
            # Inject stealth JavaScript
            await self.context.add_init_script("""
                // Remove webdriver property
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                
                // Fake plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [
                        {
                            0: {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format"},
                            description: "Portable Document Format",
                            filename: "internal-pdf-viewer",
                            length: 1,
                            name: "Chrome PDF Plugin"
                        },
                        {
                            0: {type: "application/pdf", suffixes: "pdf", description: ""},
                            description: "",
                            filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai",
                            length: 1,
                            name: "Chrome PDF Viewer"
                        }
                    ],
                });
                
                // Fake languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['de-DE', 'de', 'en-US', 'en'],
                });
                
                // Override permissions
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
                
                // Canvas fingerprint randomization
                const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
                HTMLCanvasElement.prototype.toDataURL = function(type) {
                    const context = this.getContext('2d');
                    if (context) {
                        const imageData = context.getImageData(0, 0, this.width, this.height);
                        for (let i = 0; i < imageData.data.length; i += 4) {
                            imageData.data[i] = imageData.data[i] ^ Math.floor(Math.random() * 255);
                        }
                        context.putImageData(imageData, 0, 0);
                    }
                    return originalToDataURL.apply(this, arguments);
                };
                
                // WebGL fingerprint randomization
                const getParameter = WebGLRenderingContext.prototype.getParameter;
                WebGLRenderingContext.prototype.getParameter = function(parameter) {
                    if (parameter === 37445) {
                        return 'Intel Inc.';
                    }
                    if (parameter === 37446) {
                        return 'Intel Iris OpenGL Engine';
                    }
                    return getParameter.apply(this, arguments);
                };
            """)
            
            self.page = await self.context.new_page()
            
            logger.info(f"✅ Browser setup successful (Viewport: {viewport_width}x{viewport_height})")
            return self.browser, self.context, self.page
            
        except Exception as e:
            logger.error(f"❌ Browser setup failed: {e}")
            raise
    
    async def close(self) -> None:
        """Close browser and cleanup resources."""
        try:
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            logger.debug("Browser closed")
        except Exception as e:
            logger.error(f"Error closing browser: {e}")

