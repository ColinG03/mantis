"""
Web crawler with BFS traversal and retry logic.
"""

import asyncio
from collections import deque
from typing import Set, List, Dict, Optional, Callable
from datetime import datetime
from urllib.parse import urlparse

from core.types import PageResult, CrawlReport, Bug, Inspector
from orchestrator.url_utils import URLUtils


class Crawler:
    """
    BFS web crawler that orchestrates page inspection and builds crawl reports.
    """
    
    def __init__(self, max_depth: int = 3, max_pages: int = 50, max_retries: int = 3, verbose: bool = False):
        """
        Initialize crawler with limits.
        
        Args:
            max_depth: Maximum crawl depth from seed URL
            max_pages: Maximum total pages to crawl
            max_retries: Maximum retries per failed page
            verbose: Enable verbose output
        """
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.max_retries = max_retries
        self.verbose = verbose
    
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
        if self.verbose:
            print(f"Starting crawl of {seed_url} (max_depth={self.max_depth}, max_pages={self.max_pages})")
        
        # Initialize crawl state
        seed_host = self._extract_seed_host(seed_url)
        frontier = deque([(seed_url, 0)])  # (url, depth) tuples
        visited = set()  # URLs we've already processed
        visited_normalized = set()  # Normalized URLs for deduplication
        page_results = []  # Successful page inspection results
        pages_info = []  # Page metadata for report
        crawled_count = 0
        total_bugs_found = 0
        
        if self.verbose:
            print(f"Seed host: {seed_host}")
        
        
        # BFS crawling loop
        while frontier and crawled_count < self.max_pages:
            current_url, depth = frontier.popleft()
            
            # Skip if already visited (exact URL)
            if current_url in visited:
                continue
                
            # Skip if normalized version already visited (path parameter deduplication)
            normalized_url = URLUtils.detect_path_parameters(current_url)
            if normalized_url in visited_normalized:
                if self.verbose:
                    print(f"Skipping {current_url} - normalized version already visited")
                continue
            
            # Mark as visited
            visited.add(current_url)
            visited_normalized.add(normalized_url)
            crawled_count += 1
            
            # Progress callback
            if progress_callback:
                progress_callback(current_url, crawled_count, self.max_pages)
            
            if self.verbose:
                print(f"Crawling page {crawled_count}/{self.max_pages}: {current_url} (depth {depth})")
            
            # Check content type before inspection to avoid PDF navigation timeouts
            content_type = await URLUtils.check_content_type(current_url)
            should_inspect = URLUtils.should_inspect_url(current_url, content_type)
            
            if not should_inspect:
                # Skip inspection for non-HTML content (PDFs, images, etc.)
                pages_info.append({
                    "url": current_url,
                    "depth": depth,
                    "status": 0, # We mark this as 0 because it's not a HTTP status code, rather just a marker that this was skipped. 0 won't break the check of <400 being successful.
                    "content_type": content_type
                })
                if self.verbose:
                    print(f"Skipping non-HTML content: {current_url} (type: {content_type})")
                continue
            
            # Inspect the page
            page_result = await self._inspect_page_with_retry(current_url, inspector)
            
            if page_result is None:
                # Failed to inspect page - record as failed but continue
                pages_info.append({
                    "url": current_url,
                    "depth": depth,
                    "status": None  # Failed
                })
                if self.verbose:
                    print(f"Failed to inspect {current_url} after {self.max_retries} retries")
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
            
            if self.verbose:
                print(f"Found {bugs_on_this_page} bugs and {len(page_result.outlinks)} outlinks on {current_url}")
            
            
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
                        if self.verbose:
                            print(f"Added to frontier: {normalized_outlink} (depth {depth + 1})")
                    else:
                        if self.verbose:
                            print(f"Skipping outlink: {normalized_outlink} (filtered out)")
                
                    
            else:
                if self.verbose:
                    print(f"Skipping outlinks at max depth {depth}")
        
        # Build final report
        if self.verbose:
            print(f"Crawl complete. Processed {len(page_results)} pages successfully, {len(pages_info) - len(page_results)} failed")
        
        report = self._build_crawl_report(seed_url, page_results, pages_info)
        
        # Deduplicate bugs if we have any
        if report.findings:
            report = await self._deduplicate_bugs(report, inspector)
        
        if self.verbose:
            print(f"Final report: {report.pages_total} pages, {report.bugs_total} bugs found")
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
                if self.verbose:
                    print(f"Inspecting {url} (attempt {attempt + 1}/{self.max_retries})")
                result = await inspector.inspect_page(url)
                return result
            except Exception as e:
                if self.verbose:
                    print(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt == self.max_retries - 1:
                    if self.verbose:
                        print(f"All {self.max_retries} attempts failed for {url}")
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
    
    async def _deduplicate_bugs(self, report: CrawlReport, inspector: Inspector) -> CrawlReport:
        """
        Deduplicate bugs in the crawl report using the same model that was used for scanning.
        
        Args:
            report: Original crawl report with potentially duplicate bugs
            inspector: Inspector instance to get the model configuration
            
        Returns:
            Updated crawl report with deduplicated bugs
        """
        try:
            # Import the deduplicator
            from inspector.utils.bug_deduplicator import BugDeduplicator
            
            # Get the model from the inspector's scan config
            model = getattr(inspector, 'scan_config', None)
            model_name = model.model if model else 'cohere'
            
            if self.verbose:
                print(f"Starting bug deduplication using {model_name} model...")
            
            # Create deduplicator and process bugs
            deduplicator = BugDeduplicator(model=model_name, verbose=self.verbose)
            deduplicated_bugs = await deduplicator.deduplicate_bugs(report.findings)
            
            # Update the report
            original_count = len(report.findings)
            report.findings = deduplicated_bugs
            report.bugs_total = len(deduplicated_bugs)
            
            if original_count != len(deduplicated_bugs):
                if self.verbose:
                    print(f"✅ Deduplication reduced bugs from {original_count} to {len(deduplicated_bugs)}")
            else:
                if self.verbose:
                    print("No duplicate bugs found")
            
            return report
            
        except Exception as e:
            if self.verbose:
                print(f"❌ Bug deduplication failed: {str(e)}")
                print("Continuing with original bug list")
            return report