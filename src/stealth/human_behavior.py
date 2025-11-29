"""
Human-like behavior simulation: delays, mouse movements, typing, scrolling.
"""

import asyncio
import random
from typing import Literal, Optional

from playwright.async_api import Page, ElementHandle
from loguru import logger

from src.config.settings import settings

ActionType = Literal["typing", "reading", "thinking", "navigating", "default"]


class HumanBehavior:
    """Simulates human-like behavior for bot actions."""
    
    @staticmethod
    async def delay(
        action_type: ActionType = "default",
        fast_mode: bool = False,
    ) -> None:
        """
        Human-like delay with optional fast mode.
        
        Args:
            action_type: Type of action for context-appropriate delay
            fast_mode: If True, use minimal delays (0.3-0.8s)
        """
        if fast_mode:
            delay = random.uniform(0.3, 0.8)
            # Only log if > 0.5s
            if delay > 0.5:
                logger.debug(f"⚡ {delay:.2f}s")
            await asyncio.sleep(delay)
            return
        
        # Normal mode: human-like delays
        delays = {
            "typing": (settings.delay_typing_min, settings.delay_typing_max),
            "reading": (settings.delay_reading_min, settings.delay_reading_max),
            "thinking": (settings.delay_thinking_min, settings.delay_thinking_max),
            "navigating": (settings.delay_navigating_min, settings.delay_navigating_max),
            "default": (1.0, 2.0),
        }
        
        min_s, max_s = delays.get(action_type, delays["default"])
        
        # 10% chance for longer "thinking pause"
        if random.random() < 0.1:
            min_s *= 1.5
            max_s *= 2.0
        
        delay = random.uniform(min_s, max_s)
        
        # Only log if > 2 seconds
        if delay > 2.0:
            logger.debug(f"⏳ {delay:.2f}s ({action_type})")
        
        await asyncio.sleep(delay)
    
    @staticmethod
    def _bezier_curve(t: float) -> float:
        """
        Cubic Bezier curve for smooth easing (ease-in-out).
        
        Args:
            t: Parameter from 0 to 1
            
        Returns:
            Eased value from 0 to 1
        """
        return t * t * (3 - 2 * t)
    
    @staticmethod
    async def mouse_move_to_element(page: Page, element: ElementHandle) -> None:
        """
        Move mouse to element using Bezier curve with random jitter.
        
        Args:
            page: Playwright page
            element: Target element
        """
        try:
            # Get element bounding box
            box = await element.bounding_box()
            if not box:
                return
            
            # Target position (center of element with small random offset)
            target_x = box["x"] + box["width"] / 2 + random.uniform(-5, 5)
            target_y = box["y"] + box["height"] / 2 + random.uniform(-5, 5)
            
            # Start from random position (not current mouse position)
            start_x = random.uniform(100, 500)
            start_y = random.uniform(100, 400)
            
            # Generate Bezier curve with 5-10 steps
            steps = random.randint(5, 10)
            
            for i in range(steps + 1):
                t = i / steps
                # Apply easing
                eased_t = HumanBehavior._bezier_curve(t)
                
                # Calculate position along curve
                x = start_x + (target_x - start_x) * eased_t
                y = start_y + (target_y - start_y) * eased_t
                
                # Add random jitter
                x += random.uniform(-5, 5)
                y += random.uniform(-5, 5)
                
                await page.mouse.move(x, y)
                
                # Variable delay between steps (10-30ms)
                await asyncio.sleep(random.uniform(0.01, 0.03))
            
            # Final hover before click (100-300ms)
            await asyncio.sleep(random.uniform(0.1, 0.3))
            
        except Exception as e:
            logger.debug(f"Mouse movement failed: {e}")
    
    @staticmethod
    async def human_click(page: Page, element: ElementHandle) -> None:
        """
        Perform human-like click with mouse movement and occasional misclicks.
        
        Args:
            page: Playwright page
            element: Element to click
        """
        try:
            # Move mouse to element first
            await HumanBehavior.mouse_move_to_element(page, element)
            
            # 5% chance for misclick (offset -20 to -10px) + retry
            if random.random() < 0.05:
                box = await element.bounding_box()
                if box:
                    misclick_x = box["x"] + box["width"] / 2 + random.uniform(-20, -10)
                    misclick_y = box["y"] + box["height"] / 2 + random.uniform(-20, -10)
                    await page.mouse.click(misclick_x, misclick_y)
                    await asyncio.sleep(random.uniform(0.2, 0.5))
            
            # Actual click with slight random offset
            box = await element.bounding_box()
            if box:
                click_x = box["x"] + box["width"] / 2 + random.uniform(-3, 3)
                click_y = box["y"] + box["height"] / 2 + random.uniform(-3, 3)
                await page.mouse.click(click_x, click_y)
            else:
                await element.click()
            
            # Post-click delay
            await asyncio.sleep(random.uniform(0.2, 0.5))
            
        except Exception as e:
            logger.debug(f"Human click failed, using fallback: {e}")
            try:
                await element.click()
            except:
                pass
    
    @staticmethod
    async def scroll_into_view(page: Page, element: ElementHandle) -> None:
        """
        Scroll element into view with incremental, human-like scrolling.
        
        Args:
            page: Playwright page
            element: Element to scroll to
        """
        try:
            box = await element.bounding_box()
            if not box:
                return
            
            # Get current scroll position
            current_scroll = await page.evaluate("() => window.pageYOffset")
            target_y = box["y"] - 200  # Scroll to show element with 200px offset
            
            # Calculate scroll distance
            scroll_distance = target_y - current_scroll
            
            if abs(scroll_distance) < 50:
                return  # Already in view
            
            # Incremental scroll (simulate scroll wheel)
            steps = max(5, int(abs(scroll_distance) / 100))
            step_size = scroll_distance / steps
            
            for i in range(steps):
                await page.evaluate(f"window.scrollBy(0, {step_size})")
                await asyncio.sleep(random.uniform(0.05, 0.15))
            
            # Small random offset (not perfect centering)
            await page.evaluate(f"window.scrollBy(0, {random.uniform(-50, 50)})")
            await asyncio.sleep(random.uniform(0.2, 0.4))
            
        except Exception as e:
            logger.debug(f"Scroll into view failed: {e}")
            try:
                await element.scroll_into_view_if_needed()
            except:
                pass
    
    @staticmethod
    async def human_type(element: ElementHandle, text: str) -> None:
        """
        Type text character-by-character with human-like behavior.
        
        Features:
        - Variable typing speed (80-150ms base, ±30-50ms variance)
        - 3% chance of typo + backspace correction
        - 8% chance of thinking pause (0.5-1.5s)
        - Faster typing mid-word, slower at word boundaries
        
        Args:
            element: Input element to type into
            text: Text to type
        """
        try:
            await element.click()  # Focus
            await asyncio.sleep(random.uniform(0.2, 0.5))
            
            for i, char in enumerate(text):
                # Typo simulation (3% chance)
                if random.random() < 0.03 and i > 0:
                    wrong_char = random.choice("abcdefghijklmnopqrstuvwxyz")
                    await element.type(wrong_char, delay=random.uniform(50, 150))
                    await asyncio.sleep(random.uniform(0.1, 0.3))
                    await element.press("Backspace")
                    await asyncio.sleep(random.uniform(0.1, 0.2))
                
                # Variable speed (faster mid-word, slower at word boundaries)
                if char == " " or i == 0:
                    base_delay = 120  # Slower at word boundaries
                else:
                    base_delay = 80  # Faster mid-word
                
                delay = base_delay + random.uniform(-30, 50)
                await element.type(char, delay=delay)
                
                # Thinking pauses (8% chance)
                if random.random() < 0.08:
                    await asyncio.sleep(random.uniform(0.5, 1.5))
                    
        except Exception as e:
            logger.debug(f"Human type failed, using fallback: {e}")
            try:
                await element.fill(text)
            except:
                pass

