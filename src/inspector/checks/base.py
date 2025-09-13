from abc import ABC, abstractmethod
from typing import List, Dict, Any
from playwright.async_api import Page

from core.types import Bug


class BaseCheck(ABC):
    """
    Abstract base class for all UI checks.
    
    Each check type (accessibility, visual, etc.) should inherit from this class
    and implement the run method to perform specific inspections.
    """
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        
    @abstractmethod
    async def run(self, page: Page, page_url: str, viewport: str) -> List[Bug]:
        """
        Execute the check on the given page.
        
        Args:
            page: Playwright page object
            page_url: URL of the page being inspected
            viewport: Current viewport string (e.g., "1280x800")
            
        Returns:
            List of Bug objects found by this check
        """
        pass
    
    def requires_screenshot(self) -> bool:
        """
        Whether this check typically requires screenshot evidence.
        Override in subclasses as needed.
        """
        return True
    
    def requires_interaction(self) -> bool:
        """
        Whether this check requires user interactions (clicks, scrolls, etc.).
        Override in subclasses as needed.
        """
        return False
    
    def get_check_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about this check for reporting purposes.
        """
        return {
            'name': self.name,
            'description': self.description,
            'requires_screenshot': self.requires_screenshot(),
            'requires_interaction': self.requires_interaction()
        }


class StaticCheck(BaseCheck):
    """
    Base class for checks that don't require user interaction.
    These can run on the page as-is without scrolling, clicking, etc.
    """
    
    def requires_interaction(self) -> bool:
        return False


class InteractiveCheck(BaseCheck):
    """
    Base class for checks that require user interaction.
    These checks will respect the action_budget from InspectorOptions.
    """
    
    def requires_interaction(self) -> bool:
        return True
    
    async def _safe_interaction(self, page: Page, action_func, timeout_ms: int = 5000):
        """
        Safely perform an interaction with timeout and error handling.
        
        Args:
            page: Playwright page object
            action_func: Async function to execute
            timeout_ms: Timeout in milliseconds
            
        Returns:
            True if successful, False if failed/timeout
        """
        try:
            await action_func()
            return True
        except Exception:
            return False


class ViewportSpecificCheck(BaseCheck):
    """
    Base class for checks that need to run differently per viewport.
    """
    
    def get_supported_viewports(self) -> List[str]:
        """
        Return list of viewport patterns this check supports.
        Empty list means it runs on all viewports.
        """
        return []
    
    def should_run_for_viewport(self, viewport: str) -> bool:
        """
        Determine if this check should run for the given viewport.
        
        Args:
            viewport: Viewport string like "1280x800"
            
        Returns:
            True if check should run for this viewport
        """
        supported = self.get_supported_viewports()
        if not supported:
            return True
            
        # Parse viewport dimensions
        try:
            width, height = map(int, viewport.split('x'))
            
            # Check against supported patterns
            for pattern in supported:
                if pattern == "mobile" and width <= 768:
                    return True
                elif pattern == "tablet" and 768 < width <= 1024:
                    return True
                elif pattern == "desktop" and width > 1024:
                    return True
                elif pattern == viewport:
                    return True
                    
        except ValueError:
            pass
            
        return False
