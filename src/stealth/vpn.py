"""
Mullvad VPN integration for IP rotation.
"""

import asyncio
import random
import subprocess
from typing import Optional

from loguru import logger

from src.config.settings import settings


class VPNManager:
    """Manage Mullvad VPN connection and IP rotation."""
    
    def __init__(self):
        """Initialize VPNManager."""
        self.current_ip: Optional[str] = None
        self._mullvad_available: Optional[bool] = None
    
    async def _check_mullvad_available(self) -> bool:
        """
        Check if Mullvad CLI is available.
        
        Returns:
            True if Mullvad CLI is available, False otherwise
        """
        if self._mullvad_available is not None:
            return self._mullvad_available
        
        try:
            proc = await asyncio.create_subprocess_exec(
                "mullvad", "version",
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            await proc.wait()
            self._mullvad_available = (proc.returncode == 0)
        except FileNotFoundError:
            self._mullvad_available = False
        except Exception:
            self._mullvad_available = False
        
        return self._mullvad_available
    
    async def rotate_ip(self) -> bool:
        """
        Rotate to new VPN server.
        
        Returns:
            True if successful, False otherwise
        """
        if not settings.vpn_enabled:
            logger.debug("VPN rotation disabled in config")
            return True
        
        try:
            logger.info("🔄 Rotating VPN IP...")
            
            # Disconnect
            proc = await asyncio.create_subprocess_exec(
                "mullvad", "disconnect",
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            await proc.wait()
            await asyncio.sleep(2)
            
            # Select random relay
            country = random.choice(settings.vpn_countries)
            proc = await asyncio.create_subprocess_exec(
                "mullvad", "relay", "set", "location", country,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            await proc.wait()
            await asyncio.sleep(1)
            
            # Reconnect
            proc = await asyncio.create_subprocess_exec(
                "mullvad", "connect",
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            await proc.wait()
            await asyncio.sleep(5)  # Wait for stable connection
            
            # Verify new IP
            new_ip = await self.get_current_ip()
            if new_ip and new_ip != self.current_ip:
                logger.info(f"✅ VPN rotated: {country.upper()} → {new_ip}")
                self.current_ip = new_ip
                return True
            else:
                logger.warning("⚠️  IP did not change")
                return False
            
        except FileNotFoundError:
            logger.warning("⚠️  Mullvad CLI not found. VPN rotation skipped.")
            return False
        except Exception as e:
            logger.error(f"❌ VPN rotation failed: {e}")
            return False
    
    async def get_current_ip(self) -> Optional[str]:
        """
        Get current public IP address.
        
        Returns:
            IP address string or None if failed
        """
        try:
            proc = await asyncio.create_subprocess_exec(
                "curl", "-s", "ifconfig.me",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL
            )
            stdout, _ = await proc.communicate()
            ip = stdout.decode().strip()
            return ip if ip else None
        except Exception as e:
            logger.debug(f"Failed to get IP: {e}")
            return None
    
    async def should_rotate(self) -> bool:
        """
        Decide if IP should be rotated (based on probability).
        
        Returns:
            True if should rotate, False otherwise
        """
        return random.random() < settings.vpn_rotation_probability


# Global VPN manager instance
vpn = VPNManager()

