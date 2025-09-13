import asyncio
import time
import uuid
from typing import List, Dict, Any
from urllib.parse import urljoin, urlparse

from playwright.async_api import async_playwright, Browser, BrowserContext, Page, TimeoutError as PlaywrightTimeoutError

from ..core.types import Inspector as InspectorInterface, InspectorOptions, PageResult, Bug, Evidence
from .checks.base import BaseCheck
from .utils.evidence import EvidenceCollector
from .utils.performance import PerformanceTracker
from .playwright_helpers.page_setup import PageSetup
from .playwright_helpers.link_detection import LinkDetector


class Inspector(InspectorInterface):
    """
    Main Inspector class that orchestrates Playwright-based UI testing.
    
    Responsibilities:
    - Set up browser context and page
    - Navigate to target URL safely
    - Execute all registered checks across multiple viewports
    - Collect evidence for found issues
    - Return comprehensive PageResult
    """
    
    def __init__(self):
        self.checks: List[BaseCheck] = []
        self.browser: Browser = None
        self.context: BrowserContext = None
        
    def register_check(self, check: BaseCheck):
        """Register a check to be run during inspection"""
        self.checks.append(check)
        
    async def inspect_page(self, opts: InspectorOptions) -> PageResult:
        """
        Main entry point for page inspection.
        
        Args:
            opts: Configuration options for the inspection
            
        Returns:
            PageResult containing all findings and metadata
        """
        result = PageResult(page_url=opts.url)
        performance_tracker = PerformanceTracker()
        
        try:
            # Initialize browser and context
            async with async_playwright() as p:
                self.browser = await p.chromium.launch(headless=True)
                self.context = await self._setup_context(opts)
                
                # Set up page with initial configuration
                page = await self.context.new_page()
                page_setup = PageSetup(page, opts)
                
                # Navigate to target URL and collect initial metrics
                navigation_start = time.time()
                await page_setup.navigate_safely()
                result.status = await page_setup.get_response_status()
                
                # Collect performance timings
                result.timings = await performance_tracker.collect_timings(page)
                result.timings['navigation_duration'] = time.time() - navigation_start
                
                # Set up evidence collection
                evidence_collector = EvidenceCollector(page, opts.out_dir)
                
                # Detect outlinks without navigation
                link_detector = LinkDetector(page, opts)
                result.outlinks = await link_detector.collect_outlinks()
                
                # Run checks across all viewports
                for viewport in opts.viewport_set:
                    viewport_key = f"{viewport['width']}x{viewport['height']}"
                    
                    # Set viewport
                    await page.set_viewport_size(viewport['width'], viewport['height'])
                    await asyncio.sleep(0.5)  # Allow layout to settle
                    
                    # Run all registered checks for this viewport
                    viewport_bugs = await self._run_checks_for_viewport(
                        page, opts, viewport_key, evidence_collector
                    )
                    
                    result.findings.extend(viewport_bugs)
                    
                    # Collect viewport artifacts
                    artifact_path = await evidence_collector.capture_viewport_screenshot(viewport_key)
                    if artifact_path:
                        result.viewport_artifacts.append(artifact_path)
                
                # Collect final console logs and traces
                result.trace = await self._collect_trace_data(page)
                
        except PlaywrightTimeoutError as e:
            # Handle navigation timeouts gracefully
            result.findings.append(Bug(
                id=str(uuid.uuid4()),
                type="UI",
                severity="medium",
                page_url=opts.url,
                summary=f"Page navigation timeout: {str(e)}",
                suggested_fix="Check if page loads properly or increase timeout values"
            ))
            
        except Exception as e:
            # Handle unexpected errors
            result.findings.append(Bug(
                id=str(uuid.uuid4()),
                type="Logic",
                severity="high",
                page_url=opts.url,
                summary=f"Inspector error: {str(e)}",
                suggested_fix="Review page structure and inspector configuration"
            ))
            
        finally:
            # Cleanup
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
                
        return result
    
    async def _setup_context(self, opts: InspectorOptions) -> BrowserContext:
        """Set up browser context with authentication and headers"""
        context_options = {
            'viewport': None,  # We'll set viewport per check
            'user_agent': 'Mantis-UI-Inspector/1.0'
        }
        
        # Add custom headers if provided
        if opts.headers:
            context_options['extra_http_headers'] = opts.headers
            
        context = await self.browser.new_context(**context_options)
        
        # Set authentication cookies if provided
        if opts.auth_cookies:
            # Parse and set cookies (simplified - you might want more robust parsing)
            cookies = []
            for cookie_str in opts.auth_cookies.split(';'):
                if '=' in cookie_str:
                    name, value = cookie_str.strip().split('=', 1)
                    cookies.append({
                        'name': name,
                        'value': value,
                        'domain': opts.seed_host,
                        'path': '/'
                    })
            await context.add_cookies(cookies)
            
        return context
    
    async def _run_checks_for_viewport(
        self, 
        page: Page, 
        opts: InspectorOptions, 
        viewport_key: str,
        evidence_collector: EvidenceCollector
    ) -> List[Bug]:
        """Run all registered checks for a specific viewport"""
        bugs = []
        
        for check in self.checks:
            try:
                # Run the check
                check_bugs = await check.run(page, opts, viewport_key)
                
                # Enhance bugs with evidence if needed
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
                # If a check fails, create a bug about the check failure
                bugs.append(Bug(
                    id=str(uuid.uuid4()),
                    type="Logic",
                    severity="low",
                    page_url=opts.url,
                    summary=f"Check '{check.__class__.__name__}' failed: {str(e)}",
                    evidence=Evidence(viewport=viewport_key)
                ))
                
        return bugs
    
    async def _collect_trace_data(self, page: Page) -> List[Dict]:
        """Collect trace data like console logs, network requests, etc."""
        trace_data = []
        
        # This is a placeholder - you might want to collect:
        # - Console logs
        # - Network requests
        # - JavaScript errors
        # - Performance marks
        
        return trace_data
