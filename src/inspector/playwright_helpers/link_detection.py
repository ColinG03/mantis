from typing import List, Set
from urllib.parse import urljoin, urlparse
from playwright.async_api import Page


class LinkDetector:
    """
    Safely detect and collect outlinks from a page without navigation.
    
    This class extracts all links from the current page that the orchestrator
    should consider for crawling.
    """
    
    def __init__(self, page: Page, current_url: str):
        self.page = page
        self.current_url = current_url
        self.current_host = urlparse(current_url).netloc
        
    async def collect_outlinks(self) -> List[str]:
        """
        Collect all outlinks from the current page without clicking them.
        
        Returns:
            List of unique URLs found on the page
        """
        try:
            # Get all links from the page
            raw_links = await self._extract_all_links()
            
            # Process and filter links
            processed_links = self._process_links(raw_links)
            
            # Remove duplicates and return
            return list(set(processed_links))
            
        except Exception as e:
            print(f"Error collecting outlinks: {str(e)}")
            return []
    
    async def _extract_all_links(self) -> List[str]:
        """Extract all href attributes from anchor tags"""
        
        # JavaScript to extract all links
        js_code = """
        () => {
            const links = [];
            
            // Get all anchor tags with href
            const anchors = document.querySelectorAll('a[href]');
            anchors.forEach(anchor => {
                const href = anchor.getAttribute('href');
                if (href && href.trim()) {
                    links.push(href.trim());
                }
            });
            
            // Also check for links in onclick handlers or data attributes
            const clickableElements = document.querySelectorAll('[onclick], [data-href], [data-url]');
            clickableElements.forEach(element => {
                // Extract URLs from onclick handlers
                const onclick = element.getAttribute('onclick');
                if (onclick) {
                    const urlMatch = onclick.match(/(?:location\.href|window\.open|navigate)\s*=?\s*['"`]([^'"`]+)['"`]/);
                    if (urlMatch) {
                        links.push(urlMatch[1]);
                    }
                }
                
                // Extract from data attributes
                const dataHref = element.getAttribute('data-href') || element.getAttribute('data-url');
                if (dataHref) {
                    links.push(dataHref);
                }
            });
            
            return links;
        }
        """
        
        return await self.page.evaluate(js_code)
    
    def _process_links(self, raw_links: List[str]) -> List[str]:
        """
        Process raw links to convert relative URLs to absolute and filter invalid ones.
        
        Args:
            raw_links: List of raw href values from the page
            
        Returns:
            List of processed absolute URLs
        """
        processed = []
        base_url = self.current_url
        
        for link in raw_links:
            try:
                # Skip empty links
                if not link or link.strip() == '':
                    continue
                
                # Skip javascript: and mailto: links
                if link.startswith(('javascript:', 'mailto:', 'tel:', 'sms:')):
                    continue
                
                # Skip anchor links (same page)
                if link.startswith('#'):
                    continue
                
                # Convert relative URLs to absolute
                if link.startswith(('http://', 'https://')):
                    absolute_url = link
                else:
                    absolute_url = urljoin(base_url, link)
                
                # Parse and validate URL
                parsed = urlparse(absolute_url)
                if parsed.scheme in ('http', 'https') and parsed.netloc:
                    # Remove fragment (anchor) part for deduplication
                    clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                    if parsed.query:
                        clean_url += f"?{parsed.query}"
                    
                    processed.append(clean_url)
                    
            except Exception:
                # Skip malformed URLs
                continue
                
        return processed
    
    def get_same_host_links(self, links: List[str]) -> List[str]:
        """
        Filter links to only include those from the same host.
        
        Args:
            links: List of absolute URLs
            
        Returns:
            List of URLs from the same host
        """
        filtered = []
        
        for link in links:
            try:
                parsed = urlparse(link)
                if parsed.netloc == self.current_host:
                    filtered.append(link)
            except Exception:
                continue
                
        return filtered
    
    async def get_link_metadata(self) -> List[dict]:
        """
        Get additional metadata about links for analysis.
        This can be useful for the orchestrator to prioritize links.
        
        Returns:
            List of dictionaries with link metadata
        """
        js_code = """
        () => {
            const linkData = [];
            const anchors = document.querySelectorAll('a[href]');
            
            anchors.forEach((anchor, index) => {
                const href = anchor.getAttribute('href');
                if (href && href.trim()) {
                    linkData.push({
                        href: href.trim(),
                        text: anchor.textContent?.trim() || '',
                        title: anchor.getAttribute('title') || '',
                        rel: anchor.getAttribute('rel') || '',
                        target: anchor.getAttribute('target') || '',
                        visible: anchor.offsetParent !== null,
                        position: {
                            x: anchor.offsetLeft,
                            y: anchor.offsetTop
                        }
                    });
                }
            });
            
            return linkData;
        }
        """
        
        try:
            return await self.page.evaluate(js_code)
        except Exception:
            return []
