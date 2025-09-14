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
            
            # Check for SPA routes and add them
            spa_routes = await self._discover_spa_routes()
            processed_links.extend(spa_routes)
            
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
                
                # Smart hash filtering: preserve SPA routes, skip traditional anchors
                if link.startswith('#'):
                    if self._is_spa_route(link):
                        # Convert hash route to full URL
                        absolute_url = urljoin(base_url, link)
                    else:
                        # Skip traditional same-page anchors
                        continue
                
                # Convert relative URLs to absolute
                if link.startswith(('http://', 'https://')):
                    absolute_url = link
                else:
                    absolute_url = urljoin(base_url, link)
                
                # Parse and validate URL
                parsed = urlparse(absolute_url)
                if parsed.scheme in ('http', 'https') and parsed.netloc:
                    # For SPA routes, preserve the fragment; otherwise remove it
                    clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                    if parsed.query:
                        clean_url += f"?{parsed.query}"
                    
                    # Preserve fragment for SPA routes
                    if parsed.fragment and self._is_spa_route('#' + parsed.fragment):
                        clean_url += f"#{parsed.fragment}"
                    
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
    
    def _is_spa_route(self, hash_link: str) -> bool:
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
    
    async def _discover_spa_routes(self) -> List[str]:
        """
        Discover SPA routes through JavaScript analysis and bundle parsing.
        
        Returns:
            List of discovered SPA routes as full URLs
        """
        routes = []
        
        try:
            # Method 1: Check for React Router routes in JavaScript
            react_routes = await self._discover_react_routes()
            routes.extend(react_routes)
            
            # Method 2: Parse JavaScript bundles for route patterns
            bundle_routes = await self._parse_js_bundles()
            routes.extend(bundle_routes)
            
            # Method 3: Look for navigation elements with route-like hrefs
            nav_routes = await self._discover_navigation_routes()
            routes.extend(nav_routes)
            
        except Exception as e:
            print(f"Error discovering SPA routes: {str(e)}")
        
        # Convert relative routes to absolute URLs and filter
        absolute_routes = []
        for route in routes:
            if route and not route.startswith(('http://', 'https://')):
                absolute_url = urljoin(self.current_url, route)
                # Only include same-host routes
                if urlparse(absolute_url).netloc == self.current_host:
                    absolute_routes.append(absolute_url)
        
        return list(set(absolute_routes))  # Remove duplicates
    
    async def _discover_react_routes(self) -> List[str]:
        """Extract React Router routes from the page."""
        js_code = """
        () => {
            const routes = [];
            
            // Method 1: Check for React Router in window
            if (window.__REACT_ROUTER__) {
                // Extract routes from router instance if available
                try {
                    const router = window.__REACT_ROUTER__;
                    if (router.routes) {
                        router.routes.forEach(route => {
                            if (route.path) routes.push(route.path);
                        });
                    }
                } catch (e) {}
            }
            
            // Method 2: Look for navigation elements with React Router patterns
            const navElements = document.querySelectorAll('nav a, .nav a, [role="navigation"] a');
            navElements.forEach(link => {
                const href = link.getAttribute('href');
                if (href && !href.startsWith('http') && !href.startsWith('mailto:')) {
                    routes.push(href);
                }
            });
            
            return [...new Set(routes)]; // Remove duplicates
        }
        """
        
        try:
            return await self.page.evaluate(js_code)
        except Exception:
            return []
    
    async def _parse_js_bundles(self) -> List[str]:
        """Parse JavaScript bundles for route definitions."""
        js_code = """
        () => {
            const routes = [];
            
            // Get all script tags
            const scripts = Array.from(document.scripts);
            
            for (const script of scripts) {
                if (script.src && script.src.includes('index-')) {
                    // This is likely the main bundle - we'll analyze its content
                    try {
                        // Look for common route patterns in the current page's HTML
                        const pageContent = document.documentElement.innerHTML;
                        
                        // React Router patterns: to:"/about-me"
                        const reactRoutes = pageContent.match(/to:"([^"]+)"/g);
                        if (reactRoutes) {
                            reactRoutes.forEach(match => {
                                const route = match.match(/to:"([^"]+)"/)[1];
                                if (route && route.startsWith('/')) {
                                    routes.push(route);
                                }
                            });
                        }
                        
                        // Vue Router patterns: path:"/about"
                        const vueRoutes = pageContent.match(/path:"([^"]+)"/g);
                        if (vueRoutes) {
                            vueRoutes.forEach(match => {
                                const route = match.match(/path:"([^"]+)"/)[1];
                                if (route && route.startsWith('/')) {
                                    routes.push(route);
                                }
                            });
                        }
                        
                    } catch (e) {}
                }
            }
            
            return [...new Set(routes)]; // Remove duplicates
        }
        """
        
        try:
            return await self.page.evaluate(js_code)
        except Exception:
            return []
    
    async def _discover_navigation_routes(self) -> List[str]:
        """Discover routes from navigation elements."""
        js_code = """
        () => {
            const routes = [];
            
            // Look for navigation patterns
            const selectors = [
                'nav a[href]',
                '.navbar a[href]',
                '.navigation a[href]',
                '[role="navigation"] a[href]',
                '.menu a[href]',
                '.nav-links a[href]'
            ];
            
            selectors.forEach(selector => {
                try {
                    const links = document.querySelectorAll(selector);
                    links.forEach(link => {
                        const href = link.getAttribute('href');
                        if (href && 
                            !href.startsWith('http') && 
                            !href.startsWith('mailto:') && 
                            !href.startsWith('tel:') &&
                            !href.startsWith('javascript:')) {
                            routes.push(href);
                        }
                    });
                } catch (e) {}
            });
            
            return [...new Set(routes)]; // Remove duplicates
        }
        """
        
        try:
            return await self.page.evaluate(js_code)
        except Exception:
            return []
    
    async def get_navigation_metadata(self) -> dict:
        """
        Get metadata about navigation links for action recording.
        
        Returns:
            Dictionary mapping URLs to their navigation context (text, selector, etc.)
        """
        js_code = """
        () => {
            const navigationMap = {};
            
            // Look for navigation patterns
            const selectors = [
                'nav a[href]',
                '.navbar a[href]',
                '.navigation a[href]',
                '[role="navigation"] a[href]',
                '.menu a[href]',
                '.nav-links a[href]'
            ];
            
            selectors.forEach(selector => {
                try {
                    const links = document.querySelectorAll(selector);
                    links.forEach((link, index) => {
                        const href = link.getAttribute('href');
                        if (href && 
                            !href.startsWith('http') && 
                            !href.startsWith('mailto:') && 
                            !href.startsWith('tel:') &&
                            !href.startsWith('javascript:')) {
                            
                            // Create a unique selector for this link
                            const linkText = link.textContent?.trim() || '';
                            const linkSelector = `${selector.split('[')[0]}:nth-of-type(${index + 1})`;
                            
                            navigationMap[href] = {
                                text: linkText,
                                selector: linkSelector,
                                originalSelector: selector,
                                title: link.getAttribute('title') || '',
                                ariaLabel: link.getAttribute('aria-label') || ''
                            };
                        }
                    });
                } catch (e) {}
            });
            
            return navigationMap;
        }
        """
        
        try:
            return await self.page.evaluate(js_code)
        except Exception:
            return {}
