#!/usr/bin/env python3
"""
Isolated test script for message sending functionality.
Run with headless=False to see browser actions visually.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.bot import KleinanzeigenBot
from src.utils.logger import setup_logger
from loguru import logger


async def test_message_sending():
    """
    Test only the message sending step with visual debugging.
    """
    print("=" * 60)
    print("MESSAGE SENDING TEST (DEBUG MODE)")
    print("=" * 60)
    print()
    
    # Get input from user
    url = input("Listing URL: ").strip()
    email = input("Email: ").strip()
    password = input("Password: ").strip()
    message = input("Message (press Enter for default): ").strip() or "Ist noch verfügbar?"
    
    print()
    print("Starting test with:")
    print(f"  URL: {url}")
    print(f"  Email: {email}")
    print(f"  Message: {message}")
    print()
    
    # Setup logging with DEBUG level
    setup_logger()
    logger.remove()
    logger.add(lambda msg: print(msg, end=""), level="DEBUG", colorize=True)
    
    # Create bot with headless=False to see browser
    bot = KleinanzeigenBot(email=email, password=password)
    
    try:
        # Step 1: Setup browser
        logger.info("=" * 60)
        logger.info("STEP 1: Browser Setup")
        logger.info("=" * 60)
        
        if not await bot.setup():
            logger.error("❌ Browser setup failed")
            return
        
        logger.info("✅ Browser setup successful")
        await asyncio.sleep(2)
        
        # Step 2: Login
        logger.info("=" * 60)
        logger.info("STEP 2: Authentication")
        logger.info("=" * 60)
        
        if not await bot.authenticate():
            logger.error("❌ Authentication failed")
            return
        
        logger.info("✅ Authentication successful")
        logger.info("Waiting 5 seconds to verify login...")
        await asyncio.sleep(5)
        
        # Step 3: Send message (the problematic part)
        logger.info("=" * 60)
        logger.info("STEP 3: Send Message")
        logger.info("=" * 60)
        
        result = await bot.message_manager.send_message(url, message)
        
        # Step 4: Results
        logger.info("=" * 60)
        logger.info("TEST RESULTS")
        logger.info("=" * 60)
        logger.info(f"Success: {result.get('success')}")
        logger.info(f"Conversation URL: {result.get('conversation_url')}")
        logger.info("=" * 60)
        
        if result.get('success'):
            logger.info("✅✅✅ TEST PASSED ✅✅✅")
        else:
            logger.error("❌❌❌ TEST FAILED ❌❌❌")
            logger.error("Check screenshots/ and logs/ directories for details")
        
        # Keep browser open for manual inspection
        logger.info("Keeping browser open for 30 seconds for inspection...")
        await asyncio.sleep(30)
        
    except KeyboardInterrupt:
        logger.warning("Test interrupted by user")
    except Exception as e:
        logger.error(f"Test failed with exception: {e}")
        import traceback
        logger.debug(traceback.format_exc())
    finally:
        logger.info("Closing browser...")
        await bot.browser_manager.close()
        logger.info("Test completed")


if __name__ == "__main__":
    asyncio.run(test_message_sending())

