"""
Tests for URL utilities.
"""

import pytest
from src.orchestrator.url_utils import URLUtils


class TestURLNormalization:
    """Test URL normalization functionality."""
    
    def test_normalize_strips_fragments(self):
        """URL normalization should strip fragment identifiers."""
        url = "https://example.com/page#section"
        expected = "https://example.com/page"
        assert URLUtils.normalize_url(url) == expected
    
    def test_normalize_handles_trailing_slash(self):
        """URL normalization should handle trailing slashes consistently."""
        url1 = "https://example.com/page"
        url2 = "https://example.com/page/"
        
        # Both should normalize to the same thing
        normalized1 = URLUtils.normalize_url(url1)
        normalized2 = URLUtils.normalize_url(url2)
        assert normalized1 == normalized2
    
    def test_normalize_lowercases_domain(self):
        """URL normalization should lowercase the domain."""
        url = "https://EXAMPLE.COM/Page"
        result = URLUtils.normalize_url(url)
        assert "example.com" in result
        assert "EXAMPLE.COM" not in result
    
    def test_normalize_preserves_path_case(self):
        """URL normalization should preserve path case."""
        url = "https://example.com/MyPage"
        result = URLUtils.normalize_url(url)
        assert "/MyPage" in result


class TestHostComparison:
    """Test same-host checking functionality."""
    
    def test_same_host_basic(self):
        """Should identify URLs on the same host."""
        url1 = "https://example.com/page1"
        url2 = "https://example.com/page2"
        assert URLUtils.is_same_host(url1, url2) is True
    
    def test_different_hosts(self):
        """Should identify URLs on different hosts."""
        url1 = "https://example.com/page"
        url2 = "https://other.com/page"
        assert URLUtils.is_same_host(url1, url2) is False
    
    def test_subdomain_different_host(self):
        """Should treat subdomains as different hosts."""
        url1 = "https://example.com/page"
        url2 = "https://sub.example.com/page"
        assert URLUtils.is_same_host(url1, url2) is False
    
    def test_protocol_ignored_for_host(self):
        """Should ignore protocol when comparing hosts."""
        url1 = "https://example.com/page"
        url2 = "http://example.com/page"
        assert URLUtils.is_same_host(url1, url2) is True


class TestPathParameterDetection:
    """Test path parameter detection and normalization."""
    
    def test_detect_numeric_id(self):
        """Should detect numeric IDs in paths."""
        url = "https://example.com/user/123"
        expected = "https://example.com/user/*"
        assert URLUtils.detect_path_parameters(url) == expected
    
    def test_detect_multiple_ids(self):
        """Should detect multiple ID parameters."""
        url = "https://example.com/user/123/post/456"
        expected = "https://example.com/user/*/post/*"
        assert URLUtils.detect_path_parameters(url) == expected
    
    def test_preserve_non_id_paths(self):
        """Should preserve paths that aren't ID parameters."""
        url = "https://example.com/about/team"
        assert URLUtils.detect_path_parameters(url) == url
    
    def test_detect_uuid_format(self):
        """Should detect UUID-format parameters."""
        url = "https://example.com/item/550e8400-e29b-41d4-a716-446655440000"
        expected = "https://example.com/item/*"
        assert URLUtils.detect_path_parameters(url) == expected


class TestCrawlDecision:
    """Test URL crawl decision logic."""
    
    def test_should_crawl_same_host(self):
        """Should crawl URLs on the same host."""
        url = "https://example.com/page2"
        seed_host = "example.com"
        visited = set()
        assert URLUtils.should_crawl_url(url, seed_host, visited) is True
    
    def test_should_not_crawl_different_host(self):
        """Should not crawl URLs on different hosts."""
        url = "https://other.com/page"
        seed_host = "example.com"
        visited = set()
        assert URLUtils.should_crawl_url(url, seed_host, visited) is False
    
    def test_should_not_crawl_visited(self):
        """Should not crawl already visited URLs."""
        url = "https://example.com/page"
        seed_host = "example.com"
        visited = {"https://example.com/page"}
        assert URLUtils.should_crawl_url(url, seed_host, visited) is False
    
    def test_should_crawl_with_path_params(self):
        """Should handle path parameter deduplication in crawl decision."""
        url1 = "https://example.com/user/123"
        url2 = "https://example.com/user/456"
        seed_host = "example.com"
        
        visited = set()
        # First user URL should be crawled
        assert URLUtils.should_crawl_url(url1, seed_host, visited) is True
        
        # Add normalized version to visited
        visited.add(URLUtils.detect_path_parameters(url1))
        # Second user URL should not be crawled (same pattern)
        assert URLUtils.should_crawl_url(url2, seed_host, visited) is False