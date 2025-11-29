#!/usr/bin/env python3
"""
CLI entry point using Typer for command-line interface.
"""

import asyncio
import sys
from typing import Optional

import typer
from loguru import logger

from src.core.bot import KleinanzeigenBot
from src.utils.logger import setup_logger

app = typer.Typer(
    help="eBay Kleinanzeigen Bot v2.0",
    add_completion=False,
)


@app.command("run")
def run(
    # Required
    url: str = typer.Option(..., "--url", "-u", help="Listing URL"),
    email: str = typer.Option(..., "--email", "-e", help="Email address"),
    password: str = typer.Option(..., "--password", "-p", help="Password"),
    message: str = typer.Option(..., "--message", "-m", help="Message text"),
    price: float = typer.Option(..., "--price", help="Offer price in EUR"),
    delivery: str = typer.Option(..., "--delivery", "-d", help="Delivery method: pickup/shipping/both"),

    # Optional
    shipping_cost: Optional[float] = typer.Option(None, "--shipping-cost", help="Shipping cost in EUR"),
    note: Optional[str] = typer.Option(None, "--note", "-n", help="Additional note"),
    profile_name: str = typer.Option("User", "--profile-name", help="Profile name for form"),

    # Behavior flags
    headless: bool = typer.Option(True, "--headless/--no-headless", help="Run in headless mode"),
    force_login: bool = typer.Option(False, "--force-login", help="Force fresh login (ignore cookies)"),
    debug: bool = typer.Option(False, "--debug", help="Enable debug logging"),
):
    """Execute bot workflow with offer."""

    # Setup logging
    setup_logger(debug=debug)

    logger.info("🚀 Kleinanzeigen Bot v2.0")
    logger.info(f"URL: {url}")
    logger.info(f"Offer: €{price} ({delivery})")
    logger.info(f"Headless: {headless}")
    if force_login:
        logger.info("⚠️  Force login enabled")

    # Create bot
    bot = KleinanzeigenBot(
        email=email,
        password=password,
        headless=headless,
    )

    # Execute workflow
    result = asyncio.run(
        bot.execute_workflow(
            listing_url=url,
            message=message,
            price=price,
            delivery=delivery,
            shipping_cost=shipping_cost,
            note=note,
            profile_name=profile_name,
            force_fresh_login=force_login,
        )
    )

    # Results
    if result["success"]:
        logger.info("✅✅✅ Workflow completed successfully ✅✅✅")
        raise typer.Exit(0)
    else:
        logger.error(f"❌ Workflow failed: {', '.join(result['errors'])}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()

