"""
Tests for the CLI interface.
"""

import pytest
import argparse
import json
import tempfile
import os
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path

from src.orchestrator.cli import MantisCLI
from src.core.types import CrawlReport, Bug, Evidence


class TestArgumentParsing:
    """Test CLI argument parsing."""
    
    def test_parse_basic_url(self):
        """Should parse basic URL argument."""
        cli = MantisCLI()
        args = cli.parse_args(["run", "https://example.com"])
        
        assert args.command == "run"
        assert args.url == "https://example.com"
    
    def test_parse_with_max_depth(self):
        """Should parse max-depth argument."""
        cli = MantisCLI()
        args = cli.parse_args(["run", "https://example.com", "--max-depth", "5"])
        
        assert args.max_depth == 5
    
    def test_parse_with_max_pages(self):
        """Should parse max-pages argument."""
        cli = MantisCLI()
        args = cli.parse_args(["run", "https://example.com", "--max-pages", "100"])
        
        assert args.max_pages == 100
    
    def test_parse_with_output_file(self):
        """Should parse output file argument."""
        cli = MantisCLI()
        args = cli.parse_args(["run", "https://example.com", "--output", "report.json"])
        
        assert args.output == "report.json"
    
    def test_parse_with_verbose(self):
        """Should parse verbose flag."""
        cli = MantisCLI()
        args = cli.parse_args(["run", "https://example.com", "--verbose"])
        
        assert args.verbose is True
    
    def test_parse_defaults(self):
        """Should use sensible defaults."""
        cli = MantisCLI()
        args = cli.parse_args(["run", "https://example.com"])
        
        assert args.max_depth == 3
        assert args.max_pages == 50
        assert args.output == "crawl_report.json"
        assert args.verbose is False
    
    def test_parse_all_options(self):
        """Should parse all options together."""
        cli = MantisCLI()
        args = cli.parse_args([
            "run", "https://example.com",
            "--max-depth", "2",
            "--max-pages", "25",
            "--output", "custom_report.json",
            "--verbose"
        ])
        
        assert args.url == "https://example.com"
        assert args.max_depth == 2
        assert args.max_pages == 25
        assert args.output == "custom_report.json"
        assert args.verbose is True


class TestArgumentValidation:
    """Test CLI argument validation."""
    
    def test_validate_valid_https_url(self):
        """Should accept valid HTTPS URLs."""
        cli = MantisCLI()
        args = argparse.Namespace(url="https://example.com")
        
        assert cli.validate_args(args) is True
    
    def test_validate_valid_http_url(self):
        """Should accept valid HTTP URLs."""
        cli = MantisCLI()
        args = argparse.Namespace(url="http://localhost:3000")
        
        assert cli.validate_args(args) is True
    
    def test_validate_invalid_url(self):
        """Should reject invalid URLs."""
        cli = MantisCLI()
        args = argparse.Namespace(url="not-a-url")
        
        assert cli.validate_args(args) is False
    
    def test_validate_positive_max_depth(self):
        """Should accept positive max_depth."""
        cli = MantisCLI()
        args = argparse.Namespace(url="https://example.com", max_depth=5)
        
        assert cli.validate_args(args) is True
    
    def test_validate_zero_max_depth(self):
        """Should reject zero max_depth."""
        cli = MantisCLI()
        args = argparse.Namespace(url="https://example.com", max_depth=0)
        
        assert cli.validate_args(args) is False
    
    def test_validate_negative_max_depth(self):
        """Should reject negative max_depth."""
        cli = MantisCLI()
        args = argparse.Namespace(url="https://example.com", max_depth=-1)
        
        assert cli.validate_args(args) is False
    
    def test_validate_positive_max_pages(self):
        """Should accept positive max_pages."""
        cli = MantisCLI()
        args = argparse.Namespace(url="https://example.com", max_pages=100)
        
        assert cli.validate_args(args) is True
    
    def test_validate_zero_max_pages(self):
        """Should reject zero max_pages."""
        cli = MantisCLI()
        args = argparse.Namespace(url="https://example.com", max_pages=0)
        
        assert cli.validate_args(args) is False


