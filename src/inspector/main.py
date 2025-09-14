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
from inspector.checks.accessibility_scanner import AccessibilityScanner
from inspector.checks.performance_scanner import PerformanceScanner
from inspector.checks.base_scanner import ScanConfig


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
    
    def __new__(cls, testing_mode: bool = False, scan_config: ScanConfig = None) -> 'Inspector':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
            cls._instance._testing_mode = testing_mode
        return cls._instance
    
    def __init__(self, testing_mode: bool = False, scan_config: ScanConfig = None):
        if self._initialized:
            return
            
        self.testing_mode = testing_mode
        self.scan_config = scan_config or ScanConfig.all_scans()
        
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
    async def get_instance(cls, testing_mode: bool = False, scan_config: ScanConfig = None) -> 'Inspector':
        """Get the singleton instance and ensure browser is ready"""
        instance = cls(testing_mode=testing_mode, scan_config=scan_config)
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
    
    async def inspect_page(self, url: str, scan_config: ScanConfig = None) -> PageResult:
        """
        Inspect a single page and return comprehensive results.
        
        Args:
            url: The URL to inspect
            scan_config: Optional scan configuration (uses instance default if not provided)
            
        Returns:
            PageResult with all findings from configured scans
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
            
            # Use provided scan config or instance default
            config = scan_config or self.scan_config
            
            # Initialize result
            result = PageResult(page_url=url)
            result.status = status
            result.timings['navigation_duration'] = (time.time() - navigation_start) * 1000
            
            # Run accessibility scan if enabled
            if config.accessibility:
                await self._run_accessibility_scan(page, url, result)
            
            # Run performance scan if enabled
            if config.performance:
                await self._run_performance_scan(page, url, result)
            
            # Collect outlinks and navigation metadata (always needed for crawling and action recording)
            link_detector = LinkDetector(page, url)
            result.outlinks = await link_detector.collect_outlinks()
            result.navigation_metadata = await link_detector.get_navigation_metadata()
            
            # Run comprehensive UI scans (visual + interactive) if enabled
            if config.ui_scans:
                await self._run_ui_scans(page, url, result, config)
            
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
    
    async def _run_accessibility_scan(self, page: Page, url: str, result: PageResult):
        """Run accessibility scan and merge results"""
        try:
            print(f"🔍 Running accessibility scan for {url}")
            accessibility_scanner = AccessibilityScanner(self.output_dir)
            
            # Run multi-viewport accessibility scan to catch responsive design issues
            accessibility_result = await accessibility_scanner.scan_all_viewports(page, url)
            accessibility_result.merge_into_page_result(result)
            
        except Exception as e:
            print(f"❌ Accessibility scan failed: {str(e)}")
            # Add error bug
            error_bug = Bug(
                id=str(uuid.uuid4()),
                type="Accessibility",
                severity="medium",
                page_url=url,
                summary=f"Accessibility scan error: {str(e)}",
                suggested_fix="Review accessibility scanner configuration"
            )
            result.findings.append(error_bug)
    
    async def _run_performance_scan(self, page: Page, url: str, result: PageResult):
        """Run performance scan and merge results"""
        try:
            print(f"⚡ Running performance scan for {url}")
            performance_scanner = PerformanceScanner(self.output_dir)
            
            # Run performance scan across multiple viewports to catch responsive performance issues
            viewports = ["1280x800", "768x1024", "375x667"]  # Desktop, tablet, mobile
            
            for viewport in viewports:
                # Parse viewport dimensions
                width, height = map(int, viewport.split('x'))
                
                # Set viewport
                await page.set_viewport_size({"width": width, "height": height})
                
                # Wait for any layout changes to settle
                await page.wait_for_timeout(500)
                
                # Run performance scan for this viewport
                perf_result = await performance_scanner.scan(page, url, viewport)
                perf_result.merge_into_page_result(result)
            
            # Also collect the performance timing data into the result
            performance_tracker = PerformanceTracker()
            timing_data = await performance_tracker.collect_timings(page)
            result.timings.update(timing_data)
            
        except Exception as e:
            print(f"❌ Performance scan failed: {str(e)}")
            # Add error bug
            error_bug = Bug(
                id=str(uuid.uuid4()),
                type="Performance",
                severity="medium",
                page_url=url,
                summary=f"Performance scan error: {str(e)}",
                suggested_fix="Review performance scanner configuration and page accessibility"
            )
            result.findings.append(error_bug)
    
    async def _run_ui_scans(self, page: Page, url: str, result: PageResult, config: ScanConfig):
        """Run comprehensive UI scans"""
        try:
            print(f"🔍 Running comprehensive UI exploration for {url}")
            
            # Create structured explorer
            explorer = StructuredExplorer(self.output_dir, config.model)
            
            # Pass navigation metadata for better action recording
            explorer.navigation_metadata = result.navigation_metadata
            
            # Always run complete exploration (visual + interactive)
            explorer_result = await explorer.run_complete_exploration(page, url)
            
            # Merge results
            result.findings.extend(explorer_result.findings)
            result.timings.update(explorer_result.timings)
            result.viewport_artifacts.extend(explorer_result.viewport_artifacts)
            
        except Exception as e:
            print(f"❌ UI scan failed: {str(e)}")
            # Add error bug
            error_bug = Bug(
                id=str(uuid.uuid4()),
                type="UI",
                severity="medium",
                page_url=url,
                summary=f"UI scan error: {str(e)}",
                suggested_fix="Review UI scanner configuration"
            )
            result.findings.append(error_bug)
    
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
async def get_inspector(testing_mode: bool = False, scan_config: ScanConfig = None) -> Inspector:
    """Get the singleton Inspector instance"""
    return await Inspector.get_instance(testing_mode=testing_mode, scan_config=scan_config)