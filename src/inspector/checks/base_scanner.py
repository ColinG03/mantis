"""
Base scanner interface for modular scan architecture.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from playwright.async_api import Page

try:
    from ...core.types import Bug, PageResult
except ImportError:
    from core.types import Bug, PageResult


class BaseScanResult:
    """Base class for scan results"""
    def __init__(self, scan_type: str):
        self.scan_type = scan_type
        self.findings: List[Bug] = []
        self.evidence: Dict[str, Any] = {}
        self.metadata: Dict[str, Any] = {}
    
    def add_finding(self, bug: Bug):
        """Add a bug finding to this scan result"""
        self.findings.append(bug)
    
    def merge_into_page_result(self, page_result: PageResult):
        """Merge this scan result into a PageResult"""
        page_result.findings.extend(self.findings)


class BaseScanner(ABC):
    """Abstract base class for all scanners"""
    
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.name = self.__class__.__name__
    
    @abstractmethod
    async def scan(self, page: Page, page_url: str, viewport_key: str = None) -> BaseScanResult:
        """
        Perform the scan and return results.
        
        Args:
            page: Playwright page object
            page_url: URL being scanned
            viewport_key: Optional viewport identifier (e.g., "1280x800")
            
        Returns:
            BaseScanResult containing findings and evidence
        """
        pass
    
    @property
    @abstractmethod
    def scan_type(self) -> str:
        """Return the type of scan this scanner performs"""
        pass
    
    @property
    def description(self) -> str:
        """Return a description of what this scanner does"""
        return f"{self.name} scanner"


class ScanConfig:
    """Configuration for different types of scans"""
    
    def __init__(
        self,
        accessibility: bool = True,
        ui_visual: bool = True,
        performance: bool = False,
        interactive: bool = True
    ):
        self.accessibility = accessibility
        self.ui_visual = ui_visual
        self.performance = performance
        self.interactive = interactive
    
    @classmethod
    def accessibility_only(cls) -> 'ScanConfig':
        """Create config for accessibility-only scanning"""
        return cls(accessibility=True, ui_visual=False, performance=False, interactive=False)
    
    @classmethod
    def ui_only(cls) -> 'ScanConfig':
        """Create config for UI-only scanning"""
        return cls(accessibility=False, ui_visual=True, performance=False, interactive=True)
    
    @classmethod
    def all_scans(cls) -> 'ScanConfig':
        """Create config for all available scans"""
        return cls(accessibility=True, ui_visual=True, performance=True, interactive=True)
    
    def is_enabled(self, scan_type: str) -> bool:
        """Check if a specific scan type is enabled"""
        return getattr(self, scan_type, False)
