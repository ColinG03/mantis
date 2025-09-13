import asyncio
import time
import uuid
import os
import tempfile
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse

from playwright.async_api import async_playwright, Browser, BrowserContext, Page, TimeoutError as PlaywrightTimeoutError

from core.types import Inspector as InspectorInterface, PageResult, Bug, Evidence
from inspector.checks.base import BaseCheck
from inspector.checks.accessibility import AccessibilityCheck
from inspector.checks.visual_layout import VisualLayoutCheck
from inspector.utils.evidence import EvidenceCollector
from inspector.utils.performance import PerformanceTracker
from inspector.playwright_helpers.page_setup import PageSetup
from inspector.playwright_helpers.link_detection import LinkDetector


class Inspector(InspectorInterface):
    """
    Singleton Inspector that provides a simple interface for the orchestrator.
    
    Just call inspector.inspect_page(url) and get back a PageResult with findings
    across multiple viewports and all configured checks.
    """
    
    _instance: Optional['Inspector'] = None
    _browser: Optional[Browser] = None
    _playwright = None
    
    # Default viewports to test
    DEFAULT_VIEWPORTS = [
        {"width": 1280, "height": 800},   # Desktop
        {"width": 768, "height": 1024},   # Tablet  
        {"width": 375, "height": 667}     # Mobile
    ]
    
    # Default timeouts
    DEFAULT_TIMEOUTS = {
        "nav_ms": 30000,    # 30 seconds for navigation
        "action_ms": 5000   # 5 seconds for interactions
    }
    
    def __new__(cls) -> 'Inspector':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.checks: List[BaseCheck] = []
        self.output_dir = tempfile.mkdtemp(prefix="mantis_")
        
        # Register default checks
        self._register_default_checks()
        self._initialized = True
    
    def _register_default_checks(self):
        """Register all available checks"""
        self.checks = [
            AccessibilityCheck(),
            VisualLayoutCheck()
        ]
    
    @classmethod
    async def get_instance(cls) -> 'Inspector':
        """Get the singleton instance and ensure browser is ready"""
        instance = cls()
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
            PageResult with all findings across viewports
        """
        await self._ensure_browser_ready()
        
        result = PageResult(page_url=url)
        performance_tracker = PerformanceTracker()
        
        context = None
        try:
            # Create browser context
            context = await self._create_context()
            
            # Set up page
            page = await context.new_page()
            page_setup = PageSetup(page, url, self.DEFAULT_TIMEOUTS)
            
            # Navigate to URL and collect initial metrics
            navigation_start = time.time()
            success = await page_setup.navigate_safely()
            
            if not success:
                result.findings.append(Bug(
                    id=str(uuid.uuid4()),
                    type="Logic",
                    severity="high", 
                    page_url=url,
                    summary="Failed to navigate to page",
                    suggested_fix="Check if URL is accessible and valid"
                ))
                return result
            
            result.status = await page_setup.get_response_status()
            result.timings = await performance_tracker.collect_timings(page)
            result.timings['navigation_duration'] = (time.time() - navigation_start) * 1000
            
            # Set up evidence collection
            evidence_collector = EvidenceCollector(page, self.output_dir)
            
            # Detect outlinks
            link_detector = LinkDetector(page, url)
            result.outlinks = await link_detector.collect_outlinks()
            
            # Run checks across all viewports
            for viewport in self.DEFAULT_VIEWPORTS:
                viewport_key = f"{viewport['width']}x{viewport['height']}"
                
                # Set viewport
                await page.set_viewport_size(viewport['width'], viewport['height'])
                await asyncio.sleep(0.5)  # Allow layout to settle
                
                # Run all checks for this viewport
                viewport_bugs = await self._run_checks_for_viewport(
                    page, url, viewport_key, evidence_collector
                )
                
                result.findings.extend(viewport_bugs)
                
                # Capture viewport screenshot
                artifact_path = await evidence_collector.capture_viewport_screenshot(viewport_key)
                if artifact_path:
                    result.viewport_artifacts.append(artifact_path)
            
            # Collect final trace data
            result.trace = await self._collect_trace_data(page)
            
        except PlaywrightTimeoutError:
            result.findings.append(Bug(
                id=str(uuid.uuid4()),
                type="UI",
                severity="medium",
                page_url=url,
                summary="Page navigation or loading timeout",
                suggested_fix="Check page performance and loading speed"
            ))
            
        except Exception as e:
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
    
    async def _run_checks_for_viewport(
        self, 
        page: Page, 
        url: str,
        viewport_key: str,
        evidence_collector: EvidenceCollector
    ) -> List[Bug]:
        """Run all registered checks for a specific viewport"""
        bugs = []
        
        for check in self.checks:
            try:
                # Run the check
                check_bugs = await check.run(page, url, viewport_key)
                
                # Enhance bugs with evidence
                for bug in check_bugs:
                    if not bug.evidence.screenshot_path and check.requires_screenshot():
                        screenshot_path = await evidence_collector.capture_bug_screenshot(
                            bug.id, viewport_key
                        )
                        bug.evidence.screenshot_path = screenshot_path
                    
                    if not bug.evidence.viewport:
                        bug.evidence.viewport = viewport_key
                        
                bugs.extend(check_bugs)
                
            except Exception as e:
                # Create a bug for the check failure
                bugs.append(Bug(
                    id=str(uuid.uuid4()),
                    type="Logic",
                    severity="low",
                    page_url=url,
                    summary=f"Check '{check.__class__.__name__}' failed: {str(e)}",
                    evidence=Evidence(viewport=viewport_key)
                ))
                
        return bugs
    
    async def _collect_trace_data(self, page: Page) -> List[Dict]:
        """Collect basic trace data for debugging"""
        # This is simplified - you could collect more detailed traces
        return []
    
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
        if hasattr(self, 'output_dir') and os.path.exists(self.output_dir):
            import shutil
            try:
                shutil.rmtree(self.output_dir)
            except:
                pass  # Best effort cleanup


# Convenience function for getting the singleton
async def get_inspector() -> Inspector:
    """Get the singleton Inspector instance"""
    return await Inspector.get_instance()