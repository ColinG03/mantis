import asyncio
from typing import Optional
from urllib.parse import urlparse

from playwright.async_api import Page, Response, TimeoutError as PlaywrightTimeoutError

from ...core.types import InspectorOptions


class PageSetup:
    """
    Handles safe page navigation and initial setup for inspection.
    """
    
    def __init__(self, page: Page, opts: InspectorOptions):
        self.page = page
        self.opts = opts
        self.response: Optional[Response] = None
        
    async def navigate_safely(self) -> bool:
        """
        Navigate to the target URL with proper timeout and error handling.
        
        Returns:
            True if navigation successful, False otherwise
        """
        try:
            # Set up console and error logging
            await self._setup_logging()
            
            # Navigate with timeout
            nav_timeout = self.opts.timeouts.get('nav_ms', 30000)
            self.response = await self.page.goto(
                self.opts.url,
                wait_until='domcontentloaded',
                timeout=nav_timeout
            )
            
            # Wait for additional load events
            await self._wait_for_page_ready()
            
            return True
            
        except PlaywrightTimeoutError:
            print(f"Navigation timeout for {self.opts.url}")
            return False
        except Exception as e:
            print(f"Navigation error for {self.opts.url}: {str(e)}")
            return False
    
    async def get_response_status(self) -> Optional[int]:
        """Get the HTTP response status code"""
        return self.response.status if self.response else None
    
    async def _setup_logging(self):
        """Set up console and error event listeners"""
        
        def handle_console(msg):
            # Store console messages for later analysis
            # You might want to filter by log level (error, warn, etc.)
            pass
        
        def handle_page_error(error):
            # Store JavaScript errors
            pass
        
        def handle_request_failed(request):
            # Store failed network requests
            pass
        
        self.page.on("console", handle_console)
        self.page.on("pageerror", handle_page_error)
        self.page.on("requestfailed", handle_request_failed)
    
    async def _wait_for_page_ready(self):
        """
        Wait for page to be fully ready for inspection.
        This includes waiting for:
        - DOM content loaded
        - Network idle
        - Any custom readiness indicators
        """
        try:
            # Wait for network to be mostly idle
            await self.page.wait_for_load_state('networkidle', timeout=10000)
            
            # Wait for any lazy-loaded content
            await asyncio.sleep(1)
            
            # Check for common loading indicators and wait for them to disappear
            loading_selectors = [
                '.loading',
                '.spinner',
                '[data-loading="true"]',
                '.loader'
            ]
            
            for selector in loading_selectors:
                try:
                    # Wait for loading indicators to be hidden (if they exist)
                    await self.page.wait_for_selector(
                        selector, 
                        state='hidden', 
                        timeout=5000
                    )
                except PlaywrightTimeoutError:
                    # Loading indicator might not exist, continue
                    continue
                    
        except PlaywrightTimeoutError:
            # Page might still be loading, but we'll proceed with inspection
            pass
    
    async def is_same_origin(self, url: str) -> bool:
        """
        Check if a URL is from the same origin as the seed host.
        
        Args:
            url: URL to check
            
        Returns:
            True if same origin (when same_host_only is enabled)
        """
        if not self.opts.same_host_only:
            return True
            
        try:
            parsed_url = urlparse(url)
            return parsed_url.netloc == self.opts.seed_host
        except Exception:
            return False
    
    async def scroll_to_reveal_content(self):
        """
        Perform gentle scrolling to reveal lazy-loaded content.
        This is useful for checks that need to see the full page.
        """
        try:
            # Get page height
            page_height = await self.page.evaluate("document.body.scrollHeight")
            viewport_height = await self.page.evaluate("window.innerHeight")
            
            # Scroll in chunks to trigger lazy loading
            scroll_position = 0
            scroll_step = viewport_height // 2
            
            while scroll_position < page_height:
                await self.page.evaluate(f"window.scrollTo(0, {scroll_position})")
                await asyncio.sleep(0.5)  # Allow content to load
                scroll_position += scroll_step
                
                # Update page height in case new content was loaded
                page_height = await self.page.evaluate("document.body.scrollHeight")
            
            # Scroll back to top
            await self.page.evaluate("window.scrollTo(0, 0)")
            await asyncio.sleep(0.5)
            
        except Exception as e:
            print(f"Error during scroll reveal: {str(e)}")
