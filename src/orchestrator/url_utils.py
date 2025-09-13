"""
URL utilities for normalization, deduplication, and path parameter detection.
"""

from urllib.parse import urlparse, urljoin, urlunparse
from typing import Set, List
import re


class URLUtils:
    """Utilities for URL processing in the crawler."""
    
    @staticmethod
    def normalize_url(url: str) -> str:
        """
        Normalize a URL for consistent comparison.
        
        - Strips fragments (#section)
        - Ensures consistent trailing slash handling
        - Converts to lowercase domain
        
        Args:
            url: Raw URL to normalize
            
        Returns:
            Normalized URL string
        """
        parsed = urlparse(url)
        
        # Lowercase the domain, preserve path case
        normalized_netloc = parsed.netloc.lower()
        
        # Strip fragment
        # Handle trailing slash consistently - remove it for normalization
        path = parsed.path.rstrip('/')
        if not path:  # Root path should be "/"
            path = '/'
        
        # Reconstruct without fragment
        normalized = urlunparse((
            parsed.scheme,
            normalized_netloc,
            path,
            parsed.params,
            parsed.query,
            None  # No fragment
        ))
        
        return normalized
    
    @staticmethod
    def is_same_host(url1: str, url2: str) -> bool:
        """
        Check if two URLs are on the same host.
        
        Args:
            url1: First URL
            url2: Second URL
            
        Returns:
            True if same host, False otherwise
        """
        parsed1 = urlparse(url1)
        parsed2 = urlparse(url2)
        
        # Compare hostnames (ignore protocol)
        return parsed1.netloc.lower() == parsed2.netloc.lower()
    
    @staticmethod
    def detect_path_parameters(url: str) -> str:
        """
        Detect and normalize path parameters (e.g., /user/123 -> /user/*).
        
        This helps deduplicate URLs that differ only by ID parameters.
        
        Args:
            url: URL to analyze
            
        Returns:
            URL with path parameters normalized to wildcards
        """
        parsed = urlparse(url)
        path_parts = parsed.path.strip('/').split('/')
        
        normalized_parts = []
        for part in path_parts:
            # Check if part looks like an ID parameter
            if URLUtils._is_id_parameter(part):
                normalized_parts.append('*')
            else:
                normalized_parts.append(part)
        
        # Reconstruct the URL with normalized path
        normalized_path = '/' + '/'.join(normalized_parts) if normalized_parts != [''] else '/'
        
        normalized_url = urlunparse((
            parsed.scheme,
            parsed.netloc,
            normalized_path,
            parsed.params,
            parsed.query,
            parsed.fragment
        ))
        
        return normalized_url
    
    @staticmethod
    def _is_id_parameter(path_part: str) -> bool:
        """
        Determine if a path part looks like an ID parameter.
        
        Args:
            path_part: Single path segment to analyze
            
        Returns:
            True if it looks like an ID parameter
        """
        # Numeric IDs (e.g., "123", "456")
        if path_part.isdigit():
            return True
        
        # UUID format (basic check)
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        if re.match(uuid_pattern, path_part, re.IGNORECASE):
            return True
        
        return False
    
    @staticmethod
    def should_crawl_url(url: str, seed_host: str, visited: Set[str]) -> bool:
        """
        Determine if a URL should be crawled.
        
        Args:
            url: URL to check
            seed_host: Original host we started crawling from
            visited: Set of already visited URLs
            
        Returns:
            True if URL should be crawled, False otherwise
        """
        # Parse URL to check host
        parsed = urlparse(url)
        url_host = parsed.netloc.lower()
        
        # Must be same host
        if url_host != seed_host.lower():
            return False
        
        # Check if already visited (using path parameter normalization)
        normalized_url = URLUtils.detect_path_parameters(url)
        if normalized_url in visited:
            return False
        
        return True