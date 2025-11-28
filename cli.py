#!/usr/bin/env python3
"""
CLI entry point using Typer for command-line interface.
"""

import asyncio
import sys
from typing import Optional

import typer
from loguru import logger

from src.bot import KleinanzeigenBot
from src.config import (
    EXIT_SUCCESS,
    EXIT_LOGIN_FAILED,
    EXIT_MESSAGE_FAILED,
    EXIT_CONVERSATION_NOT_FOUND,
    EXIT_OFFER_FAILED,
    EXIT_BROWSER_FAILED,
    EXIT_CAPTCHA_DETECTED,
)
from src.utils import setup_logging

app = typer.Typer(
    name="kleinanzeigen-bot",
    help="eBay Kleinanzeigen Message & Offer Bot",
    add_completion=False,
)


@app.command("send-and-offer")
def send_and_offer(
    url: str = typer.Option(..., "--url", "-u", help="Kleinanzeigen listing URL"),
    email: str = typer.Option(..., "--email", "-e", help="Your Kleinanzeigen email"),
    password: str = typer.Option(..., "--password", "-p", help="Your Kleinanzeigen password"),
    message: str = typer.Option(..., "--message", "-m", help="Message text to send"),
    price: float = typer.Option(..., "--price", help="Offer price in EUR"),
    delivery: str = typer.Option(
        ...,
        "--delivery",
        "-d",
        help='Delivery method: "pickup" / "shipping" / "both"',
    ),
    shipping_cost: Optional[float] = typer.Option(
        None,
        "--shipping-cost",
        help="Shipping cost (optional, only if shipping selected)",
    ),
    note: Optional[str] = typer.Option(
        None,
        "--note",
        "-n",
        help="Additional offer note (optional)",
    ),
    headless: bool = typer.Option(
        True,
        "--headless/--no-headless",
        help="Run browser in headless mode (default: True)",
    ),
    no_cookies: bool = typer.Option(
        False,
        "--no-cookies",
        help="Force fresh login (ignore saved cookies)",
    ),
    screenshot: bool = typer.Option(
        False,
        "--screenshot",
        help="Save screenshot after success",
    ),
    timeout: int = typer.Option(
        30,
        "--timeout",
        "-t",
        help="Max wait time in seconds (default: 30)",
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        help="Enable DEBUG logging",
    ),
):
    """
    Send a message to a Kleinanzeigen listing and make an offer.
    
    This command performs the complete workflow:
    1. Login (or use saved cookies)
    2. Send message to listing
    3. Navigate to conversation
    4. Make offer with specified parameters
    """
    # Setup logging
    setup_logging(debug=debug)
    
    # Validate delivery option
    valid_deliveries = ["pickup", "shipping", "both"]
    if delivery not in valid_deliveries:
        logger.error(f"Invalid delivery option: {delivery}. Must be one of: {valid_deliveries}")
        sys.exit(EXIT_BROWSER_FAILED)
    
    # Validate shipping cost
    if shipping_cost and delivery == "pickup":
        logger.warning("Shipping cost specified but delivery is 'pickup'. Ignoring shipping cost.")
        shipping_cost = None
    
    # Print configuration
    logger.info("=" * 60)
    logger.info("Kleinanzeigen Message & Offer Bot")
    logger.info("=" * 60)
    logger.info(f"URL: {url}")
    logger.info(f"Email: {email}")
    logger.info(f"Message: {message[:50]}...")
    logger.info(f"Offer: €{price}, Delivery: {delivery}")
    if shipping_cost:
        logger.info(f"Shipping Cost: €{shipping_cost}")
    if note:
        logger.info(f"Note: {note[:50]}...")
    logger.info(f"Headless: {headless}")
    logger.info("=" * 60)
    
    # Create bot instance
    bot = KleinanzeigenBot(
        email=email,
        password=password,
        headless=headless,
        timeout=timeout,
    )
    
    # Set debug mode
    bot.debug_mode = debug
    
    # Execute workflow
    try:
        result = asyncio.run(
            bot.execute_full_workflow(
                listing_url=url,
                message=message,
                price=price,
                delivery=delivery,
                shipping_cost=shipping_cost,
                note=note,
                force_fresh_login=no_cookies,
                save_screenshot=screenshot,
                debug_mode=debug,
            )
        )
        
        # Print results
        logger.info("=" * 60)
        logger.info("Workflow Results:")
        logger.info("=" * 60)
        logger.info(f"Browser Setup: {'✅' if result['browser_setup'] else '❌'}")
        logger.info(f"Authentication: {'✅' if result['authentication'] else '❌'}")
        logger.info(f"Message Sent: {'✅' if result['message_sent'] else '❌'}")
        logger.info(f"Conversation Opened: {'✅' if result['conversation_opened'] else '❌'}")
        logger.info(f"Offer Sent: {'✅' if result['offer_sent'] else '❌'}")
        logger.info("=" * 60)
        
        # Exit with appropriate code
        exit_code = result["exit_code"]
        
        if exit_code == EXIT_SUCCESS:
            logger.info("✅ All steps completed successfully!")
        else:
            logger.error(f"❌ Workflow failed with exit code: {exit_code}")
        
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        logger.warning("⚠️ Interrupted by user")
        sys.exit(EXIT_BROWSER_FAILED)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        sys.exit(EXIT_BROWSER_FAILED)


if __name__ == "__main__":
    app()

