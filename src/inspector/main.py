import asyncio
import time
import uuid
import os
import tempfile
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse

from playwright.async_api import async_playwright, Browser, BrowserContext, Page, TimeoutError as PlaywrightTimeoutError

from core.types import Inspector as InspectorInterface, PageResult, Bug, Evidence
from inspector.utils.evidence import EvidenceCollector
from inspector.utils.performance import PerformanceTracker
from inspector.playwright_helpers.page_setup import PageSetup
from inspector.playwright_helpers.link_detection import LinkDetector
from inspector.checks.structured_explorer import StructuredExplorer


class Inspector(InspectorInterface):
    """
    Singleton Inspector that provides a simple interface for the orchestrator.
    
    Just call inspector.inspect_page(url) and get back a PageResult with findings
    across multiple viewports and all configured checks.
    """
    
    _instance: Optional['Inspector'] = None
    _browser: Optional[Browser] = None
    _playwright = None
    
    # Default timeouts
    DEFAULT_TIMEOUTS = {
        "nav_ms": 30000,    # 30 seconds for navigation
        "action_ms": 5000   # 5 seconds for interactions
    }
    
    def __new__(cls, testing_mode: bool = False) -> 'Inspector':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
            cls._instance._testing_mode = testing_mode
        return cls._instance
    
    def __init__(self, testing_mode: bool = False):
        if self._initialized:
            return
            
        self.testing_mode = testing_mode
        
        # Set output directory based on testing mode
        if self.testing_mode:
            # Use permanent location relative to project directory
            current_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))  # Go up to project root
            self.output_dir = os.path.join(current_dir, "mantis_test_output")
            os.makedirs(self.output_dir, exist_ok=True)
            print(f"🧪 Testing mode: Images will be saved to {self.output_dir}")
        else:
            # Use temporary directory for production
            self.output_dir = tempfile.mkdtemp(prefix="mantis_")
        
        self._initialized = True
    
    @classmethod
    async def get_instance(cls, testing_mode: bool = False) -> 'Inspector':
        """Get the singleton instance and ensure browser is ready"""
        instance = cls(testing_mode=testing_mode)
        await instance._ensure_browser_ready()
        return instance
    
    async def _ensure_browser_ready(self):
        """Ensure the browser is launched and ready"""
        if self._browser is None or not self._browser.is_connected():
            if self._playwright is None:
                self._playwright = await async_playwright().start()
            
            self._browser = await self._playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage']  # Better for containers
            )
    
    async def inspect_page(self, url: str) -> PageResult:
        """
        Inspect a single page and return comprehensive results.
        
        Args:
            url: The URL to inspect
            
        Returns:
            PageResult with all findings from structured exploration
        """
        await self._ensure_browser_ready()
        
        context = None
        try:
            # Create browser context
            context = await self._create_context()
            
            # Set up page
            page = await context.new_page()
            page_setup = PageSetup(page, url, self.DEFAULT_TIMEOUTS)
            
            # Navigate to URL
            navigation_start = time.time()
            success = await page_setup.navigate_safely()
            
            if not success:
                result = PageResult(page_url=url)
                result.findings.append(Bug(
                    id=str(uuid.uuid4()),
                    type="Logic",
                    severity="high", 
                    page_url=url,
                    summary="Failed to navigate to page",
                    suggested_fix="Check if URL is accessible and valid"
                ))
                return result
            
            # Get response status
            status = await page_setup.get_response_status()
            
            # Create structured explorer and run comprehensive exploration
            explorer = StructuredExplorer(self.output_dir)
            result = await explorer.run_complete_exploration(page, url)
            
            # Add navigation timing and status from setup
            result.status = status
            if not result.timings.get('navigation_duration'):
                result.timings['navigation_duration'] = (time.time() - navigation_start) * 1000
            
        except PlaywrightTimeoutError:
            result = PageResult(page_url=url)
            result.findings.append(Bug(
                id=str(uuid.uuid4()),
                type="UI",
                severity="medium",
                page_url=url,
                summary="Page navigation or loading timeout",
                suggested_fix="Check page performance and loading speed"
            ))
            
        except Exception as e:
            result = PageResult(page_url=url)
            result.findings.append(Bug(
                id=str(uuid.uuid4()),
                type="Logic", 
                severity="high",
                page_url=url,
                summary=f"Inspector error: {str(e)}",
                suggested_fix="Review page structure and inspector compatibility"
            ))
            
        finally:
            if context:
                await context.close()
                
        return result
    
    async def _create_context(self) -> BrowserContext:
        """Create a browser context with sensible defaults"""
        return await self._browser.new_context(
            viewport=None,  # We'll set viewport per check
            user_agent='Mantis-UI-Inspector/1.0',
            ignore_https_errors=True,  # Be lenient with SSL issues
            extra_http_headers={
                'Accept-Language': 'en-US,en;q=0.9'
            }
        )
    
    
    async def close(self):
        """Clean up resources"""
        if self._browser and self._browser.is_connected():
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        
        # Reset singleton state
        Inspector._instance = None
        Inspector._browser = None
        Inspector._playwright = None
    
    def __del__(self):
        """Cleanup on deletion"""
        if hasattr(self, 'output_dir') and os.path.exists(self.output_dir) and not self.testing_mode:
            import shutil
            try:
                shutil.rmtree(self.output_dir)
            except:
                pass  # Best effort cleanup


# Convenience function for getting the singleton
async def get_inspector(testing_mode: bool = False) -> Inspector:
    """Get the singleton Inspector instance"""
    return await Inspector.get_instance(testing_mode=testing_mode)