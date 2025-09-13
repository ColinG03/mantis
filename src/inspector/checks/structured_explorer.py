import uuid
import time
import asyncio
from typing import List, Dict, Any, Optional
from playwright.async_api import Page

try:
    from ...core.types import Bug, Evidence, PageResult
    from ..utils.evidence import EvidenceCollector
    from ..utils.performance import PerformanceTracker
    from ..utils.action_recorder import ActionRecorder
    from ..utils.cohere_analyzer import analyze_screenshot
    from ..playwright_helpers.link_detection import LinkDetector
except ImportError:
    from core.types import Bug, Evidence, PageResult
    from inspector.utils.evidence import EvidenceCollector
    from inspector.utils.performance import PerformanceTracker
    from inspector.utils.action_recorder import ActionRecorder
    from inspector.utils.cohere_analyzer import analyze_screenshot
    from inspector.playwright_helpers.link_detection import LinkDetector


class StructuredExplorer:
    """
    Simple, direct page exploration that finds forms and interactive elements,
    tests them with edge cases, and captures screenshots for VLM analysis.
    """
    
    # Default viewports to explore
    DEFAULT_VIEWPORTS = [
        {"name": "desktop", "width": 1280, "height": 800},
        {"name": "tablet", "width": 768, "height": 1024},
        {"name": "mobile", "width": 375, "height": 667}
    ]
    
    def __init__(self, output_dir: str):
        self.name = "Structured Explorer"
        self.description = "Direct page exploration with form testing and interactive element analysis"
        self.output_dir = output_dir
        self.bugs = []
        self.action_recorder: Optional[ActionRecorder] = None
        
    async def run_complete_exploration(self, page: Page, page_url: str) -> PageResult:
        """
        Run complete exploration of the page across all viewports.
        """
        print(f"\n🔍 Starting direct exploration of {page_url}")
        
        # Initialize result
        result = PageResult(page_url=page_url)
        self.bugs = []
        
        # Set up evidence collection, performance tracking, and action recording
        evidence_collector = EvidenceCollector(page, self.output_dir)
        performance_tracker = PerformanceTracker()
        self.action_recorder = ActionRecorder(page_url)
        
        # Record initial navigation
        self.action_recorder.record_navigation(page_url, "Navigate to page for testing")
        
        try:
            # Collect initial performance data
            result.timings = await performance_tracker.collect_timings(page)
            
            # Detect outlinks
            link_detector = LinkDetector(page, page_url)
            result.outlinks = await link_detector.collect_outlinks()
            
            # Explore each viewport directly
            for viewport_config in self.DEFAULT_VIEWPORTS:
                viewport_name = viewport_config["name"]
                viewport_key = f"{viewport_config['width']}x{viewport_config['height']}"
                
                print(f"\n📱 Exploring {viewport_name} viewport ({viewport_key})")
                
                # Set viewport size
                await page.set_viewport_size({"width": viewport_config['width'], "height": viewport_config['height']})
                self.action_recorder.record_viewport_change(viewport_key, f"Change to {viewport_name} viewport")
                await asyncio.sleep(0.5)  # Allow layout to settle
                
                # Explore this viewport
                await self._explore_viewport(page, page_url, viewport_name, viewport_key, evidence_collector)
            
            # Collect all findings
            result.findings.extend(self.bugs)
            
            # Collect viewport artifacts
            result.viewport_artifacts = await self._get_viewport_artifacts(evidence_collector)
            
        except Exception as e:
            # Handle exploration errors
            bug = self._create_bug_with_repro_steps(
                type="Logic",
                severity="high",
                page_url=page_url,
                summary=f"Exploration error: {str(e)}",
                suggested_fix="Review page structure and exploration compatibility"
            )
            result.findings.append(bug)
            
        print(f"✅ Exploration complete. Found {len(self.bugs)} potential issues.")
        return result
    
    async def _explore_viewport(self, page: Page, page_url: str, viewport_name: str, viewport_key: str, evidence_collector: EvidenceCollector):
        """Explore a single viewport comprehensively"""
        
        # 1. Capture baseline full-page screenshot
        print(f"  📸 Capturing baseline {viewport_name} screenshot")
        baseline_path = await evidence_collector.capture_viewport_screenshot(viewport_key)
        
        # Analyze baseline screenshot with Cohere Command-A-Vision
        if baseline_path:
            baseline_bugs, error = await analyze_screenshot(
                baseline_path, 
                viewport_key, 
                page_url,
                self.action_recorder
            )
            if error:
                print(f"      ⚠️  Cohere analysis error: {error}")
            else:
                self.bugs.extend(baseline_bugs)
                if baseline_bugs:
                    print(f"      🔍 Found {len(baseline_bugs)} visual issues in baseline")
        
        # 2. Find and test forms with edge cases
        await self._test_forms_with_edge_cases(page, page_url, viewport_name, viewport_key, evidence_collector)
        
        # 3. Find and test interactive elements
        await self._test_interactive_elements(page, page_url, viewport_name, viewport_key, evidence_collector)
    
    async def _test_forms_with_edge_cases(self, page: Page, page_url: str, viewport_name: str, viewport_key: str, evidence_collector: EvidenceCollector):
        """Find forms and test them with edge case data that might break layouts"""
        
        print(f"  📝 Testing forms in {viewport_name}")
        
        try:
            # Find all visible forms AND standalone inputs
            forms_and_inputs_data = await page.evaluate("""
            () => {
                // Helper function to check if element is truly visible
                const isElementVisible = (element) => {
                    if (!element) return false;
                    
                    // Check basic visibility
                    if (element.offsetParent === null) return false;
                    
                    // Check computed style
                    const style = window.getComputedStyle(element);
                    if (style.display === 'none' || 
                        style.visibility === 'hidden' || 
                        style.opacity === '0') return false;
                    
                    // Check if element has dimensions
                    const rect = element.getBoundingClientRect();
                    if (rect.width === 0 && rect.height === 0) return false;
                    
                    // Check if element is positioned off-screen
                    if (rect.right < 0 || rect.bottom < 0 || 
                        rect.left > window.innerWidth || rect.top > window.innerHeight) return false;
                    
                    return true;
                };
                
                // Helper function to create more specific selectors
                const createBestSelector = (input, containerIndex) => {
                    // Priority: ID > name > data attributes > class + type > placeholder (with container context)
                    if (input.id) {
                        return `#${input.id}`;
                    }
                    
                    if (input.name) {
                        return `[name="${input.name}"]`;
                    }
                    
                    // Check for data attributes that could make selector more specific
                    const dataAttrs = [];
                    for (const attr of input.attributes) {
                        if (attr.name.startsWith('data-') && attr.value) {
                            dataAttrs.push(`[${attr.name}="${attr.value}"]`);
                        }
                    }
                    if (dataAttrs.length > 0) {
                        return `${input.tagName.toLowerCase()}${dataAttrs.join('')}`;
                    }
                    
                    // Use class + type if available
                    if (input.className && input.type) {
                        const firstClass = input.className.split(' ')[0];
                        return `${input.tagName.toLowerCase()}[type="${input.type}"].${firstClass}`;
                    }
                    
                    // Last resort: placeholder with additional context
                    if (input.placeholder) {
                        const tagType = input.type ? `[type="${input.type}"]` : '';
                        // Add container context to make it more specific
                        return `${input.tagName.toLowerCase()}${tagType}[placeholder="${input.placeholder}"]:nth-of-type(${containerIndex + 1})`;
                    }
                    
                    return null;
                };
                
                // Find forms with their inputs
                const forms = Array.from(document.querySelectorAll('form')).map((form, index) => ({
                    type: 'form',
                    index: index,
                    inputs: Array.from(form.querySelectorAll('input:not([type="hidden"]), textarea, select')).map((input, inputIndex) => ({
                        type: input.type || input.tagName.toLowerCase(),
                        name: input.name,
                        id: input.id,
                        placeholder: input.placeholder,
                        selector: createBestSelector(input, inputIndex),
                        visible: isElementVisible(input)
                    })).filter(input => input.selector && input.visible),
                    visible: isElementVisible(form)
                }));
                
                // Find standalone inputs (not inside forms)
                const standaloneInputs = Array.from(document.querySelectorAll('input:not(form input):not([type="hidden"]), textarea:not(form textarea)')).map((input, index) => ({
                    type: 'standalone_input',
                    index: index,
                    inputs: [{
                        type: input.type || input.tagName.toLowerCase(),
                        name: input.name,
                        id: input.id,
                        placeholder: input.placeholder,
                        selector: createBestSelector(input, index),
                        visible: isElementVisible(input)
                    }].filter(input => input.selector && input.visible),
                    visible: isElementVisible(input)
                }));
                
                return [...forms, ...standaloneInputs];
            }
            """)
            
            visible_forms = [f for f in forms_and_inputs_data if f['visible'] and f['inputs']]
            forms_count = len([f for f in visible_forms if f['type'] == 'form'])
            inputs_count = len([f for f in visible_forms if f['type'] == 'standalone_input'])
            print(f"    📝 Found {forms_count} forms and {inputs_count} standalone inputs")
            
            if not visible_forms:
                return
            
            # Test each form/input with edge case data
            for form_index, form in enumerate(visible_forms):
                form_type = "form" if form['type'] == 'form' else "input field"
                print(f"    📝 Testing {form_type} {form_index + 1} with edge case data")
                
                # Fill form with edge case data that might break layout
                for input_data in form['inputs']:
                    await self._fill_input_with_edge_case_data(page, input_data)
                
                # Screenshot after filling with edge case data
                screenshot_id = f"form_{form_index}_filled_{viewport_key}"
                screenshot_path = await evidence_collector.capture_bug_screenshot(screenshot_id, viewport_key)
                
                if screenshot_path:
                    print(f"      📸 Form edge case screenshot: {screenshot_path}")
                    
                    # Analyze form filled with edge case data
                    form_bugs, error = await analyze_screenshot(
                        screenshot_path, 
                        viewport_key, 
                        page_url,
                        self.action_recorder
                    )
                    if error:
                        print(f"      ⚠️  Cohere analysis error: {error}")
                    else:
                        self.bugs.extend(form_bugs)
                        if form_bugs:
                            print(f"      🔍 Found {len(form_bugs)} visual issues in form {form_index + 1}")
                
                # Clear form for next test
                await self._clear_form_inputs(page, form)
                
        except Exception as e:
            print(f"    ❌ Form testing error: {str(e)}")
    
    async def _fill_input_with_edge_case_data(self, page: Page, input_data: Dict[str, Any]):
        """Fill a single input with edge case data designed to test layout breaks"""
        try:
            selector = input_data['selector']
            input_type = input_data['type'].lower()
            
            # First verify the element is visible and unique before attempting to fill
            locator = page.locator(selector)
            
            # Check how many elements match the selector
            count = await locator.count()
            if count == 0:
                print(f"      ⚠️  No elements found for selector: {selector}")
                return
            elif count > 1:
                print(f"      ⚠️  Multiple elements ({count}) found for selector: {selector}, using first visible one")
                # Use the first visible element
                locator = locator.first
            
            # Wait for element to be visible and ready
            try:
                await locator.wait_for(state="visible", timeout=5000)
            except Exception as e:
                print(f"      ⚠️  Element not visible within 5s for {selector}: {str(e)}")
                return
            
            # Edge case data designed to test layout limits
            edge_data = {
                'text': 'This is an extremely long text input that should test how the form handles very long content that might overflow containers or break layouts in unexpected ways when the user enters much more text than anticipated by the designer',
                'email': 'very.very.very.long.email.address.that.might.break.layout@extremely.long.domain.name.that.could.cause.issues.example.com',
                'password': 'VeryLongPasswordThatMightBreakLayoutsWhenDisplayed123!@#$%^&*()',
                'tel': '555-123-4567-extension-9999-department-sales-very-long-phone-number',
                'url': 'https://extremely.long.domain.name.that.might.cause.layout.issues.when.displayed.in.forms.example.com/very/long/path/that/continues',
                'number': '999999999999999999999',
                'search': 'Very long search query with lots of special characters !@#$%^&*()_+ that might break search input layouts and cause overflow',
                'textarea': 'This is extremely long textarea content that spans multiple lines and contains various special characters !@#$%^&*()_+ and should test how well the textarea handles large amounts of content without breaking the surrounding layout or causing overflow issues that might affect other page elements. This text continues for a very long time to really test the boundaries of what the textarea can handle without breaking the page layout or causing visual problems for users.'
            }
            
            value = edge_data.get(input_type, edge_data['text'])
            
            # Use locator.fill() instead of page.fill() for better error handling
            await locator.fill(value)
            
            # Record the action
            if self.action_recorder:
                field_name = input_data.get('name', input_data.get('placeholder', 'unknown field'))
                self.action_recorder.record_fill(selector, value, field_name)
            
            await asyncio.sleep(0.1)  # Brief pause for layout to settle
            
        except Exception as e:
            field_identifier = input_data.get('name') or input_data.get('placeholder') or input_data.get('id') or 'unknown'
            print(f"      ⚠️  Could not fill input '{field_identifier}': {str(e)}")
    
    async def _clear_form_inputs(self, page: Page, form: Dict[str, Any]):
        """Clear all inputs in a form"""
        for input_data in form['inputs']:
            try:
                selector = input_data['selector']
                if selector:
                    locator = page.locator(selector)
                    
                    # Only clear if element is visible and available
                    if await locator.count() > 0:
                        # Use first visible element if multiple exist
                        if await locator.count() > 1:
                            locator = locator.first
                        
                        # Only clear if element is visible
                        if await locator.is_visible():
                            await locator.fill('')
            except Exception:
                continue  # Ignore individual clear failures
    
    async def _test_interactive_elements(self, page: Page, page_url: str, viewport_name: str, viewport_key: str, evidence_collector: EvidenceCollector):
        """Find and test interactive elements like dropdowns, modals, accordions"""
        
        print(f"  🎮 Testing interactive elements in {viewport_name}")
        
        try:
            # Test dropdowns
            await self._test_dropdowns(page, page_url, viewport_name, viewport_key, evidence_collector)
            
            # Test modals
            await self._test_modals(page, page_url, viewport_name, viewport_key, evidence_collector)
            
            # Test accordions
            await self._test_accordions(page, page_url, viewport_name, viewport_key, evidence_collector)
            
        except Exception as e:
            print(f"    ❌ Interactive testing error: {str(e)}")
    
    async def _test_dropdowns(self, page: Page, page_url: str, viewport_name: str, viewport_key: str, evidence_collector: EvidenceCollector):
        """Test dropdown menus by opening them and capturing screenshots"""
        
        # Find dropdown triggers (including modern ARIA patterns)
        dropdown_selectors = [
            '.dropdown-toggle',
            '[data-toggle="dropdown"]',
            '[data-bs-toggle="dropdown"]',
            '.nav-item.dropdown > a',
            'button[aria-expanded]',          # Modern ARIA dropdowns
            'button[aria-controls]',          # ARIA controlled elements
            '[data-toggle="collapse"]',       # Collapsible elements
            '[data-bs-toggle="collapse"]',    # Bootstrap 5 collapse
            '.hamburger',                     # Mobile hamburger menus
            '.menu-toggle',                   # Generic menu toggles
            '.navbar-toggler'                 # Bootstrap navbar toggles
        ]
        
        dropdown_count = 0
        for selector in dropdown_selectors:
            try:
                # Use locators instead of query_selector_all for better error handling
                locator = page.locator(selector)
                count = await locator.count()
                
                for i in range(min(count, 3)):  # Test first 3 dropdowns per selector
                    element_locator = locator.nth(i)
                    
                    if await element_locator.is_visible():
                        dropdown_count += 1
                        element_text = await element_locator.text_content()
                        print(f"    📋 Testing dropdown {dropdown_count}: '{element_text[:30] if element_text else 'unknown'}'")
                        
                        # Get initial state for ARIA elements
                        initial_aria_expanded = await element_locator.get_attribute('aria-expanded')
                        
                        # Try to click with multiple strategies
                        click_success = await self._safe_click_element(page, element_locator, selector)
                        
                        if not click_success:
                            print(f"      ⚠️  Could not click dropdown {dropdown_count}, skipping")
                            continue
                        
                        # Record the action
                        if self.action_recorder:
                            self.action_recorder.record_click(selector, element_text or "", f"Open dropdown '{element_text[:30] if element_text else 'unknown'}'")
                        
                        await asyncio.sleep(0.5)  # Longer wait for mobile animations
                        
                        # Check if state actually changed (for ARIA elements)
                        new_aria_expanded = await element_locator.get_attribute('aria-expanded')
                        state_changed = initial_aria_expanded != new_aria_expanded
                        
                        if state_changed:
                            print(f"      ✅ ARIA state changed: {initial_aria_expanded} → {new_aria_expanded}")
                        
                        # Screenshot while dropdown is OPEN
                        screenshot_id = f"dropdown_{dropdown_count}_open_{viewport_key}"
                        screenshot_path = await evidence_collector.capture_bug_screenshot(screenshot_id, viewport_key)
                        
                        if screenshot_path:
                            print(f"      📸 Dropdown open screenshot: {screenshot_path}")
                            
                            # Analyze dropdown open state
                            element_text = element_text or "unknown"
                            dropdown_bugs, error = await analyze_screenshot(
                                screenshot_path, 
                                viewport_key, 
                                page_url,
                                self.action_recorder
                            )
                            if error:
                                print(f"      ⚠️  Cohere analysis error: {error}")
                            else:
                                self.bugs.extend(dropdown_bugs)
                                if dropdown_bugs:
                                    print(f"      🔍 Found {len(dropdown_bugs)} visual issues in dropdown")
                        
                        # Close dropdown (try multiple methods)
                        if state_changed:
                            # For ARIA dropdowns, click the same element again
                            await self._safe_click_element(page, element_locator, selector)
                        else:
                            # For traditional dropdowns, click body or press escape
                            try:
                                await page.click('body', timeout=1000)
                            except:
                                await page.keyboard.press('Escape')
                        await asyncio.sleep(0.3)
                        
            except Exception as e:
                print(f"      ⚠️  Dropdown test failed: {str(e)}")
                continue
        
        if dropdown_count == 0:
            print(f"    📋 No dropdowns found in {viewport_name}")
    
    async def _safe_click_element(self, page: Page, locator, selector: str) -> bool:
        """Safely click an element with multiple fallback strategies"""
        try:
            # Strategy 1: Normal click with short timeout
            await locator.click(timeout=3000)
            return True
            
        except Exception as e:
            if "intercepts pointer events" in str(e):
                print(f"      🔄 Pointer intercepted, trying alternative click methods...")
                
                # Strategy 2: Dismiss any overlays first
                await self._dismiss_overlays(page)
                
                try:
                    # Try normal click again after dismissing overlays
                    await locator.click(timeout=2000)
                    return True
                except:
                    pass
                
                # Strategy 3: Force click (ignores intercepting elements)
                try:
                    await locator.click(force=True, timeout=2000)
                    print(f"      ✅ Force click succeeded")
                    return True
                except Exception as force_e:
                    print(f"      ⚠️  Force click failed: {str(force_e)}")
                
                # Strategy 4: Scroll into view and try again
                try:
                    await locator.scroll_into_view_if_needed()
                    await asyncio.sleep(0.2)
                    await locator.click(timeout=2000)
                    print(f"      ✅ Click after scroll succeeded")
                    return True
                except Exception as scroll_e:
                    print(f"      ⚠️  Click after scroll failed: {str(scroll_e)}")
                
                # Strategy 5: Use JavaScript click as last resort
                try:
                    await locator.evaluate("element => element.click()")
                    print(f"      ✅ JavaScript click succeeded")
                    return True
                except Exception as js_e:
                    print(f"      ⚠️  JavaScript click failed: {str(js_e)}")
            
            else:
                print(f"      ⚠️  Click failed: {str(e)}")
            
            return False
    
    async def _dismiss_overlays(self, page: Page):
        """Try to dismiss common overlays that might block clicks"""
        try:
            # Common overlay dismissal strategies
            overlay_selectors = [
                '.modal-backdrop',
                '.overlay',
                '.loading-overlay',
                '[data-dismiss="modal"]',
                '[data-bs-dismiss="modal"]',
                '.close',
                'button:has-text("Close")',
                'button:has-text("×")'
            ]
            
            for overlay_selector in overlay_selectors:
                try:
                    overlay_locator = page.locator(overlay_selector)
                    if await overlay_locator.count() > 0 and await overlay_locator.first.is_visible():
                        await overlay_locator.first.click(timeout=1000)
                        await asyncio.sleep(0.2)
                        break
                except:
                    continue
            
            # Try pressing Escape to dismiss any modal/overlay
            await page.keyboard.press('Escape')
            await asyncio.sleep(0.2)
            
        except Exception:
            pass  # Ignore overlay dismissal failures
    
    async def _test_modals(self, page: Page, page_url: str, viewport_name: str, viewport_key: str, evidence_collector: EvidenceCollector):
        """Test modal triggers by opening them and capturing screenshots"""
        
        # Find modal triggers
        modal_selectors = [
            '[data-toggle="modal"]',
            '[data-bs-toggle="modal"]',
            '[data-target*="modal"]',
            '[data-bs-target*="modal"]',
            'button:has(+ .modal)',
            '.modal-trigger'
        ]
        
        modal_count = 0
        for selector in modal_selectors:
            try:
                elements = await page.query_selector_all(selector)
                for i, element in enumerate(elements[:2]):  # Test first 2 modals per selector
                    if await element.is_visible():
                        modal_count += 1
                        print(f"    🔲 Testing modal {modal_count}")
                        
                        # Open modal
                        await element.click()
                        await asyncio.sleep(0.5)  # Wait for modal to open
                        
                        # Screenshot while modal is OPEN
                        screenshot_id = f"modal_{modal_count}_open_{viewport_key}"
                        screenshot_path = await evidence_collector.capture_bug_screenshot(screenshot_id, viewport_key)
                        
                        if screenshot_path:
                            print(f"      📸 Modal open screenshot: {screenshot_path}")
                            
                            # Analyze modal open state
                            modal_bugs, error = await analyze_screenshot(
                                screenshot_path, 
                                viewport_key, 
                                page_url,
                                self.action_recorder
                            )
                            if error:
                                print(f"      ⚠️  Cohere analysis error: {error}")
                            else:
                                self.bugs.extend(modal_bugs)
                                if modal_bugs:
                                    print(f"      🔍 Found {len(modal_bugs)} visual issues in modal")
                        
                        # Close modal with escape key
                        await page.keyboard.press('Escape')
                        await asyncio.sleep(0.3)
                        
                        # Also try clicking close button if exists
                        close_selectors = ['.modal .close', '.modal [data-dismiss="modal"]', '.modal [data-bs-dismiss="modal"]']
                        for close_selector in close_selectors:
                            try:
                                await page.click(close_selector, timeout=500)
                                break
                            except:
                                continue
                        
                        await asyncio.sleep(0.2)
                        
            except Exception as e:
                print(f"      ⚠️  Modal test failed: {str(e)}")
                continue
        
        if modal_count == 0:
            print(f"    🔲 No modals found in {viewport_name}")
    
    async def _test_accordions(self, page: Page, page_url: str, viewport_name: str, viewport_key: str, evidence_collector: EvidenceCollector):
        """Test accordion/collapsible elements by toggling them and capturing screenshots"""
        
        # Find accordion triggers
        accordion_selectors = [
            '.accordion-button',
            '[data-toggle="collapse"]',
            '[data-bs-toggle="collapse"]',
            'details summary',
            '.collapsible-header'
        ]
        
        accordion_count = 0
        for selector in accordion_selectors:
            try:
                elements = await page.query_selector_all(selector)
                for i, element in enumerate(elements[:3]):  # Test first 3 accordions per selector
                    if await element.is_visible():
                        accordion_count += 1
                        print(f"    📁 Testing accordion {accordion_count}")
                        
                        # Open accordion
                        await element.click()
                        await asyncio.sleep(0.3)  # Wait for expansion
                        
                        # Screenshot while accordion is EXPANDED
                        screenshot_id = f"accordion_{accordion_count}_expanded_{viewport_key}"
                        screenshot_path = await evidence_collector.capture_bug_screenshot(screenshot_id, viewport_key)
                        
                        if screenshot_path:
                            print(f"      📸 Accordion expanded screenshot: {screenshot_path}")
                            
                            # Analyze accordion expanded state
                            accordion_bugs, error = await analyze_screenshot(
                                screenshot_path, 
                                viewport_key, 
                                page_url,
                                self.action_recorder
                            )
                            if error:
                                print(f"      ⚠️  Cohere analysis error: {error}")
                            else:
                                self.bugs.extend(accordion_bugs)
                                if accordion_bugs:
                                    print(f"      🔍 Found {len(accordion_bugs)} visual issues in accordion")
                        
                        # Close accordion
                        await element.click()
                        await asyncio.sleep(0.3)
                        
            except Exception as e:
                print(f"      ⚠️  Accordion test failed: {str(e)}")
                continue
        
        if accordion_count == 0:
            print(f"    📁 No accordions found in {viewport_name}")
    
    async def _get_viewport_artifacts(self, evidence_collector: EvidenceCollector) -> List[str]:
        """Get list of all screenshots captured during exploration"""
        import os
        import glob
        
        try:
            screenshots_dir = evidence_collector.screenshots_dir
            if os.path.exists(screenshots_dir):
                # Find all screenshots from this exploration session
                all_screenshots = glob.glob(os.path.join(screenshots_dir, "*.png"))
                return sorted(all_screenshots)
            
        except Exception as e:
            print(f"Warning: Could not collect viewport artifacts: {str(e)}")
            
        return []
    
    def _create_bug_with_repro_steps(self, type: str, severity: str, page_url: str, summary: str, suggested_fix: str = None, evidence: Evidence = None) -> Bug:
        """Create a bug with current reproduction steps included"""
        if not evidence:
            evidence = Evidence()
        
        # Add action log to evidence if action recorder is available
        if self.action_recorder and not evidence.action_log:
            evidence.action_log = self.action_recorder.format_steps_for_human()
        
        bug = Bug(
            id=str(uuid.uuid4()),
            type=type,
            severity=severity,
            page_url=page_url,
            summary=summary,
            suggested_fix=suggested_fix,
            evidence=evidence,
            reproduction_steps=[step.description for step in self.action_recorder.get_steps()] if self.action_recorder else []
        )
        return bug
    
    async def run_visual_only_exploration(self, page: Page, page_url: str) -> PageResult:
        """
        Run visual-only exploration (baseline screenshots and Cohere Command-A-Vision analysis).
        No interactive testing.
        """
        print(f"\n🔍 Starting visual-only exploration of {page_url}")
        
        # Initialize result
        result = PageResult(page_url=page_url)
        self.bugs = []
        
        # Set up evidence collection and performance tracking
        evidence_collector = EvidenceCollector(page, self.output_dir)
        performance_tracker = PerformanceTracker()
        self.action_recorder = ActionRecorder(page_url)
        
        # Record initial navigation
        self.action_recorder.record_navigation(page_url, "Navigate to page for visual testing")
        
        try:
            # Collect initial performance data
            result.timings = await performance_tracker.collect_timings(page)
            
            # Detect outlinks
            link_detector = LinkDetector(page, page_url)
            result.outlinks = await link_detector.collect_outlinks()
            
            # Visual exploration across viewports
            for viewport_config in self.DEFAULT_VIEWPORTS:
                viewport_name = viewport_config["name"]
                viewport_key = f"{viewport_config['width']}x{viewport_config['height']}"
                
                print(f"\n📱 Visual testing {viewport_name} viewport ({viewport_key})")
                
                # Set viewport size
                await page.set_viewport_size({"width": viewport_config['width'], "height": viewport_config['height']})
                await asyncio.sleep(0.5)  # Allow layout to settle
                
                # Capture baseline full-page screenshot and analyze
                print(f"  📸 Capturing baseline {viewport_name} screenshot")
                baseline_path = await evidence_collector.capture_viewport_screenshot(viewport_key)
                
                # Analyze baseline screenshot with Cohere Command-A-Vision
                if baseline_path:
                    baseline_bugs, error = await analyze_screenshot(
                        baseline_path, 
                        viewport_key, 
                        page_url,
                        self.action_recorder
                    )
                    if error:
                        print(f"      ⚠️  Cohere analysis error: {error}")
                    else:
                        self.bugs.extend(baseline_bugs)
                        if baseline_bugs:
                            print(f"      🔍 Found {len(baseline_bugs)} visual issues in baseline")
            
            # Collect all findings
            result.findings.extend(self.bugs)
            
            # Collect viewport artifacts
            result.viewport_artifacts = await self._get_viewport_artifacts(evidence_collector)
            
        except Exception as e:
            # Handle exploration errors
            bug = self._create_bug_with_repro_steps(
                type="UI",
                severity="high",
                page_url=page_url,
                summary=f"Visual exploration error: {str(e)}",
                suggested_fix="Review page structure and visual analysis compatibility"
            )
            result.findings.append(bug)
            
        print(f"✅ Visual exploration complete. Found {len(self.bugs)} potential issues.")
        return result
    
    async def run_interactive_only_exploration(self, page: Page, page_url: str) -> PageResult:
        """
        Run interactive-only exploration (forms, dropdowns, modals, accordions).
        No baseline visual analysis.
        """
        print(f"\n🔍 Starting interactive-only exploration of {page_url}")
        
        # Initialize result
        result = PageResult(page_url=page_url)
        self.bugs = []
        
        # Set up evidence collection and performance tracking
        evidence_collector = EvidenceCollector(page, self.output_dir)
        performance_tracker = PerformanceTracker()
        self.action_recorder = ActionRecorder(page_url)
        
        # Record initial navigation
        self.action_recorder.record_navigation(page_url, "Navigate to page for interactive testing")
        
        try:
            # Collect initial performance data
            result.timings = await performance_tracker.collect_timings(page)
            
            # Detect outlinks
            link_detector = LinkDetector(page, page_url)
            result.outlinks = await link_detector.collect_outlinks()
            
            # Interactive exploration across viewports
            for viewport_config in self.DEFAULT_VIEWPORTS:
                viewport_name = viewport_config["name"]
                viewport_key = f"{viewport_config['width']}x{viewport_config['height']}"
                
                print(f"\n📱 Interactive testing {viewport_name} viewport ({viewport_key})")
                
                # Set viewport size
                await page.set_viewport_size({"width": viewport_config['width'], "height": viewport_config['height']})
                await asyncio.sleep(0.5)  # Allow layout to settle
                
                # Test forms with edge cases
                await self._test_forms_with_edge_cases(page, page_url, viewport_name, viewport_key, evidence_collector)
                
                # Test interactive elements
                await self._test_interactive_elements(page, page_url, viewport_name, viewport_key, evidence_collector)
            
            # Collect all findings
            result.findings.extend(self.bugs)
            
            # Collect viewport artifacts
            result.viewport_artifacts = await self._get_viewport_artifacts(evidence_collector)
            
        except Exception as e:
            # Handle exploration errors
            bug = self._create_bug_with_repro_steps(
                type="UI",
                severity="high",
                page_url=page_url,
                summary=f"Interactive exploration error: {str(e)}",
                suggested_fix="Review page structure and interactive testing compatibility"
            )
            result.findings.append(bug)
            
        print(f"✅ Interactive exploration complete. Found {len(self.bugs)} potential issues.")
        return result

    async def run(self, page: Page, page_url: str, viewport: str) -> List[Bug]:
        """
        Legacy interface for compatibility with old system.
        This should not be used - use run_complete_exploration instead.
        """
        print(f"⚠️  Warning: Using legacy run() method. Use run_complete_exploration() instead.")
        result = await self.run_complete_exploration(page, page_url)
        return result.findings
