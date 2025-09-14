"""
Accessibility scanner using axe-core for WCAG compliance testing.
"""
import uuid
import asyncio
from typing import List, Dict, Any, Optional
from playwright.async_api import Page

try:
    from axe_playwright_python.async_playwright import Axe
except ImportError:
    print("Warning: axe-playwright-python not installed. Run: pip install axe-playwright-python")
    Axe = None

try:
    from .base_scanner import BaseScanner, BaseScanResult
    from ...core.types import Bug, Evidence
    from ..utils.evidence import EvidenceCollector
except ImportError:
    from inspector.checks.base_scanner import BaseScanner, BaseScanResult
    from core.types import Bug, Evidence
    from inspector.utils.evidence import EvidenceCollector


class AccessibilityScanResult(BaseScanResult):
    """Results from accessibility scanning"""
    
    def __init__(self):
        super().__init__("accessibility")
        self.wcag_level: str = "AA"
        self.rules_tested: List[str] = []
        self.pass_rate: float = 0.0
        self.total_checks: int = 0
        self.violations_count: int = 0
        self.passes_count: int = 0
        self.incomplete_count: int = 0
        self.inapplicable_count: int = 0


class AccessibilityScanner(BaseScanner):
    """
    Accessibility scanner using axe-core for comprehensive WCAG compliance testing.
    """
    
    # WCAG 2.1 AA rules (high priority)
    DEFAULT_RULES = [
        'color-contrast',           # Color contrast ratio
        'image-alt',               # Images must have alt text
        'label',                   # Form elements must have labels
        'heading-order',           # Heading levels should increase by one
        'link-name',               # Links must have discernible text
        'button-name',             # Buttons must have discernible text
        'aria-roles',              # ARIA roles must be valid
        'aria-allowed-attr',       # ARIA attributes must be allowed
        'aria-required-attr',      # Required ARIA attributes must be present
        'keyboard',                # Elements must be keyboard accessible
        'focus-order-semantics',   # Focus order must be meaningful
        'skip-link',               # Skip links should be provided
        'bypass',                  # Page must have means to bypass repetitive content
        'page-has-heading-one',    # Page must have at least one h1
        'landmark-one-main',       # Page must have one main landmark
        'region',                  # All page content must be contained by landmarks
    ]
    
    # Severity mapping from axe to our system
    SEVERITY_MAPPING = {
        'critical': 'critical',
        'serious': 'high',
        'moderate': 'medium',
        'minor': 'low'
    }
    
    def __init__(self, output_dir: str, wcag_level: str = "AA"):
        super().__init__(output_dir)
        self.wcag_level = wcag_level
        self.axe = Axe() if Axe else None
        
    @property
    def scan_type(self) -> str:
        return "accessibility"
    
    @property
    def description(self) -> str:
        return f"WCAG {self.wcag_level} accessibility compliance scanner using axe-core"
    
    async def scan(self, page: Page, page_url: str, viewport_key: str = None) -> AccessibilityScanResult:
        """
        Perform comprehensive accessibility scan using axe-core.
        """
        result = AccessibilityScanResult()
        
        if not self.axe:
            # Create a fallback bug if axe is not available
            bug = Bug(
                id=str(uuid.uuid4()),
                type="Accessibility",
                severity="medium",
                page_url=page_url,
                summary="Accessibility scanner unavailable - axe-playwright-python not installed",
                suggested_fix="Install axe-playwright-python: pip install axe-playwright-python"
            )
            result.add_finding(bug)
            return result
                
        try:
            # Set up evidence collection
            evidence_collector = EvidenceCollector(page, self.output_dir)
            
            # Configure axe options
            axe_options = {
                'runOnly': {
                    'type': 'tag',
                    'values': self._get_wcag_tags()
                }
            }
            
            # Run axe-core accessibility scan
            scan_results = await self.axe.run(page, options=axe_options)
            
            # Process results
            await self._process_scan_results(
                scan_results, 
                page_url, 
                viewport_key, 
                result, 
                evidence_collector
            )
            
            # Update metadata
            result.wcag_level = self.wcag_level
            result.rules_tested = list(self.DEFAULT_RULES)
            result.total_checks = result.violations_count + result.passes_count + result.incomplete_count
            
            if result.total_checks > 0:
                result.pass_rate = result.passes_count / result.total_checks
            
            if self.verbose:
                print(f"    ✅ Accessibility scan complete: {result.violations_count} violations, {result.passes_count} passes")
            
        except Exception as e:
            if self.verbose:
                print(f"    ❌ Accessibility scan error: {str(e)}")
            
            # Create error bug
            bug = Bug(
                id=str(uuid.uuid4()),
                type="Accessibility",
                severity="medium",
                page_url=page_url,
                summary=f"Accessibility scan failed: {str(e)}",
                suggested_fix="Review page structure and accessibility scanner compatibility"
            )
            result.add_finding(bug)
        
        return result
    
    async def _process_scan_results(
        self, 
        scan_results, 
        page_url: str, 
        viewport_key: str,
        result: AccessibilityScanResult,
        evidence_collector: EvidenceCollector
    ):
        """Process axe-core scan results and convert to Bug objects"""
        
        # Get the actual results from the AxeResults object
        response = scan_results.response
        
        # Update counts
        result.violations_count = len(response.get('violations', []))
        result.passes_count = len(response.get('passes', []))
        result.incomplete_count = len(response.get('incomplete', []))
        result.inapplicable_count = len(response.get('inapplicable', []))
        
        # Process violations (actual accessibility issues)
        for violation in response.get('violations', []):
            await self._create_violation_bug(
                violation, 
                page_url, 
                viewport_key, 
                result, 
                evidence_collector
            )
        
        # Process incomplete results (potential issues that need manual review)
        for incomplete in response.get('incomplete', []):
            await self._create_incomplete_bug(
                incomplete, 
                page_url, 
                viewport_key, 
                result, 
                evidence_collector
            )
    
    async def _create_violation_bug(
        self, 
        violation: Dict[str, Any], 
        page_url: str, 
        viewport_key: str,
        result: AccessibilityScanResult,
        evidence_collector: EvidenceCollector
    ):
        """Create a Bug object from an axe violation"""
        
        # Map severity
        axe_impact = violation.get('impact', 'moderate')
        severity = self.SEVERITY_MAPPING.get(axe_impact, 'medium')
        
        # Build summary and description
        rule_id = violation.get('id', 'unknown')
        description = violation.get('description', '')
        help_text = violation.get('help', '')
        
        summary = f"Accessibility: {description}"
        if len(summary) > 100:
            summary = summary[:97] + "..."
        
        # Get affected elements
        affected_elements = []
        element_details = []
        
        for node in violation.get('nodes', []):
            target = node.get('target', [])
            if target:
                selector = target[0] if isinstance(target[0], str) else str(target[0])
                affected_elements.append(selector)
                
                # Add failure details
                failure_summary = node.get('failureSummary', '')
                if failure_summary:
                    element_details.append(f"Element {selector}: {failure_summary}")
        
        # Build WCAG guidelines
        wcag_guidelines = []
        tags = violation.get('tags', [])
        for tag in tags:
            if tag.startswith('wcag'):
                wcag_guidelines.append(tag.upper())
        
        # Capture screenshot for this violation if possible
        screenshot_path = None
        if viewport_key and evidence_collector:
            try:
                screenshot_id = f"a11y_{rule_id}_{viewport_key}"
                screenshot_path = await evidence_collector.capture_bug_screenshot(screenshot_id, viewport_key)
            except Exception:
                pass  # Screenshot capture is optional
        
        # Create evidence
        evidence = Evidence(
            screenshot_path=screenshot_path,
            viewport=viewport_key,
            wcag=wcag_guidelines
        )
        
        # Build technical details
        technical_details = f"Rule: {rule_id}\n"
        technical_details += f"Impact: {axe_impact}\n"
        technical_details += f"Help: {help_text}\n"
        if element_details:
            technical_details += f"Element Issues:\n" + "\n".join(f"  - {detail}" for detail in element_details)
        
        # Create bug
        bug = Bug(
            id=str(uuid.uuid4()),
            type="Accessibility",
            severity=severity,
            page_url=page_url,
            summary=summary,
            suggested_fix=help_text,
            evidence=evidence,
            affected_elements=affected_elements,
            wcag_guidelines=wcag_guidelines,
            technical_details=technical_details,
            impact_description=self._get_impact_description(axe_impact),
            business_impact=self._get_business_impact(axe_impact),
            category="Functional",
            tags=[f"axe-{rule_id}", f"wcag-{self.wcag_level.lower()}", "accessibility"]
        )
        result.add_finding(bug)
    
    async def _create_incomplete_bug(
        self, 
        incomplete: Dict[str, Any], 
        page_url: str, 
        viewport_key: str,
        result: AccessibilityScanResult,
        evidence_collector: EvidenceCollector
    ):
        """Create a Bug object from an axe incomplete result (needs manual review)"""
        
        rule_id = incomplete.get('id', 'unknown')
        description = incomplete.get('description', '')
        help_text = incomplete.get('help', '')
        
        summary = f"Accessibility Review Needed: {description}"
        if len(summary) > 100:
            summary = summary[:97] + "..."
        
        # Get affected elements
        affected_elements = []
        for node in incomplete.get('nodes', []):
            target = node.get('target', [])
            if target:
                selector = target[0] if isinstance(target[0], str) else str(target[0])
                affected_elements.append(selector)
        
        # Build WCAG guidelines
        wcag_guidelines = []
        tags = incomplete.get('tags', [])
        for tag in tags:
            if tag.startswith('wcag'):
                wcag_guidelines.append(tag.upper())
        
        # Create evidence
        evidence = Evidence(
            viewport=viewport_key,
            wcag=wcag_guidelines
        )
        
        # Create bug with low severity since it needs manual review
        bug = Bug(
            id=str(uuid.uuid4()),
            type="Accessibility",
            severity="low",
            page_url=page_url,
            summary=summary,
            suggested_fix=f"Manual review required: {help_text}",
            evidence=evidence,
            affected_elements=affected_elements,
            wcag_guidelines=wcag_guidelines,
            technical_details=f"Rule: {rule_id}\nRequires manual accessibility review",
            impact_description="Potential accessibility issue requiring manual verification",
            category="Functional",
            tags=[f"axe-{rule_id}", "manual-review", "accessibility"]
        )
        
        result.add_finding(bug)
    
    def _get_wcag_tags(self) -> List[str]:
        """Get WCAG tags based on compliance level"""
        tags = ['wcag2a']  # Always include Level A
        
        if self.wcag_level in ['AA', 'AAA']:
            tags.append('wcag2aa')
        
        if self.wcag_level == 'AAA':
            tags.append('wcag2aaa')
        
        return tags
    
    def _get_rule_config(self) -> Dict[str, Any]:
        """Get rule configuration for axe-core"""
        # Enable specific rules we care about
        rules = {}
        for rule in self.DEFAULT_RULES:
            rules[rule] = {'enabled': True}
        
        return rules
    
    def _get_impact_description(self, axe_impact: str) -> str:
        """Convert axe impact to user-friendly description"""
        impact_map = {
            'critical': 'Blocks users with disabilities from accessing key functionality',
            'serious': 'Significantly impacts users with disabilities',
            'moderate': 'May impact some users with disabilities',
            'minor': 'Minor accessibility improvement needed'
        }
        return impact_map.get(axe_impact, 'Accessibility issue detected')
    
    def _get_business_impact(self, axe_impact: str) -> str:
        """Get business impact description based on severity"""
        business_impact_map = {
            'critical': 'Legal compliance risk, potential user exclusion, brand damage',
            'serious': 'Compliance risk, reduced user base, poor user experience',
            'moderate': 'Minor compliance gap, some users may struggle',
            'minor': 'Accessibility enhancement opportunity'
        }
        return business_impact_map.get(axe_impact, 'May affect accessibility compliance')
    
    async def scan_all_viewports(self, page: Page, page_url: str, viewports: List[Dict[str, Any]] = None) -> AccessibilityScanResult:
        """
        Perform accessibility scan across multiple viewports to catch responsive design issues.
        """
        if not viewports:
            # Default viewports for accessibility testing
            viewports = [
                {"name": "desktop", "width": 1280, "height": 800},
                {"name": "tablet", "width": 768, "height": 1024},
                {"name": "mobile", "width": 375, "height": 667}
            ]
        
        combined_result = AccessibilityScanResult()
        
        for viewport in viewports:
            viewport_key = f"{viewport['width']}x{viewport['height']}"
            viewport_name = viewport.get('name', viewport_key)
            
            if self.verbose:
                print(f"    Testing accessibility in {viewport_name} ({viewport_key})")
            
            # Set viewport
            await page.set_viewport_size({"width": viewport['width'], "height": viewport['height']})
            await asyncio.sleep(0.5)  # Allow layout to settle
            
            # Run accessibility scan for this viewport
            viewport_result = await self.scan(page, page_url, viewport_key)
            
            # Merge results, but mark findings with viewport info
            for finding in viewport_result.findings:
                # Add viewport info to evidence and tags
                if finding.evidence:
                    finding.evidence.viewport = viewport_key
                else:
                    finding.evidence = Evidence(viewport=viewport_key)
                
                finding.tags.append(f"viewport-{viewport_name}")
                
                # Update summary to include viewport context if this is a viewport-specific issue
                if viewport_name != "desktop":
                    finding.summary = f"[{viewport_name}] {finding.summary}"
            
            # Merge findings and counts
            combined_result.findings.extend(viewport_result.findings)
            combined_result.violations_count += viewport_result.violations_count
            combined_result.passes_count += viewport_result.passes_count
            combined_result.incomplete_count += viewport_result.incomplete_count
            combined_result.inapplicable_count += viewport_result.inapplicable_count
        
        # Update combined metadata
        combined_result.total_checks = combined_result.violations_count + combined_result.passes_count + combined_result.incomplete_count
        if combined_result.total_checks > 0:
            combined_result.pass_rate = combined_result.passes_count / combined_result.total_checks
        
        if self.verbose:
            print(f"    ✅ Multi-viewport accessibility scan complete: {combined_result.violations_count} total violations")
        return combined_result
