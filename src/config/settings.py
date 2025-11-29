"""
Application settings using Pydantic for environment-based configuration.
"""

from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Paths
    cookies_path: Path = Path("./cookies.json")
    logs_dir: Path = Path("./logs")
    screenshots_dir: Path = Path("./screenshots")
    
    # Browser
    headless: bool = False  # Changed default to False for better anti-detection
    browser_timeout: int = 30
    
    # Delays (human-like ranges in seconds)
    delay_typing_min: float = 0.05
    delay_typing_max: float = 0.15
    delay_reading_min: float = 2.0
    delay_reading_max: float = 5.0
    delay_thinking_min: float = 3.0
    delay_thinking_max: float = 8.0
    delay_navigating_min: float = 1.5
    delay_navigating_max: float = 4.0
    
    # VPN
    vpn_enabled: bool = True
    vpn_rotation_probability: float = 0.3  # 30% chance
    vpn_countries: List[str] = ["de", "nl", "se", "ch", "at"]
    
    # Logging
    log_level: str = "INFO"
    log_rotation: str = "10 MB"
    log_retention: str = "7 days"
    
    # Retry
    max_retries: int = 3
    retry_backoff: int = 5
    
    class Config:
        env_file = ".env"
        env_prefix = "BOT_"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from .env


# Global settings instance
settings = Settings()

