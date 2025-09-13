from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal, List, Dict, Optional

Severity = Literal["low", "medium", "high", "critical"]
BugType  = Literal["UI", "Accessibility", "Logic"]

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
