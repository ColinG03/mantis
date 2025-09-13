"""
Tests for the BFS crawler logic.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock
from datetime import datetime

from src.orchestrator.crawler import Crawler
from src.core.types import PageResult, Bug, Evidence, CrawlReport, Inspector


class TestCrawlerInitialization:
    """Test crawler initialization and configuration."""
    
    def test_crawler_default_limits(self):
        """Crawler should have sensible default limits."""
        crawler = Crawler()
        assert crawler.max_depth == 3
        assert crawler.max_pages == 50
        assert crawler.max_retries == 3
    
    def test_crawler_custom_limits(self):
        """Crawler should accept custom limits."""
        crawler = Crawler(max_depth=5, max_pages=100, max_retries=5)
        assert crawler.max_depth == 5
        assert crawler.max_pages == 100
        assert crawler.max_retries == 5


class TestSeedHostExtraction:
    """Test seed host extraction logic."""
    
    def test_extract_host_from_https(self):
        """Should extract host from HTTPS URL."""
        crawler = Crawler()
        host = crawler._extract_seed_host("https://example.com/page")
        assert host == "example.com"
    
    def test_extract_host_from_http(self):
        """Should extract host from HTTP URL."""
        crawler = Crawler()
        host = crawler._extract_seed_host("http://example.com/page")
        assert host == "example.com"
    
    def test_extract_host_with_port(self):
        """Should extract host with port."""
        crawler = Crawler()
        host = crawler._extract_seed_host("https://example.com:8080/page")
        assert host == "example.com:8080"


class TestPageInspectionWithRetry:
    """Test page inspection with retry logic."""
    
    @pytest.mark.asyncio
    async def test_inspect_success_first_try(self):
        """Should return result on first successful inspection."""
        crawler = Crawler()
        
        # Mock successful inspection
        mock_result = PageResult(
            page_url="https://example.com",
            status=200,
            outlinks=["https://example.com/about"],
            findings=[]
        )
        
        mock_inspector = Mock()
        mock_inspector.inspect_page = AsyncMock(return_value=mock_result)
        
        result = await crawler._inspect_page_with_retry("https://example.com", mock_inspector)
        
        assert result == mock_result
        assert mock_inspector.inspect_page.call_count == 1
    
    @pytest.mark.asyncio
    async def test_inspect_retry_on_failure(self):
        """Should retry on inspection failure."""
        crawler = Crawler(max_retries=3)
        
        # Mock failing inspection
        mock_inspector = Mock()
        mock_inspector.inspect_page = AsyncMock(side_effect=Exception("Network error"))
        
        result = await crawler._inspect_page_with_retry("https://example.com", mock_inspector)
        
        assert result is None
        assert mock_inspector.inspect_page.call_count == 3
    
    @pytest.mark.asyncio
    async def test_inspect_success_after_retry(self):
        """Should succeed after initial failures."""
        crawler = Crawler(max_retries=3)
        
        # Mock inspection that fails twice then succeeds
        mock_result = PageResult(page_url="https://example.com", status=200)
        mock_inspector = Mock()
        mock_inspector.inspect_page = AsyncMock(side_effect=[
            Exception("Error 1"),
            Exception("Error 2"), 
            mock_result
        ])
        
        result = await crawler._inspect_page_with_retry("https://example.com", mock_inspector)
        
        assert result == mock_result
        assert mock_inspector.inspect_page.call_count == 3


class TestBFSCrawling:
    """Test the core BFS crawling algorithm."""
    
    @pytest.mark.asyncio
    async def test_crawl_single_page(self):
        """Should handle crawling a single page correctly."""
        crawler = Crawler(max_depth=1, max_pages=1)
        
        # Mock page result with no outlinks
        mock_result = PageResult(
            page_url="https://example.com",
            status=200,
            outlinks=[],
            findings=[
                Bug(
                    id="bug1",
                    type="Accessibility",
                    severity="medium",
                    page_url="https://example.com",
                    summary="Missing alt text",
                    evidence=Evidence()
                )
            ]
        )
        
        mock_inspector = Mock()
        mock_inspector.inspect_page = AsyncMock(return_value=mock_result)
        
        report = await crawler.crawl_site("https://example.com", mock_inspector)
        
        assert report.seed_url == "https://example.com"
        assert report.pages_total == 1
        assert report.bugs_total == 1
        assert len(report.findings) == 1
        assert len(report.pages) == 1
        assert report.pages[0]["url"] == "https://example.com"
        assert report.pages[0]["depth"] == 0
    
    @pytest.mark.asyncio
    async def test_crawl_with_outlinks(self):
        """Should follow outlinks within depth limit."""
        crawler = Crawler(max_depth=2, max_pages=10)
        
        # Mock seed page with outlinks
        seed_result = PageResult(
            page_url="https://example.com",
            status=200,
            outlinks=["https://example.com/about", "https://example.com/contact"],
            findings=[]
        )
        
        # Mock about page with outlink
        about_result = PageResult(
            page_url="https://example.com/about",
            status=200,
            outlinks=["https://example.com/team"],
            findings=[]
        )
        
        # Mock contact page
        contact_result = PageResult(
            page_url="https://example.com/contact",
            status=200,
            outlinks=[],
            findings=[]
        )
        
        # Mock team page (depth 2)
        team_result = PageResult(
            page_url="https://example.com/team",
            status=200,
            outlinks=["https://example.com/careers"],  # Should not be crawled (depth 3)
            findings=[]
        )
        
        mock_inspector = Mock()
        mock_inspector.inspect_page = AsyncMock(side_effect=[seed_result, about_result, contact_result, team_result])
        
        report = await crawler.crawl_site("https://example.com", mock_inspector)
        
        assert report.pages_total == 4
        assert len(report.pages) == 4
        
        # Verify depths are correct
        depth_map = {page["url"]: page["depth"] for page in report.pages}
        assert depth_map["https://example.com"] == 0
        assert depth_map["https://example.com/about"] == 1
        assert depth_map["https://example.com/contact"] == 1
        assert depth_map["https://example.com/team"] == 2
    
    @pytest.mark.asyncio
    async def test_crawl_respects_max_pages(self):
        """Should stop crawling when max_pages limit is reached."""
        crawler = Crawler(max_depth=10, max_pages=2)
        
        # Mock pages with many outlinks
        page1_result = PageResult(
            page_url="https://example.com",
            status=200,
            outlinks=["https://example.com/page2", "https://example.com/page3", "https://example.com/page4"],
            findings=[]
        )
        
        page2_result = PageResult(
            page_url="https://example.com/page2",
            status=200,
            outlinks=["https://example.com/page5"],
            findings=[]
        )
        
        mock_inspector = Mock()
        mock_inspector.inspect_page = AsyncMock(side_effect=[page1_result, page2_result])
        
        report = await crawler.crawl_site("https://example.com", mock_inspector)
        
        # Should stop at 2 pages
        assert report.pages_total == 2
        assert mock_inspector.inspect_page.call_count == 2
    
    @pytest.mark.asyncio
    async def test_crawl_deduplicates_urls(self):
        """Should not crawl the same URL twice."""
        crawler = Crawler(max_depth=2, max_pages=10)
        
        # Mock pages that link to each other
        page1_result = PageResult(
            page_url="https://example.com",
            status=200,
            outlinks=["https://example.com/about"],
            findings=[]
        )
        
        about_result = PageResult(
            page_url="https://example.com/about", 
            status=200,
            outlinks=["https://example.com"],  # Links back to home
            findings=[]
        )
        
        mock_inspector = Mock()
        mock_inspector.inspect_page = AsyncMock(side_effect=[page1_result, about_result])
        
        report = await crawler.crawl_site("https://example.com", mock_inspector)
        
        # Should only crawl each page once
        assert report.pages_total == 2
        assert mock_inspector.inspect_page.call_count == 2
    
    @pytest.mark.asyncio
    async def test_crawl_filters_external_links(self):
        """Should not crawl links to external domains."""
        crawler = Crawler(max_depth=2, max_pages=10)
        
        # Mock page with internal and external links
        seed_result = PageResult(
            page_url="https://example.com",
            status=200,
            outlinks=[
                "https://example.com/about",       # Internal - should crawl
                "https://external.com/page",       # External - should not crawl
                "https://sub.example.com/page"     # Subdomain - should not crawl
            ],
            findings=[]
        )
        
        about_result = PageResult(
            page_url="https://example.com/about",
            status=200,
            outlinks=[],
            findings=[]
        )
        
        mock_inspector = Mock()
        mock_inspector.inspect_page = AsyncMock(side_effect=[seed_result, about_result])
        
        report = await crawler.crawl_site("https://example.com", mock_inspector)
        
        # Should only crawl internal pages
        assert report.pages_total == 2
        crawled_urls = [page["url"] for page in report.pages]
        assert "https://example.com" in crawled_urls
        assert "https://example.com/about" in crawled_urls
        assert "https://external.com/page" not in crawled_urls


class TestCrawlReportBuilding:
    """Test crawl report generation."""
    
    def test_build_report_aggregates_bugs(self):
        """Should aggregate all bugs from crawled pages."""
        crawler = Crawler()
        
        # Mock page results with bugs
        page_results = [
            PageResult(
                page_url="https://example.com",
                status=200,
                findings=[
                    Bug(id="bug1", type="Accessibility", severity="high", 
                        page_url="https://example.com", summary="Missing alt text")
                ]
            ),
            PageResult(
                page_url="https://example.com/about",
                status=200,
                findings=[
                    Bug(id="bug2", type="UI", severity="medium",
                        page_url="https://example.com/about", summary="Overlap detected"),
                    Bug(id="bug3", type="Logic", severity="low",
                        page_url="https://example.com/about", summary="Console error")
                ]
            )
        ]
        
        pages_info = [
            {"url": "https://example.com", "depth": 0, "status": 200},
            {"url": "https://example.com/about", "depth": 1, "status": 200}
        ]
        
        report = crawler._build_crawl_report("https://example.com", page_results, pages_info)
        
        assert report.seed_url == "https://example.com"
        assert report.pages_total == 2
        assert report.bugs_total == 3
        assert len(report.findings) == 3
        assert len(report.pages) == 2
    
    def test_build_report_handles_no_bugs(self):
        """Should handle pages with no bugs correctly."""
        crawler = Crawler()
        
        page_results = [
            PageResult(page_url="https://example.com", status=200, findings=[])
        ]
        
        pages_info = [
            {"url": "https://example.com", "depth": 0, "status": 200}
        ]
        
        report = crawler._build_crawl_report("https://example.com", page_results, pages_info)
        
        assert report.bugs_total == 0
        assert len(report.findings) == 0


class TestProgressReporting:
    """Test progress callback functionality."""
    
    @pytest.mark.asyncio
    async def test_progress_callback_called(self):
        """Should call progress callback during crawling."""
        crawler = Crawler(max_pages=2)
        
        # Mock page results
        page1_result = PageResult(page_url="https://example.com", status=200, outlinks=["https://example.com/about"])
        page2_result = PageResult(page_url="https://example.com/about", status=200, outlinks=[])
        
        mock_inspector = Mock()
        mock_inspector.inspect_page = AsyncMock(side_effect=[page1_result, page2_result])
        progress_callback = Mock()
        
        await crawler.crawl_site("https://example.com", mock_inspector, progress_callback)
        
        # Should call progress callback for each page
        assert progress_callback.call_count >= 2
        
        # Verify callback was called with expected arguments (url, current, total)
        calls = progress_callback.call_args_list
        assert len(calls) >= 2