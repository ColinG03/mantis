"""
Dashboard web server for viewing crawl reports.
"""

import json
import os
import webbrowser
from pathlib import Path
from typing import Optional, Dict, Any
from flask import Flask, render_template, jsonify, send_from_directory
import threading
import time

from core.types import CrawlReport


class DashboardServer:
    """Web server for displaying crawl reports at localhost:8080."""
    
    def __init__(self, port: int = 8080, output_dir: Optional[str] = None):
        self.port = port
        self.output_dir = output_dir
        self.app = Flask(__name__, 
                        template_folder=str(Path(__file__).parent / 'templates'),
                        static_folder=str(Path(__file__).parent / 'static'))
        self.app.config['SECRET_KEY'] = 'mantis-dashboard-secret'
        
        
        self.current_report: Optional[CrawlReport] = None
        self.report_data: Optional[Dict[str, Any]] = None
        
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup Flask routes."""
        @self.app.route('/')
        def dashboard():
            """Main dashboard page - always show dashboard template."""
            # Always use dashboard template with empty data if no report
            if not self.current_report:
                empty_report = self._create_empty_report()
                empty_stats = self._create_empty_stats()
                return render_template('dashboard.html', 
                                     report=empty_report,
                                     stats=empty_stats)
            
            return render_template('dashboard.html', 
                                 report=self.current_report,
                                 stats=self.get_summary_stats())
        
        @self.app.route('/api/report')
        def api_report():
            """API endpoint for full report data."""
            if not self.report_data:
                return jsonify({'error': 'No report loaded'}), 404
            return jsonify(self.report_data)
        
        @self.app.route('/api/stats')
        def api_stats():
            """API endpoint for summary statistics."""
            return jsonify(self.get_summary_stats())
        
        @self.app.route('/api/bugs/severity')
        def api_bugs_by_severity():
            """API endpoint for bugs grouped by severity."""
            return jsonify(self.get_bugs_by_severity())
        
        @self.app.route('/api/bugs/type')
        def api_bugs_by_type():
            """API endpoint for bugs grouped by type."""
            return jsonify(self.get_bugs_by_type())
        
        @self.app.route('/api/bugs/page')
        def api_bugs_by_page():
            """API endpoint for bugs grouped by page."""
            return jsonify(self.get_bugs_by_page())
        
        @self.app.route('/screenshots/<path:filename>')
        def serve_screenshot(filename):
            """Serve screenshot files from the output directory."""
            if not self.output_dir:
                return "Screenshots not available", 404
            
            screenshots_dir = os.path.join(self.output_dir, 'screenshots')
            if not os.path.exists(screenshots_dir):
                return "Screenshots directory not found", 404
            
            return send_from_directory(screenshots_dir, filename)
        
    
    def load_report(self, report: CrawlReport) -> None:
        """Load a crawl report for display."""
        self.current_report = report
        
        # Convert to dict for JSON serialization
        self.report_data = {
            'scanned_at': report.scanned_at,
            'seed_url': report.seed_url,
            'pages_total': report.pages_total,
            'bugs_total': report.bugs_total,
            'findings': [
                {
                    'id': bug.id,
                    'type': bug.type,
                    'severity': bug.severity,
                    'page_url': bug.page_url,
                    'summary': bug.summary,
                    'suggested_fix': bug.suggested_fix,
                    'evidence': {
                        'screenshot_path': bug.evidence.screenshot_path,
                        'console_log': bug.evidence.console_log,
                        'wcag': bug.evidence.wcag,
                        'viewport': bug.evidence.viewport
                    },
                    'reproduction_steps': getattr(bug, 'reproduction_steps', []),
                    'fix_steps': getattr(bug, 'fix_steps', []),
                    'affected_elements': getattr(bug, 'affected_elements', []),
                    'impact_description': getattr(bug, 'impact_description', None),
                    'wcag_guidelines': getattr(bug, 'wcag_guidelines', []),
                    'business_impact': getattr(bug, 'business_impact', None),
                    'technical_details': getattr(bug, 'technical_details', None),
                    'priority': getattr(bug, 'priority', None),
                    'category': getattr(bug, 'category', None),
                    'estimated_effort': getattr(bug, 'estimated_effort', None),
                    'tags': getattr(bug, 'tags', [])
                }
                for bug in report.findings
            ],
            'pages': report.pages
        }
    
    def load_report_from_file(self, report_path: str) -> None:
        """Load a crawl report from JSON file."""
        with open(report_path, 'r') as f:
            self.report_data = json.load(f)
        
        # Create a minimal CrawlReport object for template compatibility
        # Note: This is a simplified version since we're loading from JSON
        class MockReport:
            def __init__(self, data):
                self.scanned_at = data['scanned_at']
                self.seed_url = data['seed_url']
                self.pages_total = data['pages_total']
                self.bugs_total = data['bugs_total']
                self.findings = data['findings']
                self.pages = data['pages']
        
        self.current_report = MockReport(self.report_data)
    
    def start_server(self, open_browser: bool = True, blocking: bool = True) -> None:
        """Start the dashboard server."""
        if open_browser:
            # Open browser after a short delay
            def open_browser_delayed():
                time.sleep(1)  # Give server time to start
                webbrowser.open(f'http://localhost:{self.port}')
            
            threading.Thread(target=open_browser_delayed, daemon=True).start()
        
        print(f"🌐 Dashboard starting at http://localhost:{self.port}")
        
        if blocking:
            self.app.run(host='0.0.0.0', port=self.port, debug=False)
        else:
            # Run in background thread
            self.server_thread = threading.Thread(
                target=lambda: self.app.run(host='0.0.0.0', port=self.port, debug=False),
                daemon=True
            )
            self.server_thread.start()
    
    def stop_server(self) -> None:
        """Stop the dashboard server."""
        # TODO: Implement server shutdown
        pass
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics for the dashboard."""
        if not self.current_report:
            return {}
        
        return {
            'total_pages': self.current_report.pages_total,
            'total_bugs': self.current_report.bugs_total,
            'seed_url': self.current_report.seed_url,
            'scanned_at': self.current_report.scanned_at,
            'bugs_by_severity': self.get_bugs_by_severity(),
            'bugs_by_type': self.get_bugs_by_type(),
            'success_rate': self._calculate_success_rate()
        }
    
    def get_bugs_by_severity(self) -> Dict[str, int]:
        """Get bug counts grouped by severity."""
        if not self.current_report:
            return {}
        
        severity_counts = {}
        for bug in self.current_report.findings:
            severity = bug['severity'] if isinstance(bug, dict) else bug.severity
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        return severity_counts
    
    def get_bugs_by_type(self) -> Dict[str, int]:
        """Get bug counts grouped by type."""
        if not self.current_report:
            return {}
        
        type_counts = {}
        for bug in self.current_report.findings:
            bug_type = bug['type'] if isinstance(bug, dict) else bug.type
            type_counts[bug_type] = type_counts.get(bug_type, 0) + 1
        
        return type_counts
    
    def get_bugs_by_page(self) -> Dict[str, int]:
        """Get bug counts grouped by page."""
        if not self.current_report:
            return {}
        
        page_counts = {}
        for bug in self.current_report.findings:
            page_url = bug['page_url'] if isinstance(bug, dict) else bug.page_url
            page_counts[page_url] = page_counts.get(page_url, 0) + 1
        
        return page_counts
    
    def _calculate_success_rate(self) -> float:
        """Calculate the percentage of successfully crawled pages."""
        if not self.current_report or not self.current_report.pages:
            return 0.0
        
        successful_pages = sum(1 for page in self.current_report.pages 
                             if page.get('status') and page['status'] < 400)
        
        return (successful_pages / len(self.current_report.pages)) * 100
    
    def _create_empty_report(self):
        """Create an empty report structure for initial dashboard display."""
        from datetime import datetime
        
        # Create simple object with required attributes
        class EmptyReport:
            def __init__(self):
                self.scanned_at = datetime.now().isoformat()
                self.seed_url = "Waiting for crawl to start..."
                self.pages_total = 0
                self.bugs_total = 0
                self.findings = []
                self.pages = []
        
        return EmptyReport()
    
    def _create_empty_stats(self):
        """Create empty stats for initial dashboard display."""
        return {
            'total_pages': 0,
            'total_bugs': 0,
            'seed_url': 'Waiting for crawl to start...',
            'scanned_at': 'Waiting to start...',
            'bugs_by_severity': {},  # Empty dict for severity counts
            'bugs_by_type': {},      # Empty dict for type counts  
            'success_rate': 0
        }
    