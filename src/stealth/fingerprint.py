"""
Browser fingerprint randomization utilities.
Note: Main fingerprinting is handled in browser.py init script.
This module provides additional utilities if needed.
"""

from loguru import logger


class FingerprintManager:
    """Additional fingerprint randomization utilities."""
    
    @staticmethod
    async def randomize_canvas(page) -> None:
        """
        Additional canvas fingerprint randomization (if needed).
        
        Note: Main canvas randomization is done in browser init script.
        This can be called for additional randomization.
        
        Args:
            page: Playwright page
        """
        try:
            await page.evaluate("""
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
            """)
            logger.debug("Canvas fingerprint randomized")
        except Exception as e:
            logger.debug(f"Canvas randomization failed: {e}")

