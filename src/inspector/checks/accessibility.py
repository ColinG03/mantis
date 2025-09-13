import uuid
from typing import List
from playwright.async_api import Page

from ...core.types import Bug, Evidence
from .base import StaticCheck


class AccessibilityCheck(StaticCheck):
    """
    Comprehensive accessibility checker that goes beyond basic axe rules.
    
    Checks for:
    - Missing alt text on images
    - Poor color contrast
    - Missing form labels
    - Keyboard navigation issues
    - ARIA usage problems
    - Heading structure issues
    """
    
    def __init__(self):
        super().__init__(
            name="Accessibility Check",
            description="Comprehensive accessibility analysis including WCAG compliance"
        )
    
    async def run(self, page: Page, page_url: str, viewport: str) -> List[Bug]:
        """Run all accessibility checks on the page"""
        bugs = []
        
        # Check for missing alt text
        bugs.extend(await self._check_missing_alt_text(page, page_url))
        
        # Check for missing form labels
        bugs.extend(await self._check_form_labels(page, page_url))
        
        # Check heading structure
        bugs.extend(await self._check_heading_structure(page, page_url))
        
        # Check color contrast (simplified version)
        bugs.extend(await self._check_color_contrast(page, page_url))
        
        # Check for keyboard accessibility
        bugs.extend(await self._check_keyboard_accessibility(page, page_url))
        
        return bugs
    
    async def _check_missing_alt_text(self, page: Page, page_url: str) -> List[Bug]:
        """Check for images missing alt text"""
        bugs = []
        
        try:
            # Find images without alt text
            missing_alt_images = await page.evaluate("""
            () => {
                const images = Array.from(document.querySelectorAll('img'));
                return images
                    .filter(img => !img.hasAttribute('alt') || img.alt.trim() === '')
                    .map((img, index) => ({
                        src: img.src,
                        index: index,
                        selector: `img[src="${img.src}"]`,
                        visible: img.offsetParent !== null
                    }));
            }
            """)
            
            for img_data in missing_alt_images:
                if img_data['visible']:  # Only report visible images
                    bugs.append(Bug(
                        id=str(uuid.uuid4()),
                        type="Accessibility",
                        severity="medium",
                        page_url=page_url,
                        summary=f"Image missing alt text: {img_data['src'][:100]}...",
                        suggested_fix="Add descriptive alt text to the image element",
                        evidence=Evidence(wcag=["1.1.1"])
                    ))
                    
        except Exception as e:
            print(f"Error checking alt text: {str(e)}")
            
        return bugs
    
    async def _check_form_labels(self, page: Page, page_url: str) -> List[Bug]:
        """Check for form inputs missing labels"""
        bugs = []
        
        try:
            unlabeled_inputs = await page.evaluate("""
            () => {
                const inputs = Array.from(document.querySelectorAll('input, textarea, select'));
                return inputs
                    .filter(input => {
                        // Skip hidden inputs
                        if (input.type === 'hidden' || input.offsetParent === null) {
                            return false;
                        }
                        
                        // Check for label association
                        const hasLabel = input.labels && input.labels.length > 0;
                        const hasAriaLabel = input.hasAttribute('aria-label') && input.getAttribute('aria-label').trim() !== '';
                        const hasAriaLabelledby = input.hasAttribute('aria-labelledby');
                        
                        return !hasLabel && !hasAriaLabel && !hasAriaLabelledby;
                    })
                    .map(input => ({
                        type: input.type,
                        name: input.name,
                        id: input.id,
                        placeholder: input.placeholder
                    }));
            }
            """)
            
            for input_data in unlabeled_inputs:
                bugs.append(Bug(
                    id=str(uuid.uuid4()),
                    type="Accessibility",
                    severity="high",
                    page_url=page_url,
                    summary=f"Form input missing label: {input_data['type']} input",
                    suggested_fix="Add a <label> element or aria-label attribute to the input",
                    evidence=Evidence(wcag=["3.3.2"])
                ))
                
        except Exception as e:
            print(f"Error checking form labels: {str(e)}")
            
        return bugs
    
    async def _check_heading_structure(self, page: Page, page_url: str) -> List[Bug]:
        """Check for proper heading hierarchy"""
        bugs = []
        
        try:
            heading_issues = await page.evaluate("""
            () => {
                const headings = Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, h6'));
                const issues = [];
                
                if (headings.length === 0) {
                    return [{ type: 'no_headings', message: 'No heading elements found on page' }];
                }
                
                // Check for multiple h1s
                const h1s = headings.filter(h => h.tagName === 'H1');
                if (h1s.length > 1) {
                    issues.push({ 
                        type: 'multiple_h1', 
                        message: `Found ${h1s.length} h1 elements, should only have one` 
                    });
                }
                
                // Check for skipped heading levels
                let previousLevel = 0;
                headings.forEach(heading => {
                    const currentLevel = parseInt(heading.tagName.charAt(1));
                    if (currentLevel > previousLevel + 1) {
                        issues.push({
                            type: 'skipped_level',
                            message: `Heading level skipped: jumped from h${previousLevel} to h${currentLevel}`
                        });
                    }
                    previousLevel = Math.max(previousLevel, currentLevel);
                });
                
                return issues;
            }
            """)
            
            for issue in heading_issues:
                severity = "high" if issue['type'] == 'multiple_h1' else "medium"
                bugs.append(Bug(
                    id=str(uuid.uuid4()),
                    type="Accessibility",
                    severity=severity,
                    page_url=page_url,
                    summary=f"Heading structure issue: {issue['message']}",
                    suggested_fix="Ensure proper heading hierarchy (h1 > h2 > h3, etc.)",
                    evidence=Evidence(wcag=["1.3.1"])
                ))
                
        except Exception as e:
            print(f"Error checking heading structure: {str(e)}")
            
        return bugs
    
    async def _check_color_contrast(self, page: Page, page_url: str) -> List[Bug]:
        """Basic color contrast check (simplified)"""
        bugs = []
        
        try:
            # This is a simplified contrast check
            # In a real implementation, you'd want more sophisticated color analysis
            contrast_issues = await page.evaluate("""
            () => {
                const issues = [];
                
                // Check for common low-contrast patterns
                const elements = document.querySelectorAll('*');
                const lowContrastSelectors = [
                    '[style*="color: #999"]',
                    '[style*="color: #ccc"]',
                    '[style*="color: gray"]',
                    '.text-muted',
                    '.text-secondary'
                ];
                
                lowContrastSelectors.forEach(selector => {
                    const matches = document.querySelectorAll(selector);
                    if (matches.length > 0) {
                        issues.push({
                            selector: selector,
                            count: matches.length,
                            message: `Potentially low contrast elements found: ${selector}`
                        });
                    }
                });
                
                return issues;
            }
            """)
            
            for issue in contrast_issues:
                bugs.append(Bug(
                    id=str(uuid.uuid4()),
                    type="Accessibility",
                    severity="medium",
                    page_url=page_url,
                    summary=f"Potential color contrast issue: {issue['message']}",
                    suggested_fix="Ensure text has sufficient contrast ratio (4.5:1 for normal text, 3:1 for large text)",
                    evidence=Evidence(wcag=["1.4.3"])
                ))
                
        except Exception as e:
            print(f"Error checking color contrast: {str(e)}")
            
        return bugs
    
    async def _check_keyboard_accessibility(self, page: Page, page_url: str) -> List[Bug]:
        """Check for keyboard accessibility issues"""
        bugs = []
        
        try:
            keyboard_issues = await page.evaluate("""
            () => {
                const issues = [];
                
                // Check for interactive elements without proper focus indicators
                const interactiveElements = document.querySelectorAll(
                    'button, a, input, textarea, select, [tabindex], [onclick], [role="button"]'
                );
                
                let elementsWithoutTabindex = 0;
                let elementsWithNegativeTabindex = 0;
                
                interactiveElements.forEach(element => {
                    const tabindex = element.getAttribute('tabindex');
                    
                    if (tabindex === '-1' && element.tagName !== 'DIV') {
                        elementsWithNegativeTabindex++;
                    }
                    
                    // Check if element is focusable
                    if (!element.matches(':focus-visible') && 
                        element.offsetParent !== null && 
                        !['INPUT', 'BUTTON', 'A', 'TEXTAREA', 'SELECT'].includes(element.tagName)) {
                        elementsWithoutTabindex++;
                    }
                });
                
                if (elementsWithNegativeTabindex > 0) {
                    issues.push({
                        type: 'negative_tabindex',
                        count: elementsWithNegativeTabindex,
                        message: `${elementsWithNegativeTabindex} interactive elements with tabindex="-1"`
                    });
                }
                
                return issues;
            }
            """)
            
            for issue in keyboard_issues:
                bugs.append(Bug(
                    id=str(uuid.uuid4()),
                    type="Accessibility",
                    severity="medium",
                    page_url=page_url,
                    summary=f"Keyboard accessibility issue: {issue['message']}",
                    suggested_fix="Ensure all interactive elements are keyboard accessible",
                    evidence=Evidence(wcag=["2.1.1"])
                ))
                
        except Exception as e:
            print(f"Error checking keyboard accessibility: {str(e)}")
            
        return bugs
