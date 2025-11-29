"""
Custom logger setup with clean, minimal output.
"""

import sys
from pathlib import Path

from loguru import logger

from src.config.settings import settings


def setup_logger(debug: bool = False) -> None:
    """Configure loguru with clean, minimal output."""
    
    # Remove default handler
    logger.remove()
    
    # Console: Emoji-based, minimal
    level = "DEBUG" if debug else settings.log_level
    logger.add(
        sys.stdout,
        format="<level>{level.icon}</level> <level>{message}</level>",
        level=level,
        colorize=True,
    )
    
    # File: Structured, detailed
    settings.logs_dir.mkdir(exist_ok=True)
    logger.add(
        settings.logs_dir / "bot.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
        level="DEBUG",  # Always DEBUG in file
        rotation=settings.log_rotation,
        retention=settings.log_retention,
        compression="zip",
    )
    
    # Add level icons
    logger.level("DEBUG", icon="🔍")
    logger.level("INFO", icon="✅")
    logger.level("WARNING", icon="⚠️")
    logger.level("ERROR", icon="❌")
    logger.level("CRITICAL", icon="🔥")

