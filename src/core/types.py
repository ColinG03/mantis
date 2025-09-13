from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal, List, Dict, Optional

Severity = Literal["low", "medium", "high", "critical"]
BugType  = Literal["UI", "Accessibility", "Logic", "Performance", "Security", "Usability"]
Priority = Literal["P1", "P2", "P3", "P4"]  # P1 = Must fix, P4 = Nice to have
BugCategory = Literal["Functional", "Visual", "Content", "Navigation", "Form", "Mobile", "Desktop"]

#LAYER BETWEEN THE ORCHESTRATOR AND THE INSPECTOR: pass a url to inspector, inspector returns a PageResult

@dataclass
class Evidence:
    screenshot_path: Optional[str] = None
    console_log: Optional[str] = None
    wcag: Optional[List[str]] = None
    viewport: Optional[str] = None  # "1280x800"

@dataclass
class Bug:
    id: str
    type: BugType
    severity: Severity
    page_url: str
    summary: str
    suggested_fix: Optional[str] = None
    evidence: Evidence = field(default_factory=Evidence)
    
    # Enhanced bug reporting fields
    reproduction_steps: List[str] = field(default_factory=list)
    fix_steps: List[str] = field(default_factory=list)
    affected_elements: List[str] = field(default_factory=list)  # CSS selectors or element descriptions
    impact_description: Optional[str] = None
    wcag_guidelines: List[str] = field(default_factory=list)  # WCAG reference codes
    business_impact: Optional[str] = None  # High-level impact on users/business
    technical_details: Optional[str] = None  # Additional technical context
    
    # Categorization and prioritization
    priority: Optional[Priority] = None
    category: Optional[BugCategory] = None
    estimated_effort: Optional[str] = None  # "1 hour", "1 day", "1 week", etc.
    tags: List[str] = field(default_factory=list)  # Custom tags for filtering

@dataclass
class PageResult:
    page_url: str
    status: Optional[int] = None
    outlinks: List[str] = field(default_factory=list)
    findings: List[Bug] = field(default_factory=list)
    timings: Dict[str, float] = field(default_factory=dict)  # dcl, load
    trace: List[Dict] = field(default_factory=list)
    viewport_artifacts: List[str] = field(default_factory=list)

@dataclass
class CrawlReport:
    scanned_at: str
    seed_url: str
    pages_total: int
    bugs_total: int
    findings: List[Bug]
    pages: List[Dict]  # {url, depth, status}

class Inspector:
    async def inspect_page(self, url: str) -> PageResult: ...
