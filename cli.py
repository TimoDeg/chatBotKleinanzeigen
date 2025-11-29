#!/usr/bin/env python3
"""
CLI entry point using Typer for command-line interface.
"""

import asyncio
import sys

import typer
from loguru import logger

from src.core.bot import KleinanzeigenBot
from src.utils.logger import setup_logger
from src.config.constants import EXIT_CODES

app = typer.Typer(
    help="eBay Kleinanzeigen Bot v2.0",
    add_completion=False,
)


@app.command()
def run(
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
    shipping_cost: float = typer.Option(
        None,
        "--shipping-cost",
        help="Shipping cost (optional, only if shipping selected)",
    ),
    note: str = typer.Option(
        None,
        "--note",
        "-n",
        help="Additional offer note (optional)",
    ),
):
    """Execute bot workflow."""
    setup_logger()
    
    logger.info("🚀 Kleinanzeigen Bot v2.0")
    logger.info(f"URL: {url}")
    logger.info(f"Offer: €{price} ({delivery})")
    
    bot = KleinanzeigenBot(email, password)
    result = asyncio.run(
        bot.execute_workflow(url, message, price, delivery, shipping_cost, note)
    )
    
    if result["success"]:
        logger.info("✅ Workflow completed successfully")
        sys.exit(EXIT_CODES["SUCCESS"])
    else:
        logger.error(f"❌ Workflow failed: {', '.join(result['errors'])}")
        sys.exit(EXIT_CODES["BROWSER_FAILED"])


if __name__ == "__main__":
    app()
