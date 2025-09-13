"""
Command line interface for Mantis web crawler.
"""

import argparse
import asyncio
import json
import sys
import logging
from pathlib import Path
from typing import Optional

from core.types import CrawlReport
from inspector import get_inspector
from inspector.checks.base_scanner import ScanConfig
from orchestrator.crawler import Crawler


class MantisCLI:
    """Command line interface for Mantis crawler."""
    
    def __init__(self):
        self.parser = self._create_parser()
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create the argument parser."""
        parser = argparse.ArgumentParser(
            prog='mantis',
            description='Mantis - Web accessibility and UI bug detection tool',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  mantis run https://example.com
  mantis run https://example.com --max-depth 2 --max-pages 25
  mantis run https://example.com --output my_report.json --verbose
            """
        )
        
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        
        # Run command
        run_parser = subparsers.add_parser('run', help='Run crawl on a website')
        run_parser.add_argument('url', help='Starting URL to crawl')
        run_parser.add_argument(
            '--max-depth', 
            type=int, 
            default=3,
            help='Maximum crawl depth (default: 3)'
        )
        run_parser.add_argument(
            '--max-pages',
            type=int,
            default=50, 
            help='Maximum pages to crawl (default: 50)'
        )
        run_parser.add_argument(
            '--output', '-o',
            default='crawl_report.json',
            help='Output file for report (default: crawl_report.json)'
        )
        run_parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='Enable verbose logging'
        )
        run_parser.add_argument(
            '--dashboard', '-d',
            action='store_true',
            help='Launch dashboard after crawl completes'
        )
        run_parser.add_argument(
            '--scan-type',
            choices=['all', 'accessibility', 'ui', 'interactive', 'performance'],
            default='all',
            help='Type of scan to perform (default: all)'
        )
        run_parser.add_argument(
            '--model',
            choices=['cohere', 'gemini'],
            default='cohere',
            help='AI model to use for screenshot analysis (default: cohere)'
        )
        
        return parser
    
    def parse_args(self, args: Optional[list] = None) -> argparse.Namespace:
        """Parse command line arguments."""
        return self.parser.parse_args(args)
    
    def validate_args(self, args: argparse.Namespace) -> bool:
        """Validate parsed arguments."""
        # Validate URL
        if not hasattr(args, 'url'):
            return True  # No URL to validate
            
        url = args.url.lower()
        if not (url.startswith('http://') or url.startswith('https://')):
            print(f"Error: Invalid URL '{args.url}'. Must start with http:// or https://")
            return False
        
        # Validate max_depth
        if hasattr(args, 'max_depth') and args.max_depth <= 0:
            print(f"Error: max-depth must be positive, got {args.max_depth}")
            return False
            
        # Validate max_pages  
        if hasattr(args, 'max_pages') and args.max_pages <= 0:
            print(f"Error: max-pages must be positive, got {args.max_pages}")
            return False
            
        return True
    
    def _create_scan_config(self, scan_type: str, model: str = 'cohere') -> ScanConfig:
        """Create scan configuration based on CLI argument."""
        if scan_type == 'accessibility':
            return ScanConfig.accessibility_only(model=model)
        elif scan_type == 'ui':
            return ScanConfig.ui_only(model=model)
        elif scan_type == 'interactive':
            return ScanConfig(accessibility=False, ui_visual=False, performance=False, interactive=True, model=model)
        elif scan_type == 'performance':
            return ScanConfig(accessibility=False, ui_visual=False, performance=True, interactive=False, model=model)
        else:  # 'all' or any other value
            return ScanConfig.all_scans(model=model)
    
    async def run_crawl(self, args: argparse.Namespace):
        """Execute the crawl with given arguments."""
        print(f"🔍 Starting crawl of {args.url}")
        print(f"📊 Configuration: max_depth={args.max_depth}, max_pages={args.max_pages}")
        print(f"🔬 Scan type: {args.scan_type}")
        print(f"🤖 AI Model: {args.model}")
        
        # Create scan configuration based on CLI argument
        scan_config = self._create_scan_config(args.scan_type, args.model)
        
        # Get inspector instance with scan configuration
        inspector = await get_inspector(scan_config=scan_config)
        
        # Create crawler
        crawler = Crawler(
            max_depth=args.max_depth,
            max_pages=args.max_pages
        )
        
        try:
            # Run crawl with progress callback only
            report = await crawler.crawl_site(
                seed_url=args.url,
                inspector=inspector,
                progress_callback=self.progress_callback
            )
            
            return report, inspector.output_dir, inspector
            
        except Exception as e:
            # Clean up inspector on error
            await inspector.close()
            raise
    
    
    def setup_logging(self, verbose: bool = False) -> None:
        """Setup logging configuration."""
        level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    def save_report(self, report: CrawlReport, output_path: str) -> None:
        """Save crawl report to JSON file."""
        # Create output directory if it doesn't exist
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Convert report to dict for JSON serialization
        report_dict = {
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
                    'reproduction_steps': bug.reproduction_steps,
                    'fix_steps': bug.fix_steps,
                    'affected_elements': bug.affected_elements,
                    'impact_description': bug.impact_description,
                    'wcag_guidelines': bug.wcag_guidelines,
                    'business_impact': bug.business_impact,
                    'technical_details': bug.technical_details,
                    'priority': bug.priority,
                    'category': bug.category,
                    'estimated_effort': bug.estimated_effort,
                    'tags': bug.tags
                }
                for bug in report.findings
            ],
            'pages': report.pages
        }
        
        # Save to file
        with open(output_path, 'w') as f:
            json.dump(report_dict, f, indent=2)
        
        print(f"💾 Report saved to {output_path}")
    
    def print_summary(self, report: CrawlReport) -> None:
        """Print crawl summary to console."""
        print(f"\n{'='*60}")
        print(f"🎯 CRAWL SUMMARY")
        print(f"{'='*60}")
        print(f"🌐 Seed URL: {report.seed_url}")
        print(f"📄 Pages crawled: {report.pages_total}")
        print(f"🐛 Total bugs found: {report.bugs_total}")
        print(f"📅 Scanned at: {report.scanned_at}")
        
        if report.bugs_total == 0:
            print(f"✅ No bugs found! Your site looks good.")
        else:
            print(f"\n🔍 Bug Breakdown:")
            
            # Group bugs by severity
            severity_counts = {}
            type_counts = {}
            
            for bug in report.findings:
                severity_counts[bug.severity] = severity_counts.get(bug.severity, 0) + 1
                type_counts[bug.type] = type_counts.get(bug.type, 0) + 1
            
            for severity, count in severity_counts.items():
                emoji = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🔵'}.get(severity, '⚪')
                print(f"  {emoji} {severity.capitalize()}: {count}")
            
            print(f"\n📋 By Type:")
            for bug_type, count in type_counts.items():
                emoji = {'Accessibility': '♿', 'UI': '🎨', 'Logic': '⚙️'}.get(bug_type, '🐛')
                print(f"  {emoji} {bug_type}: {count}")
            
            # Show sample bugs
            print(f"\n🔎 Sample Issues:")
            for i, bug in enumerate(report.findings[:5]):  # Show first 5
                severity_emoji = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🔵'}.get(bug.severity, '⚪')
                print(f"  {i+1}. {severity_emoji} [{bug.severity.upper()}] {bug.summary}")
                print(f"     📍 Page: {bug.page_url}")
            
            if len(report.findings) > 5:
                print(f"  ... and {len(report.findings) - 5} more issues")
        
        print(f"\n📊 Page Status:")
        print(f"Report statuses: {[page.get('status') for page in report.pages]}")
        success_count = sum(1 for page in report.pages if page.get('status') and isinstance(page['status'], int) and page['status'] < 400)
        failed_count = len(report.pages) - success_count
        
        if success_count > 0:
            print(f"  ✅ Successful: {success_count}")
        if failed_count > 0:
            print(f"  ❌ Failed: {failed_count}")
        
        print(f"{'='*60}")
    
    def progress_callback(self, url: str, current: int, total: int) -> None:
        """Progress callback for real-time updates."""
        # Create a simple progress bar
        percent = (current / total * 100) if total > 0 else 0
        bar_length = 30
        filled_length = int(bar_length * current // total) if total > 0 else 0
        bar = '█' * filled_length + '-' * (bar_length - filled_length)
        
        # Truncate URL if too long
        display_url = url if len(url) <= 50 else url[:47] + "..."
        
        print(f"\r🔄 [{bar}] {current}/{total} ({percent:.0f}%) - {display_url}", end='', flush=True)
        
        # Print newline when done
        if current == total:
            print()
    
    def launch_dashboard(self, report: CrawlReport, output_dir: Optional[str] = None) -> None:
        """Launch the dashboard with the crawl report."""
        try:
            from dashboard.server import DashboardServer
            
            print(f"\n🌐 Launching dashboard at http://localhost:8080...")
            dashboard = DashboardServer(port=8080, output_dir=output_dir)
            dashboard.load_report(report)
            
            print(f"💡 Dashboard will open automatically in your browser")
            print(f"🛑 Press Ctrl+C to stop the dashboard")
            
            # Start dashboard (blocking)
            dashboard.start_server(open_browser=True, blocking=True)
            
        except ImportError:
            print(f"❌ Dashboard not available - Flask not installed")
        except Exception as e:
            print(f"❌ Error launching dashboard: {e}")


async def main():
    """Main CLI entry point."""
    cli = MantisCLI()
    
    try:
        # Parse arguments
        args = cli.parse_args()
        
        # Handle no command
        if not args.command:
            cli.parser.print_help()
            return
        
        # Validate arguments
        if not cli.validate_args(args):
            sys.exit(1)
        
        # Setup logging
        cli.setup_logging(getattr(args, 'verbose', False))
        
        # Execute command
        if args.command == 'run':
            # Run crawl
            report, output_dir, inspector = await cli.run_crawl(args)
            
            # Save report
            cli.save_report(report, args.output)
            
            # Print summary
            cli.print_summary(report)
            
            # Handle dashboard
            if getattr(args, 'dashboard', False):
                # Launch static dashboard with completed report
                # Don't clean up inspector yet - dashboard needs the screenshot files
                cli.launch_dashboard(report, output_dir)
                # Clean up inspector after dashboard closes
                await inspector.close()
            else:
                # No dashboard - clean up inspector immediately
                await inspector.close()
                # Exit with error code if bugs found (for CI/CD)
                if report.bugs_total > 0:
                    sys.exit(1)
        
    except KeyboardInterrupt:
        print(f"\n⚠️  Crawl interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


def cli_main():
    """Synchronous entry point for console script."""
    asyncio.run(main())


if __name__ == "__main__":
    cli_main()