import uuid
from typing import List
from playwright.async_api import Page

from ...core.types import Bug, Evidence
from .base import StaticCheck


class VisualLayoutCheck(StaticCheck):
    """
    Checks for visual and layout defects on the page.
    
    Detects issues like:
    - Overlapping elements
    - Elements outside viewport
    - Invisible text (0 opacity, same color as background)
    - Broken images
    - Layout shifts
    - Empty or malformed elements
    """
    
    def __init__(self):
        super().__init__(
            name="Visual Layout Check",
            description="Detects visual and layout defects including overlaps and broken elements"
        )
    
    async def run(self, page: Page, page_url: str, viewport: str) -> List[Bug]:
        """Run all visual layout checks"""
        bugs = []
        
        # Check for overlapping elements
        bugs.extend(await self._check_overlapping_elements(page, page_url))
        
        # Check for broken images
        bugs.extend(await self._check_broken_images(page, page_url))
        
        # Check for invisible text
        bugs.extend(await self._check_invisible_text(page, page_url))
        
        # Check for elements outside viewport
        bugs.extend(await self._check_elements_outside_viewport(page, page_url))
        
        # Check for empty elements that should have content
        bugs.extend(await self._check_empty_elements(page, page_url))
        
        return bugs
    
    async def _check_overlapping_elements(self, page: Page, page_url: str) -> List[Bug]:
        """Detect overlapping elements that might indicate layout issues"""
        bugs = []
        
        try:
            overlaps = await page.evaluate("""
            () => {
                const overlaps = [];
                const elements = Array.from(document.querySelectorAll('*')).filter(el => {
                    const style = window.getComputedStyle(el);
                    return style.display !== 'none' && 
                           style.visibility !== 'hidden' && 
                           el.offsetParent !== null &&
                           el.getBoundingClientRect().width > 0 &&
                           el.getBoundingClientRect().height > 0;
                });
                
                // Check for elements with same position (simplified overlap detection)
                const positions = new Map();
                
                elements.forEach((el, index) => {
                    const rect = el.getBoundingClientRect();
                    const key = `${Math.round(rect.left)},${Math.round(rect.top)}`;
                    
                    if (positions.has(key)) {
                        const existing = positions.get(key);
                        // Check if elements actually overlap (not just same top-left)
                        const existingRect = existing.getBoundingClientRect();
                        
                        if (rect.right > existingRect.left && 
                            rect.left < existingRect.right &&
                            rect.bottom > existingRect.top && 
                            rect.top < existingRect.bottom) {
                            
                            overlaps.push({
                                element1: existing.tagName + (existing.className ? '.' + existing.className.split(' ')[0] : ''),
                                element2: el.tagName + (el.className ? '.' + el.className.split(' ')[0] : ''),
                                position: key
                            });
                        }
                    } else {
                        positions.set(key, el);
                    }
                });
                
                return overlaps.slice(0, 10); // Limit to first 10 overlaps
            }
            """)
            
            for overlap in overlaps:
                bugs.append(Bug(
                    id=str(uuid.uuid4()),
                    type="UI",
                    severity="medium",
                    page_url=page_url,
                    summary=f"Overlapping elements detected: {overlap['element1']} and {overlap['element2']}",
                    suggested_fix="Check CSS positioning and z-index values to resolve overlap"
                ))
                
        except Exception as e:
            print(f"Error checking overlapping elements: {str(e)}")
            
        return bugs
    
    async def _check_broken_images(self, page: Page, page_url: str) -> List[Bug]:
        """Check for broken or failed-to-load images"""
        bugs = []
        
        try:
            broken_images = await page.evaluate("""
            () => {
                const images = Array.from(document.querySelectorAll('img'));
                return images
                    .filter(img => !img.complete || img.naturalWidth === 0)
                    .map(img => ({
                        src: img.src,
                        alt: img.alt,
                        visible: img.offsetParent !== null
                    }));
            }
            """)
            
            for img in broken_images:
                if img['visible']:
                    bugs.append(Bug(
                        id=str(uuid.uuid4()),
                        type="UI",
                        severity="medium",
                        page_url=page_url,
                        summary=f"Broken image: {img['src'][:100]}...",
                        suggested_fix="Check image URL and ensure the image file exists and is accessible"
                    ))
                    
        except Exception as e:
            print(f"Error checking broken images: {str(e)}")
            
        return bugs
    
    async def _check_invisible_text(self, page: Page, page_url: str) -> List[Bug]:
        """Check for text that might be invisible due to styling"""
        bugs = []
        
        try:
            invisible_text = await page.evaluate("""
            () => {
                const textElements = Array.from(document.querySelectorAll('*')).filter(el => {
                    return el.textContent && el.textContent.trim().length > 0 && 
                           el.children.length === 0; // Only leaf text nodes
                });
                
                const invisible = [];
                
                textElements.forEach(el => {
                    const style = window.getComputedStyle(el);
                    const rect = el.getBoundingClientRect();
                    
                    // Check for various invisibility conditions
                    if (style.opacity === '0' ||
                        style.visibility === 'hidden' ||
                        style.display === 'none' ||
                        rect.width === 0 ||
                        rect.height === 0 ||
                        style.fontSize === '0px' ||
                        style.color === style.backgroundColor) {
                        
                        invisible.push({
                            text: el.textContent.trim().substring(0, 100),
                            reason: style.opacity === '0' ? 'opacity-0' :
                                   style.visibility === 'hidden' ? 'visibility-hidden' :
                                   style.display === 'none' ? 'display-none' :
                                   rect.width === 0 || rect.height === 0 ? 'zero-dimensions' :
                                   style.fontSize === '0px' ? 'font-size-0' :
                                   'color-match-background',
                            tagName: el.tagName
                        });
                    }
                });
                
                return invisible.slice(0, 5); // Limit results
            }
            """)
            
            for item in invisible_text:
                severity = "high" if item['reason'] in ['opacity-0', 'color-match-background'] else "low"
                bugs.append(Bug(
                    id=str(uuid.uuid4()),
                    type="UI",
                    severity=severity,
                    page_url=page_url,
                    summary=f"Invisible text detected ({item['reason']}): {item['text']}...",
                    suggested_fix=f"Review CSS styling for {item['tagName']} element to ensure text is visible"
                ))
                
        except Exception as e:
            print(f"Error checking invisible text: {str(e)}")
            
        return bugs
    
    async def _check_elements_outside_viewport(self, page: Page, page_url: str) -> List[Bug]:
        """Check for important elements that are positioned outside the viewport"""
        bugs = []
        
        try:
            outside_elements = await page.evaluate("""
            () => {
                const viewport = {
                    width: window.innerWidth,
                    height: window.innerHeight
                };
                
                const importantSelectors = [
                    'button', 'a', 'input', 'form', 
                    '[role="button"]', '.btn', '.button',
                    'nav', 'header', 'main', 'footer'
                ];
                
                const outside = [];
                
                importantSelectors.forEach(selector => {
                    const elements = document.querySelectorAll(selector);
                    elements.forEach(el => {
                        const rect = el.getBoundingClientRect();
                        
                        if (rect.right < 0 || 
                            rect.left > viewport.width || 
                            rect.bottom < 0 || 
                            rect.top > viewport.height) {
                            
                            outside.push({
                                selector: selector,
                                tagName: el.tagName,
                                className: el.className,
                                text: el.textContent ? el.textContent.trim().substring(0, 50) : '',
                                position: {
                                    left: Math.round(rect.left),
                                    top: Math.round(rect.top),
                                    right: Math.round(rect.right),
                                    bottom: Math.round(rect.bottom)
                                }
                            });
                        }
                    });
                });
                
                return outside.slice(0, 5);
            }
            """)
            
            for element in outside_elements:
                bugs.append(Bug(
                    id=str(uuid.uuid4()),
                    type="UI",
                    severity="medium",
                    page_url=page_url,
                    summary=f"Important element outside viewport: {element['tagName']} ({element['text']})",
                    suggested_fix="Check CSS positioning to ensure important elements are visible within the viewport"
                ))
                
        except Exception as e:
            print(f"Error checking elements outside viewport: {str(e)}")
            
        return bugs
    
    async def _check_empty_elements(self, page: Page, page_url: str) -> List[Bug]:
        """Check for elements that should have content but appear empty"""
        bugs = []
        
        try:
            empty_elements = await page.evaluate("""
            () => {
                const shouldHaveContent = [
                    'button', 'a', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                    'p', 'span', 'div.card', 'div.content', 'article',
                    'section', 'main', 'aside'
                ];
                
                const empty = [];
                
                shouldHaveContent.forEach(selector => {
                    const elements = document.querySelectorAll(selector);
                    elements.forEach(el => {
                        const hasText = el.textContent && el.textContent.trim().length > 0;
                        const hasImages = el.querySelectorAll('img').length > 0;
                        const hasIcons = el.querySelectorAll('[class*="icon"], [class*="fa-"], svg').length > 0;
                        const isVisible = el.offsetParent !== null;
                        
                        if (isVisible && !hasText && !hasImages && !hasIcons) {
                            const rect = el.getBoundingClientRect();
                            if (rect.width > 10 && rect.height > 10) { // Has visible dimensions
                                empty.push({
                                    tagName: el.tagName,
                                    className: el.className,
                                    selector: selector,
                                    dimensions: `${Math.round(rect.width)}x${Math.round(rect.height)}`
                                });
                            }
                        }
                    });
                });
                
                return empty.slice(0, 5);
            }
            """)
            
            for element in empty_elements:
                bugs.append(Bug(
                    id=str(uuid.uuid4()),
                    type="UI",
                    severity="low",
                    page_url=page_url,
                    summary=f"Empty element with visible dimensions: {element['tagName']} ({element['dimensions']})",
                    suggested_fix="Add content to the element or hide it if not needed"
                ))
                
        except Exception as e:
            print(f"Error checking empty elements: {str(e)}")
            
        return bugs
