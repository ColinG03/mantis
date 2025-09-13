"""
Web crawler with BFS traversal and retry logic.
"""

import asyncio
from collections import deque
from typing import Set, List, Dict, Optional, Callable
from datetime import datetime
import logging
from urllib.parse import urlparse

from core.types import PageResult, CrawlReport, Bug, Inspector
from orchestrator.url_utils import URLUtils


class Crawler:
    """
    BFS web crawler that orchestrates page inspection and builds crawl reports.
    """
    
    def __init__(self, max_depth: int = 3, max_pages: int = 50, max_retries: int = 3):
        """
        Initialize crawler with limits.
        
        Args:
            max_depth: Maximum crawl depth from seed URL
            max_pages: Maximum total pages to crawl
            max_retries: Maximum retries per failed page
        """
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.max_retries = max_retries
        self.logger = logging.getLogger(__name__)
    
    async def crawl_site(
        self,
        seed_url: str,
        inspector: Inspector,
        progress_callback: Optional[Callable[[str, int, int], None]] = None
    ) -> CrawlReport:
        """
        Crawl a website starting from seed URL using BFS.
        
        Args:
            seed_url: Starting URL for crawl
            inspector: Inspector instance with inspect_page(url) method
            progress_callback: Optional callback for progress updates (url, current_count, total_found)
            dashboard_server: Optional dashboard server for WebSocket updates
            
        Returns:
            Complete crawl report with all findings
        """
        self.logger.info(f"Starting crawl of {seed_url} (max_depth={self.max_depth}, max_pages={self.max_pages})")
        
        # Initialize crawl state
        seed_host = self._extract_seed_host(seed_url)
        frontier = deque([(seed_url, 0)])  # (url, depth) tuples
        visited = set()  # URLs we've already processed
        visited_normalized = set()  # Normalized URLs for deduplication
        page_results = []  # Successful page inspection results
        pages_info = []  # Page metadata for report
        crawled_count = 0
        total_bugs_found = 0
        
        self.logger.info(f"Seed host: {seed_host}")
        
        
        # BFS crawling loop
        while frontier and crawled_count < self.max_pages:
            current_url, depth = frontier.popleft()
            
            # Skip if already visited (exact URL)
            if current_url in visited:
                continue
                
            # Skip if normalized version already visited (path parameter deduplication)
            normalized_url = URLUtils.detect_path_parameters(current_url)
            if normalized_url in visited_normalized:
                self.logger.debug(f"Skipping {current_url} - normalized version already visited")
                continue
            
            # Mark as visited
            visited.add(current_url)
            visited_normalized.add(normalized_url)
            crawled_count += 1
            
            # Progress callback
            if progress_callback:
                progress_callback(current_url, crawled_count, self.max_pages)
            
            self.logger.info(f"Crawling page {crawled_count}/{self.max_pages}: {current_url} (depth {depth})")
            
            # Inspect the page
            page_result = await self._inspect_page_with_retry(current_url, inspector)
            
            if page_result is None:
                # Failed to inspect page - record as failed but continue
                pages_info.append({
                    "url": current_url,
                    "depth": depth,
                    "status": None  # Failed
                })
                self.logger.warning(f"Failed to inspect {current_url} after {self.max_retries} retries")
                continue
            
            # Record successful page
            page_results.append(page_result)
            pages_info.append({
                "url": current_url,
                "depth": depth,
                "status": page_result.status
            })
            
            # Count bugs and emit WebSocket events for each bug found
            bugs_on_this_page = len(page_result.findings)
            total_bugs_found += bugs_on_this_page
            
            self.logger.info(f"Found {bugs_on_this_page} bugs and {len(page_result.outlinks)} outlinks on {current_url}")
            
            
            # Add outlinks to frontier if within depth limit
            if depth < self.max_depth:
                new_links_added = 0
                for outlink in page_result.outlinks:
                    # Normalize and check if we should crawl this URL
                    normalized_outlink = URLUtils.normalize_url(outlink)
                    
                    # Check crawl criteria
                    if URLUtils.should_crawl_url(normalized_outlink, seed_host, visited_normalized):
                        frontier.append((normalized_outlink, depth + 1))
                        new_links_added += 1
                        self.logger.debug(f"Added to frontier: {normalized_outlink} (depth {depth + 1})")
                    else:
                        self.logger.debug(f"Skipping outlink: {normalized_outlink} (filtered out)")
                
                    
            else:
                self.logger.debug(f"Skipping outlinks at max depth {depth}")
        
        # Build final report
        self.logger.info(f"Crawl complete. Processed {len(page_results)} pages successfully, {len(pages_info) - len(page_results)} failed")
        
        report = self._build_crawl_report(seed_url, page_results, pages_info)
        
        
        self.logger.info(f"Final report: {report.pages_total} pages, {report.bugs_total} bugs found")
        return report
    
    def _extract_seed_host(self, seed_url: str) -> str:
        """
        Extract host from seed URL for boundary checking.
        
        Args:
            seed_url: Starting URL
            
        Returns:
            Host string for comparison
        """
        parsed = urlparse(seed_url)
        return parsed.netloc
    
    async def _inspect_page_with_retry(
        self,
        url: str,
        inspector: Inspector
    ) -> Optional[PageResult]:
        """
        Inspect a page with retry logic.
        
        Args:
            url: URL to inspect
            inspector: Inspector instance
            
        Returns:
            PageResult if successful, None if all retries failed
        """
        for attempt in range(self.max_retries):
            try:
                self.logger.debug(f"Inspecting {url} (attempt {attempt + 1}/{self.max_retries})")
                result = await inspector.inspect_page(url)
                return result
            except Exception as e:
                self.logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt == self.max_retries - 1:
                    self.logger.error(f"All {self.max_retries} attempts failed for {url}")
                    return None
                # Wait briefly before retry
                await asyncio.sleep(1)
        
        return None
    
    def _build_crawl_report(
        self,
        seed_url: str,
        page_results: List[PageResult],
        pages_info: List[Dict]
    ) -> CrawlReport:
        """
        Build final crawl report from page results.
        
        Args:
            seed_url: Original seed URL
            page_results: List of successful page inspection results
            pages_info: List of page metadata (url, depth, status)
            
        Returns:
            Complete crawl report
        """
        # Aggregate all bugs from all pages
        all_bugs = []
        for page_result in page_results:
            all_bugs.extend(page_result.findings)
        
        # Create report
        report = CrawlReport(
            scanned_at=datetime.now().isoformat(),
            seed_url=seed_url,
            pages_total=len(pages_info),
            bugs_total=len(all_bugs),
            findings=all_bugs,
            pages=pages_info
        )
        
        return report