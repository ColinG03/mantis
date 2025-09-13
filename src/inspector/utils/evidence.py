import os
import uuid
import json
from typing import Optional
from datetime import datetime
from playwright.async_api import Page


class EvidenceCollector:
    """
    Handles collection and storage of evidence for bugs found during inspection.
    
    This includes screenshots, console logs, DOM snapshots, and other artifacts
    that help developers understand and reproduce issues.
    """
    
    def __init__(self, page: Page, output_dir: str):
        self.page = page
        self.output_dir = output_dir
        self.screenshots_dir = os.path.join(output_dir, 'screenshots')
        self.logs_dir = os.path.join(output_dir, 'logs')
        
        # Ensure directories exist
        os.makedirs(self.screenshots_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)
        
    async def capture_bug_screenshot(self, bug_id: str, viewport: str) -> Optional[str]:
        """
        Capture a screenshot for a specific bug.
        
        Args:
            bug_id: Unique identifier for the bug
            viewport: Current viewport (e.g., "1280x800")
            
        Returns:
            Path to the screenshot file, or None if capture failed
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"bug_{bug_id}_{viewport}_{timestamp}.png"
            filepath = os.path.join(self.screenshots_dir, filename)
            
            await self.page.screenshot(
                path=filepath,
                full_page=True,
                type='png'
            )
            
            return filepath
            
        except Exception as e:
            print(f"Failed to capture screenshot for bug {bug_id}: {str(e)}")
            return None
    
    async def capture_viewport_screenshot(self, viewport: str) -> Optional[str]:
        """
        Capture a full viewport screenshot for general documentation.
        
        Args:
            viewport: Current viewport (e.g., "1280x800")
            
        Returns:
            Path to the screenshot file, or None if capture failed
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"viewport_{viewport}_{timestamp}.png"
            filepath = os.path.join(self.screenshots_dir, filename)
            
            await self.page.screenshot(
                path=filepath,
                full_page=True,
                type='png'
            )
            
            return filepath
            
        except Exception as e:
            print(f"Failed to capture viewport screenshot: {str(e)}")
            return None
    
    async def capture_element_screenshot(self, selector: str, bug_id: str) -> Optional[str]:
        """
        Capture a screenshot of a specific element.
        
        Args:
            selector: CSS selector for the element
            bug_id: Bug ID for filename
            
        Returns:
            Path to the screenshot file, or None if capture failed
        """
        try:
            element = await self.page.query_selector(selector)
            if not element:
                return None
                
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"element_{bug_id}_{timestamp}.png"
            filepath = os.path.join(self.screenshots_dir, filename)
            
            await element.screenshot(path=filepath, type='png')
            
            return filepath
            
        except Exception as e:
            print(f"Failed to capture element screenshot: {str(e)}")
            return None
    
    def format_console_logs(self, logs: list) -> Optional[str]:
        """
        Format console logs as a readable string.
        
        Args:
            logs: List of console log entries
            
        Returns:
            Formatted log string, or None if no logs
        """
        if not logs:
            return None
            
        try:
            formatted_lines = []
            
            for log_entry in logs:
                # Handle different log entry formats
                if isinstance(log_entry, dict):
                    level = log_entry.get('level', 'info')
                    message = log_entry.get('message', str(log_entry))
                    timestamp = log_entry.get('timestamp', '')
                    
                    if timestamp:
                        line = f"[{timestamp}] {level.upper()}: {message}"
                    else:
                        line = f"{level.upper()}: {message}"
                        
                elif isinstance(log_entry, str):
                    line = log_entry
                else:
                    line = str(log_entry)
                
                formatted_lines.append(line)
            
            return '\n'.join(formatted_lines)
            
        except Exception as e:
            print(f"Failed to format console logs: {str(e)}")
            return f"Error formatting logs: {str(e)}"
    
    async def save_dom_snapshot(self, bug_id: str, selector: Optional[str] = None) -> Optional[str]:
        """
        Save a DOM snapshot for debugging purposes.
        
        Args:
            bug_id: Unique identifier for the bug
            selector: Optional selector to capture specific element HTML
            
        Returns:
            Path to the HTML file, or None if save failed
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"dom_{bug_id}_{timestamp}.html"
            filepath = os.path.join(self.logs_dir, filename)
            
            if selector:
                # Capture specific element
                element = await self.page.query_selector(selector)
                if element:
                    html_content = await element.inner_html()
                else:
                    html_content = f"<!-- Element not found: {selector} -->"
            else:
                # Capture full page HTML
                html_content = await self.page.content()
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return filepath
            
        except Exception as e:
            print(f"Failed to save DOM snapshot for bug {bug_id}: {str(e)}")
            return None
    
    async def collect_console_logs(self) -> list:
        """
        Collect console logs from the current page.
        
        Returns:
            List of console log entries
        """
        try:
            # Get console logs using JavaScript
            logs = await self.page.evaluate("""
            () => {
                // Try to get logs from console if they've been captured
                if (window.__mantis_console_logs) {
                    return window.__mantis_console_logs;
                }
                
                // If no logs captured, return empty array
                return [];
            }
            """)
            
            return logs if logs else []
            
        except Exception as e:
            print(f"Failed to collect console logs: {str(e)}")
            return []
    
    async def collect_network_logs(self) -> list:
        """
        Collect network request logs from the current page session.
        
        Returns:
            List of network request data
        """
        # This would require setting up network listeners during page setup
        # For now, return empty list - implement based on your needs
        return []
    
    async def get_page_metrics(self) -> dict:
        """
        Collect performance and accessibility metrics.
        
        Returns:
            Dictionary of page metrics
        """
        try:
            # Get basic performance metrics
            metrics = await self.page.evaluate("""
            () => {
                const perfData = performance.getEntriesByType('navigation')[0];
                const paintData = performance.getEntriesByType('paint');
                
                return {
                    loadTime: perfData ? perfData.loadEventEnd - perfData.loadEventStart : null,
                    domContentLoaded: perfData ? perfData.domContentLoadedEventEnd - perfData.domContentLoadedEventStart : null,
                    firstPaint: paintData.find(p => p.name === 'first-paint')?.startTime || null,
                    firstContentfulPaint: paintData.find(p => p.name === 'first-contentful-paint')?.startTime || null,
                    documentHeight: document.documentElement.scrollHeight,
                    viewportHeight: window.innerHeight,
                    viewportWidth: window.innerWidth
                };
            }
            """)
            
            return metrics
            
        except Exception as e:
            print(f"Failed to collect page metrics: {str(e)}")
            return {}
