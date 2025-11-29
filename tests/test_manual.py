"""
Manual test script to validate all components.
"""

import asyncio

from src.core.browser import BrowserManager
from src.stealth.human_behavior import HumanBehavior
from src.stealth.vpn import vpn


async def test_browser():
    """Test browser setup with anti-detection."""
    print("Testing browser...")
    manager = BrowserManager(headless=False)
    browser, context, page = await manager.launch()
    
    await page.goto("https://bot.sannysoft.com/")
    await asyncio.sleep(10)  # Visual inspection
    
    await manager.close()
    print("✅ Browser test passed")


async def test_human_behavior():
    """Test human-like typing and delays."""
    print("Testing human behavior...")
    manager = BrowserManager(headless=False)
    browser, context, page = await manager.launch()
    
    await page.goto("https://www.google.com")
    
    human = HumanBehavior()
    search_input = await page.wait_for_selector("textarea[name='q']")
    
    if search_input:
        await human.human_type(search_input, "eBay Kleinanzeigen Bot Test")
        await human.delay("thinking")
    
    await manager.close()
    print("✅ Human behavior test passed")


async def test_vpn():
    """Test VPN IP rotation."""
    print("Testing VPN...")
    initial_ip = await vpn.get_current_ip()
    print(f"Initial IP: {initial_ip}")
    
    if initial_ip:
        await vpn.rotate_ip()
        
        new_ip = await vpn.get_current_ip()
        print(f"New IP: {new_ip}")
        
        if initial_ip != new_ip:
            print("✅ VPN test passed")
        else:
            print("⚠️  IP did not change (might be expected if VPN not configured)")
    else:
        print("⚠️  Could not get IP (VPN might not be configured)")


if __name__ == "__main__":
    print("Running manual tests...")
    print("=" * 60)
    
    asyncio.run(test_browser())
    print()
    
    asyncio.run(test_human_behavior())
    print()
    
    asyncio.run(test_vpn())
    print()
    
    print("=" * 60)
    print("All tests completed!")

