"""
ScrollManager handles scrolling logic for viewport-based exploration.
"""

import asyncio
from typing import Dict, Any
from playwright.async_api import Page


class ScrollManager:
    """
    Manages scrolling behavior for comprehensive page exploration.
    
    This class handles:
    - Detecting if a page is scrollable
    - Managing scroll positions with configurable overlap
    - Smart termination when reaching page bottom
    - Dynamic content detection
    """
    
    def __init__(self, page: Page, viewport_height: int, config: Dict[str, Any] = None):
        """
        Initialize scroll manager.
        
        Args:
            page: Playwright page object
            viewport_height: Height of the current viewport in pixels
            config: Optional configuration dict with scroll settings
        """
        self.page = page
        self.viewport_height = viewport_height
        
        # Default configuration
        default_config = {
            'max_scrolls': 10,
            'overlap_percentage': 20,
            'dynamic_content_detection': True,
            'scroll_delay': 0.5  # seconds to wait after scrolling
        }
        
        self.config = {**default_config, **(config or {})}
        
        # Calculate scroll amount (80% of viewport height for 20% overlap)
        overlap_factor = (100 - self.config['overlap_percentage']) / 100
        self.scroll_amount = int(self.viewport_height * overlap_factor)
        
        # State tracking
        self.current_position = 0
        self.total_scrollable_height = 0
        self.last_content_height = 0
        self.scroll_iterations = 0
        
    async def initialize(self) -> bool:
        """
        Initialize scroll manager by detecting page scrollability.
        
        Returns:
            True if page is scrollable, False otherwise
        """
        try:
            # Get initial page dimensions and scroll position
            scroll_data = await self.page.evaluate("""
            () => {
                return {
                    scrollTop: window.pageYOffset || document.documentElement.scrollTop,
                    scrollHeight: document.body.scrollHeight,
                    clientHeight: document.documentElement.clientHeight,
                    windowHeight: window.innerHeight
                };
            }
            """)
            
            self.current_position = scroll_data['scrollTop']
            self.total_scrollable_height = scroll_data['scrollHeight']
            self.last_content_height = scroll_data['scrollHeight']
            
            # Page is scrollable if content height > viewport height
            viewport_height = max(scroll_data['clientHeight'], scroll_data['windowHeight'])
            is_scrollable = self.total_scrollable_height > viewport_height
            
            if is_scrollable:
                print(f"    📏 Page is scrollable: {self.total_scrollable_height}px total, {viewport_height}px viewport")
                print(f"    📐 Scroll amount: {self.scroll_amount}px ({self.config['overlap_percentage']}% overlap)")
            else:
                print(f"    📏 Page fits in viewport: {self.total_scrollable_height}px total")
            
            return is_scrollable
            
        except Exception as e:
            print(f"    ⚠️  Failed to initialize scroll manager: {str(e)}")
            return False
    
    async def scroll_to_next_position(self) -> bool:
        """
        Scroll to the next position in the exploration sequence.
        
        Returns:
            True if scrolled successfully, False if reached bottom or max iterations
        """
        # Check if we've reached maximum iterations
        if self.scroll_iterations >= self.config['max_scrolls']:
            print(f"    📜 Reached maximum scroll iterations ({self.config['max_scrolls']})")
            return False
        
        # Calculate next scroll position
        next_position = self.current_position + self.scroll_amount
        
        # Check if we can actually scroll further
        can_scroll_more = await self._can_scroll_to_position(next_position)
        if not can_scroll_more:
            print(f"    📜 Reached bottom of page at position {self.current_position}px")
            return False
        
        # Perform the scroll
        try:
            await self.page.evaluate(f"window.scrollTo(0, {next_position})")
            await asyncio.sleep(self.config['scroll_delay'])
            
            # Update current position
            actual_position = await self.page.evaluate("() => window.pageYOffset || document.documentElement.scrollTop")
            self.current_position = actual_position
            self.scroll_iterations += 1
            
            print(f"    📜 Scrolled to position {self.current_position}px (iteration {self.scroll_iterations})")
            
            # Check for dynamic content if enabled
            if self.config['dynamic_content_detection']:
                await self._check_for_dynamic_content()
            
            return True
            
        except Exception as e:
            print(f"    ⚠️  Failed to scroll to position {next_position}: {str(e)}")
            return False
    
    async def _can_scroll_to_position(self, position: int) -> bool:
        """
        Check if we can scroll to a specific position.
        
        Args:
            position: Target scroll position in pixels
            
        Returns:
            True if we can scroll to that position, False otherwise
        """
        try:
            # Get current scroll data
            scroll_data = await self.page.evaluate("""
            () => {
                const maxScrollTop = document.body.scrollHeight - window.innerHeight;
                return {
                    maxScrollTop: Math.max(0, maxScrollTop),
                    currentScrollTop: window.pageYOffset || document.documentElement.scrollTop
                };
            }
            """)
            
            # Check if target position is within scrollable range
            max_scroll = scroll_data['maxScrollTop']
            current_scroll = scroll_data['currentScrollTop']
            
            # We can scroll if:
            # 1. Target position is less than max scroll
            # 2. Target position is greater than current position (moving forward)
            can_scroll = position <= max_scroll and position > current_scroll
            
            if not can_scroll:
                print(f"    📜 Cannot scroll to {position}px (max: {max_scroll}px, current: {current_scroll}px)")
            
            return can_scroll
            
        except Exception as e:
            print(f"    ⚠️  Error checking scroll position: {str(e)}")
            return False
    
    async def _check_for_dynamic_content(self):
        """
        Check if dynamic content has been loaded that affects page height.
        Updates scroll limits if new content is detected.
        """
        try:
            current_height = await self.page.evaluate("() => document.body.scrollHeight")
            
            if current_height > self.last_content_height:
                height_diff = current_height - self.last_content_height
                self.total_scrollable_height = current_height
                self.last_content_height = current_height
                print(f"    🔄 Dynamic content detected: +{height_diff}px (total: {current_height}px)")
            
        except Exception as e:
            print(f"    ⚠️  Error checking dynamic content: {str(e)}")
    
    async def reset_to_top(self):
        """Reset scroll position to top of page."""
        try:
            await self.page.evaluate("window.scrollTo(0, 0)")
            await asyncio.sleep(0.3)
            self.current_position = 0
            self.scroll_iterations = 0
            print(f"    📜 Reset to top of page")
            
        except Exception as e:
            print(f"    ⚠️  Failed to reset scroll position: {str(e)}")
    
    def get_scroll_info(self) -> Dict[str, Any]:
        """
        Get current scroll information for debugging/logging.
        
        Returns:
            Dictionary with current scroll state
        """
        return {
            'current_position': self.current_position,
            'total_height': self.total_scrollable_height,
            'scroll_amount': self.scroll_amount,
            'iterations': self.scroll_iterations,
            'max_iterations': self.config['max_scrolls'],
            'overlap_percentage': self.config['overlap_percentage']
        }
