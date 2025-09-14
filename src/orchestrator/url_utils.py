"""
URL utilities for normalization, deduplication, and path parameter detection.
"""

from urllib.parse import urlparse, urljoin, urlunparse
from typing import Set, List, Optional
import re
import aiohttp
import asyncio


class URLUtils:
    """Utilities for URL processing in the crawler."""
    
    @staticmethod
    def normalize_url(url: str) -> str:
        """
        Normalize a URL for consistent comparison.
        
        - Strips fragments (#section) UNLESS they look like SPA routes
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
        
        # Handle trailing slash consistently
        path = parsed.path.rstrip('/')
        if not path:  # Root path should be "/"
            path = '/'
        
        # Determine if we should preserve the fragment (for SPA routes)
        preserve_fragment = parsed.fragment and URLUtils._is_spa_route('#' + parsed.fragment)
        
        # For SPA routes, ensure the path ends with slash for proper fragment URLs
        if preserve_fragment and not path.endswith('/'):
            path = path + '/'
        
        # Reconstruct with or without fragment based on SPA detection
        normalized = urlunparse((
            parsed.scheme,
            normalized_netloc,
            path,
            parsed.params,
            parsed.query,
            parsed.fragment if preserve_fragment else None
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
    
    @staticmethod
    async def check_content_type(url: str, timeout: int = 10) -> Optional[str]:
        """
        Check the content type of a URL using a HEAD request.
        
        Args:
            url: URL to check
            timeout: Request timeout in seconds
            
        Returns:
            Content type string (e.g., "text/html", "application/pdf") or None if failed
        """
        try:
            # Use aiohttp for async HEAD request
            timeout_config = aiohttp.ClientTimeout(total=timeout)
            async with aiohttp.ClientSession(timeout=timeout_config) as session:
                async with session.head(url) as response:
                    content_type = response.headers.get('content-type', '').lower()
                    # Extract main content type (remove charset and other parameters)
                    return content_type.split(';')[0].strip()
        except Exception as e:
            print(f"Failed to check content type for {url}: {e}")
            return None
    
    @staticmethod
    def is_html_content(content_type: Optional[str]) -> bool:
        """
        Determine if a content type represents HTML content that should be inspected.
        
        Args:
            content_type: Content type string from HTTP headers
            
        Returns:
            True if content should be inspected as a web page, False otherwise
        """
        if not content_type:
            # If we can't determine content type, assume it might be HTML
            return True
        
        # Content types that should be inspected
        html_types = {
            'text/html',
            'application/xhtml+xml',
            'text/xml',
            'application/xml',
            'text/plain'  # Many servers return text/plain for HTML pages
        }
        
        return content_type in html_types
    
    @staticmethod
    def is_binary_content(content_type: Optional[str]) -> bool:
        """
        Determine if a content type represents binary content that shouldn't be inspected.
        
        Args:
            content_type: Content type string from HTTP headers
            
        Returns:
            True if content is binary and shouldn't be inspected, False otherwise
        """
        if not content_type:
            return False
        
        # Common binary content types that shouldn't be inspected
        binary_types = {
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.ms-powerpoint',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            'application/zip',
            'application/x-zip-compressed',
            'application/octet-stream',
            'image/jpeg',
            'image/png',
            'image/gif',
            'image/webp',
            'image/svg+xml',
            'video/mp4',
            'video/mpeg',
            'video/quicktime',
            'video/webm',
            'audio/mpeg',
            'audio/wav',
            'audio/ogg',
            'audio/webm'
        }
        
        return content_type in binary_types
    
    @staticmethod
    def should_inspect_url(url: str, content_type: Optional[str] = None) -> bool:
        """
        Determine if a URL should be inspected based on content type.
        
        Args:
            url: URL to check
            content_type: Optional content type from HEAD request
            
        Returns:
            True if URL should be inspected, False otherwise
        """
        # If we have content type information, use it
        if content_type is not None:
            # Primary check: exclude known binary content
            if URLUtils.is_binary_content(content_type):
                return False
            # Allow text-based content types through (HTML, plain text, etc.)
            return True
        
        # Fallback to URL extension checking
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        # Common file extensions that shouldn't be inspected
        skip_extensions = {
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            '.zip', '.rar', '.7z', '.tar', '.gz',
            '.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.ico',
            '.mp4', '.avi', '.mov', '.webm', '.flv',
            '.mp3', '.wav', '.ogg', '.flac',
            '.exe', '.dmg', '.pkg', '.deb', '.rpm'
        }
        
        for ext in skip_extensions:
            if path.endswith(ext):
                return False
        
        return True
    
    @staticmethod
    def _is_spa_route(hash_link: str) -> bool:
        """
        Determine if a hash link is likely an SPA route vs a same-page anchor.
        
        SPA routes typically look like:
        - #/about, #/projects  
        - #/user/123
        
        Same-page anchors look like:
        - #section1, #top, #contact-form
        """
        # Remove the # prefix
        fragment = hash_link[1:] if hash_link.startswith('#') else hash_link
        
        # SPA route indicators
        spa_indicators = [
            fragment.startswith('/'),           # #/about, #/projects
            '/' in fragment,                    # #user/123, #app/dashboard  
            fragment in ['home', 'about', 'contact', 'projects', 'portfolio', 'blog', 'about-me'],  # common page names
        ]
        
        # Traditional anchor indicators (less likely to be routes)
        anchor_indicators = [
            fragment.isdigit(),                 # #123 (probably a section)
            fragment in ['top', 'bottom', 'header', 'footer', 'main'],  # page sections
            len(fragment.split('-')) > 2,       # #contact-form-section (descriptive anchors)
        ]
        
        # If any SPA indicator is true, treat as route
        if any(spa_indicators):
            return True
            
        # If any anchor indicator is true, treat as anchor
        if any(anchor_indicators):
            return False
            
        # Default: if it's a single word that could be a page, treat as route
        return len(fragment.split()) == 1 and len(fragment) > 2