class TestCrawlExecution:
    """Test crawl execution logic."""
    
    @pytest.mark.asyncio
    async def test_run_crawl_basic(self):
        """Should execute basic crawl."""
        cli = MantisCLI()
        args = argparse.Namespace(
            url="https://example.com",
            max_depth=2,
            max_pages=10
        )
        
        # Mock inspector and crawler
        mock_report = CrawlReport(
            scanned_at="2023-01-01T00:00:00",
            seed_url="https://example.com",
            pages_total=3,
            bugs_total=1,
            findings=[
                Bug(id="bug1", type="Accessibility", severity="medium", 
                    page_url="https://example.com", summary="Test bug")
            ],
            pages=[{"url": "https://example.com", "depth": 0, "status": 200}]
        )
        
        with patch('src.orchestrator.cli.get_inspector') as mock_get_inspector, \
             patch('src.orchestrator.cli.Crawler') as mock_crawler_class:
            
            mock_inspector = Mock()
            mock_get_inspector.return_value = mock_inspector
            
            mock_crawler = Mock()
            mock_crawler.crawl_site = AsyncMock(return_value=mock_report)
            mock_crawler_class.return_value = mock_crawler
            
            report = await cli.run_crawl(args)
            
            # Verify crawler was created with correct args
            mock_crawler_class.assert_called_once_with(max_depth=2, max_pages=10)
            
            # Verify crawl was executed
            mock_crawler.crawl_site.assert_called_once()
            call_args = mock_crawler.crawl_site.call_args
            assert call_args[1]['seed_url'] == "https://example.com"
            assert call_args[1]['inspector'] == mock_inspector
            
            assert report == mock_report
    
    @pytest.mark.asyncio
    async def test_run_crawl_with_progress(self):
        """Should execute crawl with progress callback."""
        cli = MantisCLI()
        args = argparse.Namespace(
            url="https://example.com",
            max_depth=1,
            max_pages=5
        )
        
        mock_report = CrawlReport(
            scanned_at="2023-01-01T00:00:00",
            seed_url="https://example.com", 
            pages_total=1,
            bugs_total=0,
            findings=[],
            pages=[]
        )
        
        with patch('src.orchestrator.cli.get_inspector') as mock_get_inspector, \
             patch('src.orchestrator.cli.Crawler') as mock_crawler_class:
            
            mock_inspector = Mock()
            mock_get_inspector.return_value = mock_inspector
            
            mock_crawler = Mock()
            mock_crawler.crawl_site = AsyncMock(return_value=mock_report)
            mock_crawler_class.return_value = mock_crawler
            
            await cli.run_crawl(args)
            
            # Verify progress callback was passed
            call_args = mock_crawler.crawl_site.call_args
            progress_callback = call_args[1]['progress_callback']
            assert progress_callback is not None
            
            # Test that progress callback works
            progress_callback("https://example.com", 1, 1)  # Should not raise


class TestReportSaving:
    """Test report saving functionality."""
    
    def test_save_report_to_file(self):
        """Should save report to JSON file."""
        cli = MantisCLI()
        
        report = CrawlReport(
            scanned_at="2023-01-01T00:00:00",
            seed_url="https://example.com",
            pages_total=1,
            bugs_total=0,
            findings=[],
            pages=[{"url": "https://example.com", "depth": 0, "status": 200}]
        )
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_file = f.name
        
        try:
            cli.save_report(report, temp_file)
            
            # Verify file was created and contains valid JSON
            assert os.path.exists(temp_file)
            
            with open(temp_file, 'r') as f:
                saved_data = json.load(f)
            
            assert saved_data['seed_url'] == "https://example.com"
            assert saved_data['pages_total'] == 1
            assert saved_data['bugs_total'] == 0
            
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_save_report_creates_directory(self):
        """Should create output directory if it doesn't exist."""
        cli = MantisCLI()
        
        report = CrawlReport(
            scanned_at="2023-01-01T00:00:00",
            seed_url="https://example.com",
            pages_total=1,
            bugs_total=0,
            findings=[],
            pages=[]
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "subdir", "report.json")
            
            cli.save_report(report, output_path)
            
            assert os.path.exists(output_path)


class TestSummaryOutput:
    """Test console summary output."""
    
    def test_print_summary_basic(self, capsys):
        """Should print basic summary to console."""
        cli = MantisCLI()
        
        report = CrawlReport(
            scanned_at="2023-01-01T00:00:00",
            seed_url="https://example.com",
            pages_total=3,
            bugs_total=2,
            findings=[
                Bug(id="bug1", type="Accessibility", severity="high",
                    page_url="https://example.com", summary="Missing alt text"),
                Bug(id="bug2", type="UI", severity="medium", 
                    page_url="https://example.com/about", summary="Button overlap")
            ],
            pages=[
                {"url": "https://example.com", "depth": 0, "status": 200},
                {"url": "https://example.com/about", "depth": 1, "status": 200},
                {"url": "https://example.com/contact", "depth": 1, "status": 404}
            ]
        )
        
        cli.print_summary(report)
        
        captured = capsys.readouterr()
        assert "3 pages" in captured.out
        assert "2 bugs" in captured.out
        assert "https://example.com" in captured.out
        assert "Missing alt text" in captured.out
        assert "Button overlap" in captured.out
    
    def test_print_summary_no_bugs(self, capsys):
        """Should handle reports with no bugs."""
        cli = MantisCLI()
        
        report = CrawlReport(
            scanned_at="2023-01-01T00:00:00",
            seed_url="https://example.com",
            pages_total=1,
            bugs_total=0,
            findings=[],
            pages=[{"url": "https://example.com", "depth": 0, "status": 200}]
        )
        
        cli.print_summary(report)
        
        captured = capsys.readouterr()
        assert "0 bugs" in captured.out or "No bugs" in captured.out


class TestProgressDisplay:
    """Test progress display functionality."""
    
    def test_progress_callback_display(self, capsys):
        """Should display progress updates."""
        cli = MantisCLI()
        
        cli.progress_callback("https://example.com", 1, 3)
        cli.progress_callback("https://example.com/about", 2, 3)
        cli.progress_callback("https://example.com/contact", 3, 3)
        
        captured = capsys.readouterr()
        assert "1/3" in captured.out or "1 of 3" in captured.out
        assert "2/3" in captured.out or "2 of 3" in captured.out
        assert "3/3" in captured.out or "3 of 3" in captured.out
        assert "example.com" in captured.out