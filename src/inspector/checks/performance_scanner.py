"""
Performance Scanner - Analyzes performance metrics and generates actionable bug reports.

This scanner takes the performance data collected by PerformanceTracker and analyzes it
against web performance standards to detect issues that impact user experience.
"""

import uuid
from typing import List, Dict, Any, Optional
from playwright.async_api import Page

try:
    from ...core.types import Bug, Evidence
    from .base_scanner import BaseScanner, BaseScanResult
    from ..utils.performance import PerformanceTracker
except ImportError:
    from core.types import Bug, Evidence
    from inspector.checks.base_scanner import BaseScanner, BaseScanResult
    from inspector.utils.performance import PerformanceTracker


class PerformanceScanResult(BaseScanResult):
    """Specialized scan result for performance analysis"""
    
    def __init__(self):
        super().__init__("Performance")
        self.performance_metrics: Dict[str, float] = {}
        self.thresholds_exceeded: List[str] = []


class PerformanceScanner(BaseScanner):
    """
    Scanner that analyzes performance metrics and generates bug reports for performance issues.
    
    Uses industry-standard thresholds based on Core Web Vitals and performance best practices
    to identify issues that negatively impact user experience.
    """
    
    # Performance thresholds based on Core Web Vitals and web performance standards
    THRESHOLDS = {
        # Core Web Vitals (Google's user experience metrics)
        'largest_contentful_paint': 2500,  # LCP should be < 2.5s
        'first_contentful_paint': 1800,    # FCP should be < 1.8s
        'cumulative_layout_shift': 0.1,    # CLS should be < 0.1
        
        # Page load performance
        'total_load_time': 3000,           # Total load should be < 3s
        'dom_content_loaded': 1500,        # DCL should be < 1.5s
        'dom_interactive': 2000,           # DOM interactive should be < 2s
        
        # Resource performance
        'slowest_resource_duration': 5000, # No single resource should take > 5s
        'average_resource_duration': 500,  # Average resource load should be < 500ms
        'total_resource_size': 3000000,    # Total resources should be < 3MB
        
        # Resource counts (too many resources can slow page)
        'resource_count': 100,             # Total resources should be < 100
        'image_count': 30,                 # Images should be < 30
        'script_count': 15,                # Scripts should be < 15
        'stylesheet_count': 10,            # Stylesheets should be < 10
        
        # Connection performance
        'dns_lookup': 200,                 # DNS lookup should be < 200ms
        'tcp_connect': 300,                # TCP connect should be < 300ms
        'ssl_handshake': 200,              # SSL handshake should be < 200ms
    }
    
    # Severity mapping based on how much threshold is exceeded
    SEVERITY_MULTIPLIERS = {
        1.5: 'medium',    # 1.5x threshold = medium
        2.0: 'high',      # 2x threshold = high  
        3.0: 'critical',  # 3x threshold = critical
    }
    
    def __init__(self, output_dir: str):
        super().__init__(output_dir)
        self.performance_tracker = PerformanceTracker()
    
    @property
    def scan_type(self) -> str:
        return "performance"
    
    @property
    def description(self) -> str:
        return "Analyzes page performance metrics and identifies performance bottlenecks"
    
    async def scan(self, page: Page, page_url: str, viewport_key: str = None) -> PerformanceScanResult:
        """
        Perform performance analysis and generate bug reports for issues found.
        
        Args:
            page: Playwright page object
            page_url: URL being scanned
            viewport_key: Optional viewport identifier (e.g., "1280x800")
            
        Returns:
            PerformanceScanResult containing performance-related bugs
        """
        result = PerformanceScanResult()
        
        try:
            # Collect performance metrics using existing PerformanceTracker
            metrics = await self.performance_tracker.collect_timings(page)
            result.performance_metrics = metrics
            
            if not metrics:
                # If no metrics collected, create a warning bug
                result.add_finding(self._create_no_metrics_bug(page_url, viewport_key))
                return result
            
            # Collect Core Web Vitals separately
            cwv_metrics = await self.performance_tracker.get_core_web_vitals(page)
            metrics.update(cwv_metrics)
            
            # Analyze each metric against thresholds
            for metric_name, threshold in self.THRESHOLDS.items():
                if metric_name in metrics:
                    metric_value = metrics[metric_name]
                    if metric_value > threshold:
                        bug = self._create_performance_bug(
                            metric_name, metric_value, threshold, page_url, viewport_key
                        )
                        result.add_finding(bug)
                        result.thresholds_exceeded.append(metric_name)
            
            # Special analysis for Core Web Vitals combinations
            self._analyze_core_web_vitals_combinations(metrics, result, page_url, viewport_key)
            
            # Analyze resource efficiency
            self._analyze_resource_efficiency(metrics, result, page_url, viewport_key)
            
        except Exception as e:
            # Create error bug if performance analysis fails
            error_bug = Bug(
                id=str(uuid.uuid4()),
                type="Performance",
                severity="medium",
                page_url=page_url,
                summary="Performance analysis failed",
                suggested_fix=f"Check page accessibility for performance monitoring. Error: {str(e)}",
                evidence=Evidence(viewport=viewport_key)
            )
            result.add_finding(error_bug)
        
        return result
    
    def _create_performance_bug(self, metric_name: str, value: float, threshold: float, 
                              page_url: str, viewport_key: str = None) -> Bug:
        """Create a performance bug based on threshold violation"""
        
        # Calculate severity based on how much threshold is exceeded
        ratio = value / threshold
        severity = "low"  # default
        
        for multiplier in sorted(self.SEVERITY_MULTIPLIERS.keys(), reverse=True):
            if ratio >= multiplier:
                severity = self.SEVERITY_MULTIPLIERS[multiplier]
                break
        
        # Generate human-readable summary and fix suggestion
        summary, fix_suggestion = self._get_metric_description(metric_name, value, threshold)
        
        # Add viewport context if provided
        if viewport_key:
            summary = f"[{viewport_key}] {summary}"
        
        return Bug(
            id=str(uuid.uuid4()),
            type="Performance",
            severity=severity,
            page_url=page_url,
            summary=summary,
            suggested_fix=fix_suggestion,
            evidence=Evidence(viewport=viewport_key),
            impact_description=self._get_impact_description(metric_name, ratio),
            business_impact=self._get_business_impact(metric_name, severity),
            technical_details=f"Measured: {value:.1f}ms, Threshold: {threshold}ms, Ratio: {ratio:.1f}x"
        )
    
    def _get_metric_description(self, metric_name: str, value: float, threshold: float) -> tuple[str, str]:
        """Get human-readable description and fix suggestion for a metric"""
        
        descriptions = {
            'largest_contentful_paint': (
                f"Largest Contentful Paint is slow ({value:.0f}ms vs {threshold}ms target)",
                "Optimize largest images/text blocks, improve server response time, use CDN"
            ),
            'first_contentful_paint': (
                f"First Contentful Paint is slow ({value:.0f}ms vs {threshold}ms target)",
                "Reduce server response time, eliminate render-blocking resources, optimize CSS"
            ),
            'cumulative_layout_shift': (
                f"Cumulative Layout Shift is high ({value:.3f} vs {threshold} target)",
                "Set dimensions on images/videos, reserve space for dynamic content, use CSS containment"
            ),
            'total_load_time': (
                f"Page load time is slow ({value:.0f}ms vs {threshold}ms target)",
                "Optimize images, minify CSS/JS, reduce HTTP requests, use browser caching"
            ),
            'dom_content_loaded': (
                f"DOM Content Loaded is slow ({value:.0f}ms vs {threshold}ms target)",
                "Reduce initial HTML size, defer non-critical CSS/JS, optimize critical path"
            ),
            'dom_interactive': (
                f"DOM Interactive time is slow ({value:.0f}ms vs {threshold}ms target)",
                "Minimize parser-blocking scripts, optimize HTML structure, reduce DOM complexity"
            ),
            'slowest_resource_duration': (
                f"Slowest resource takes too long ({value:.0f}ms vs {threshold}ms target)",
                "Identify and optimize slow resources, use compression, consider lazy loading"
            ),
            'average_resource_duration': (
                f"Average resource load time is high ({value:.0f}ms vs {threshold}ms target)",
                "Optimize all resources, use compression, enable HTTP/2, consider CDN"
            ),
            'total_resource_size': (
                f"Total resource size is large ({value/1000:.0f}KB vs {threshold/1000}KB target)",
                "Compress images, minify CSS/JS, remove unused resources, use modern formats"
            ),
            'resource_count': (
                f"Too many resources loaded ({value:.0f} vs {threshold} target)",
                "Combine CSS/JS files, use CSS sprites, reduce number of images, bundle resources"
            ),
            'image_count': (
                f"Too many images loaded ({value:.0f} vs {threshold} target)",
                "Use CSS sprites, lazy load images, combine decorative images, optimize formats"
            ),
            'script_count': (
                f"Too many script files ({value:.0f} vs {threshold} target)",
                "Bundle JavaScript files, remove unused scripts, use code splitting"
            ),
            'stylesheet_count': (
                f"Too many CSS files ({value:.0f} vs {threshold} target)",
                "Combine CSS files, inline critical CSS, remove unused styles"
            ),
            'dns_lookup': (
                f"DNS lookup is slow ({value:.0f}ms vs {threshold}ms target)",
                "Use faster DNS provider, implement DNS prefetching, reduce DNS lookups"
            ),
            'tcp_connect': (
                f"TCP connection is slow ({value:.0f}ms vs {threshold}ms target)",
                "Use keep-alive connections, implement connection pooling, use HTTP/2"
            ),
            'ssl_handshake': (
                f"SSL handshake is slow ({value:.0f}ms vs {threshold}ms target)",
                "Optimize TLS configuration, use session resumption, consider OCSP stapling"
            )
        }
        
        return descriptions.get(metric_name, (
            f"Performance metric {metric_name} exceeds threshold ({value:.1f} vs {threshold})",
            "Review and optimize this performance metric"
        ))
    
    def _get_impact_description(self, metric_name: str, ratio: float) -> str:
        """Get impact description based on metric and severity ratio"""
        
        if ratio >= 3.0:
            impact_level = "severe"
        elif ratio >= 2.0:
            impact_level = "significant"
        elif ratio >= 1.5:
            impact_level = "moderate"
        else:
            impact_level = "minor"
        
        core_vitals = ['largest_contentful_paint', 'first_contentful_paint', 'cumulative_layout_shift']
        if metric_name in core_vitals:
            return f"This {impact_level} Core Web Vitals issue directly impacts Google search rankings and user experience"
        else:
            return f"This {impact_level} performance issue may cause user frustration and increased bounce rates"
    
    def _get_business_impact(self, metric_name: str, severity: str) -> str:
        """Get business impact description based on metric and severity"""
        
        if severity == "critical":
            return "Critical performance issue likely causing significant user abandonment and revenue loss"
        elif severity == "high":
            return "High performance impact affecting user satisfaction and conversion rates"
        elif severity == "medium":
            return "Moderate performance impact that may reduce user engagement"
        else:
            return "Minor performance impact with limited user-facing effects"
    
    def _create_no_metrics_bug(self, page_url: str, viewport_key: str = None) -> Bug:
        """Create bug when no performance metrics could be collected"""
        summary = "Unable to collect performance metrics"
        if viewport_key:
            summary = f"[{viewport_key}] {summary}"
        
        return Bug(
            id=str(uuid.uuid4()),
            type="Performance",
            severity="medium",
            page_url=page_url,
            summary=summary,
            suggested_fix="Check if page supports Performance API or investigate navigation issues",
            evidence=Evidence(viewport=viewport_key),
            technical_details="Performance timing data was not available from the browser"
        )
    
    def _analyze_core_web_vitals_combinations(self, metrics: Dict[str, float], 
                                            result: PerformanceScanResult, 
                                            page_url: str, viewport_key: str = None):
        """Analyze Core Web Vitals as a group for additional insights"""
        
        lcp = metrics.get('largest_contentful_paint', 0)
        fcp = metrics.get('first_contentful_paint', 0)
        cls = metrics.get('cumulative_layout_shift', 0)
        
        # Check if all Core Web Vitals are failing
        lcp_failing = lcp > self.THRESHOLDS['largest_contentful_paint']
        fcp_failing = fcp > self.THRESHOLDS['first_contentful_paint']
        cls_failing = cls > self.THRESHOLDS['cumulative_layout_shift']
        
        failing_count = sum([lcp_failing, fcp_failing, cls_failing])
        
        if failing_count >= 2:
            summary = f"Multiple Core Web Vitals failing ({failing_count}/3)"
            if viewport_key:
                summary = f"[{viewport_key}] {summary}"
            
            severity = "critical" if failing_count == 3 else "high"
            
            bug = Bug(
                id=str(uuid.uuid4()),
                type="Performance",
                severity=severity,
                page_url=page_url,
                summary=summary,
                suggested_fix="Comprehensive performance optimization needed - review render pipeline, resource loading, and layout stability",
                evidence=Evidence(viewport=viewport_key),
                impact_description="Multiple Core Web Vitals failures severely impact SEO rankings and user experience",
                business_impact="Critical performance issues affecting search visibility and user conversion",
                technical_details=f"LCP: {lcp:.1f}ms, FCP: {fcp:.1f}ms, CLS: {cls:.3f}"
            )
            result.add_finding(bug)
    
    def _analyze_resource_efficiency(self, metrics: Dict[str, float], 
                                   result: PerformanceScanResult,
                                   page_url: str, viewport_key: str = None):
        """Analyze resource loading efficiency patterns"""
        
        resource_count = metrics.get('resource_count', 0)
        total_size = metrics.get('total_resource_size', 0)
        avg_duration = metrics.get('average_resource_duration', 0)
        
        # Check for inefficient resource loading patterns
        if resource_count > 0 and total_size > 0:
            avg_size_per_resource = total_size / resource_count
            
            # Flag if average resource size is very large (> 100KB per resource)
            if avg_size_per_resource > 100000 and resource_count > 20:
                summary = f"Inefficient resource loading pattern detected"
                if viewport_key:
                    summary = f"[{viewport_key}] {summary}"
                
                bug = Bug(
                    id=str(uuid.uuid4()),
                    type="Performance",
                    severity="medium",
                    page_url=page_url,
                    summary=summary,
                    suggested_fix="Optimize resource sizes and consider lazy loading for non-critical resources",
                    evidence=Evidence(viewport=viewport_key),
                    technical_details=f"Average resource size: {avg_size_per_resource/1000:.1f}KB, Total resources: {resource_count}",
                    impact_description="Large average resource sizes may cause slow loading on slower connections"
                )
                result.add_finding(bug)
