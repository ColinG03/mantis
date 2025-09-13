from typing import Dict
from playwright.async_api import Page


class PerformanceTracker:
    """
    Tracks and collects performance metrics during page inspection.
    
    This class helps identify performance-related UI issues and provides
    timing data for the PageResult.
    """
    
    def __init__(self):
        self.metrics = {}
        
    async def collect_timings(self, page: Page) -> Dict[str, float]:
        """
        Collect comprehensive timing metrics from the page.
        
        Args:
            page: Playwright page object
            
        Returns:
            Dictionary of timing metrics in milliseconds
        """
        try:
            # Use JavaScript to get performance timing data
            timing_data = await page.evaluate("""
            () => {
                const perfData = performance.getEntriesByType('navigation')[0];
                const paintEntries = performance.getEntriesByType('paint');
                
                if (!perfData) {
                    return {};
                }
                
                // Core navigation timings
                const timings = {
                    // DNS and connection
                    dns_lookup: perfData.domainLookupEnd - perfData.domainLookupStart,
                    tcp_connect: perfData.connectEnd - perfData.connectStart,
                    ssl_handshake: perfData.secureConnectionStart > 0 ? 
                        perfData.connectEnd - perfData.secureConnectionStart : 0,
                    
                    // Request/Response
                    request_start: perfData.requestStart - perfData.navigationStart,
                    response_start: perfData.responseStart - perfData.navigationStart,
                    response_end: perfData.responseEnd - perfData.navigationStart,
                    
                    // Document processing
                    dom_loading: perfData.domLoading - perfData.navigationStart,
                    dom_interactive: perfData.domInteractive - perfData.navigationStart,
                    dom_content_loaded: perfData.domContentLoadedEventEnd - perfData.navigationStart,
                    dom_complete: perfData.domComplete - perfData.navigationStart,
                    
                    // Load events
                    load_event_start: perfData.loadEventStart - perfData.navigationStart,
                    load_event_end: perfData.loadEventEnd - perfData.navigationStart,
                    
                    // Total times
                    total_load_time: perfData.loadEventEnd - perfData.navigationStart,
                    dcl_time: perfData.domContentLoadedEventEnd - perfData.domContentLoadedEventStart
                };
                
                // Add paint timings
                paintEntries.forEach(entry => {
                    if (entry.name === 'first-paint') {
                        timings.first_paint = entry.startTime;
                    } else if (entry.name === 'first-contentful-paint') {
                        timings.first_contentful_paint = entry.startTime;
                    }
                });
                
                // Add largest contentful paint if available
                try {
                    const lcpEntries = performance.getEntriesByType('largest-contentful-paint');
                    if (lcpEntries.length > 0) {
                        timings.largest_contentful_paint = lcpEntries[lcpEntries.length - 1].startTime;
                    }
                } catch (e) {
                    // LCP might not be available in all browsers
                }
                
                return timings;
            }
            """)
            
            # Add resource timing summary
            resource_summary = await self._get_resource_summary(page)
            timing_data.update(resource_summary)
            
            return timing_data
            
        except Exception as e:
            print(f"Failed to collect timing data: {str(e)}")
            return {}
    
    async def _get_resource_summary(self, page: Page) -> Dict[str, float]:
        """
        Get summary statistics about resource loading.
        
        Args:
            page: Playwright page object
            
        Returns:
            Dictionary with resource timing summaries
        """
        try:
            return await page.evaluate("""
            () => {
                const resources = performance.getEntriesByType('resource');
                
                if (resources.length === 0) {
                    return {};
                }
                
                let totalSize = 0;
                let totalDuration = 0;
                let slowestResource = 0;
                let resourceCounts = {
                    images: 0,
                    scripts: 0,
                    stylesheets: 0,
                    fonts: 0,
                    xhr: 0,
                    other: 0
                };
                
                resources.forEach(resource => {
                    const duration = resource.responseEnd - resource.startTime;
                    totalDuration += duration;
                    slowestResource = Math.max(slowestResource, duration);
                    
                    // Estimate size from transfer size
                    if (resource.transferSize) {
                        totalSize += resource.transferSize;
                    }
                    
                    // Categorize resources
                    const initiatorType = resource.initiatorType;
                    if (initiatorType === 'img') {
                        resourceCounts.images++;
                    } else if (initiatorType === 'script') {
                        resourceCounts.scripts++;
                    } else if (initiatorType === 'css') {
                        resourceCounts.stylesheets++;
                    } else if (resource.name.includes('font') || initiatorType === 'font') {
                        resourceCounts.fonts++;
                    } else if (initiatorType === 'xmlhttprequest' || initiatorType === 'fetch') {
                        resourceCounts.xhr++;
                    } else {
                        resourceCounts.other++;
                    }
                });
                
                return {
                    resource_count: resources.length,
                    total_resource_size: totalSize,
                    average_resource_duration: totalDuration / resources.length,
                    slowest_resource_duration: slowestResource,
                    image_count: resourceCounts.images,
                    script_count: resourceCounts.scripts,
                    stylesheet_count: resourceCounts.stylesheets,
                    font_count: resourceCounts.fonts,
                    xhr_count: resourceCounts.xhr
                };
            }
            """)
            
        except Exception as e:
            print(f"Failed to get resource summary: {str(e)}")
            return {}
    
    async def get_core_web_vitals(self, page: Page) -> Dict[str, float]:
        """
        Collect Core Web Vitals metrics if available.
        
        Args:
            page: Playwright page object
            
        Returns:
            Dictionary with CWV metrics
        """
        try:
            return await page.evaluate("""
            () => {
                const vitals = {};
                
                // Get LCP (Largest Contentful Paint)
                try {
                    const lcpEntries = performance.getEntriesByType('largest-contentful-paint');
                    if (lcpEntries.length > 0) {
                        vitals.lcp = lcpEntries[lcpEntries.length - 1].startTime;
                    }
                } catch (e) {}
                
                // Get FID (First Input Delay) - only available after user interaction
                // This would need to be collected differently in a real implementation
                
                // Get CLS (Cumulative Layout Shift)
                try {
                    const clsEntries = performance.getEntriesByType('layout-shift');
                    let clsScore = 0;
                    clsEntries.forEach(entry => {
                        if (!entry.hadRecentInput) {
                            clsScore += entry.value;
                        }
                    });
                    vitals.cls = clsScore;
                } catch (e) {}
                
                return vitals;
            }
            """)
            
        except Exception as e:
            print(f"Failed to get Core Web Vitals: {str(e)}")
            return {}
    
    async def measure_interaction_timing(self, page: Page, action_func) -> float:
        """
        Measure the timing of a specific interaction.
        
        Args:
            page: Playwright page object
            action_func: Async function that performs the interaction
            
        Returns:
            Duration of the interaction in milliseconds
        """
        try:
            # Mark start time
            await page.evaluate("performance.mark('interaction-start')")
            
            # Perform the action
            await action_func()
            
            # Mark end time and measure
            duration = await page.evaluate("""
            () => {
                performance.mark('interaction-end');
                performance.measure('interaction-duration', 'interaction-start', 'interaction-end');
                const measure = performance.getEntriesByName('interaction-duration')[0];
                return measure ? measure.duration : 0;
            }
            """)
            
            return duration
            
        except Exception as e:
            print(f"Failed to measure interaction timing: {str(e)}")
            return 0.0
