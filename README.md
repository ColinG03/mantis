# Mantis Web Crawler

🕷️ **Mantis** is a powerful web accessibility and UI bug detection tool that crawls websites to discover issues before they reach production.

*Originally created for Hack The North 2025*

## Features

- 🔍 **Comprehensive Web Crawling**: Deep crawl of websites with configurable depth and page limits
- ♿ **Accessibility Testing**: Automated detection of accessibility violations
- 🎨 **Visual Layout Analysis**: Detection of UI layout bugs and visual inconsistencies  
- 📊 **Real-time Dashboard**: Live monitoring of crawl progress with WebSocket updates
- 📋 **Detailed Reporting**: JSON reports with bug details, evidence, and recommendations
- 🚀 **Easy CLI Interface**: Simple command-line tool for quick scans

## Installation

### From PyPI (Recommended)

```bash
pip install mantis-web-crawler
playwright install
```

### From Source (Development)

```bash
# Clone the repository
git clone https://github.com/yourusername/mantis.git
cd mantis

# Install the package
pip install -e .

# Install Playwright browsers (required)
playwright install
```

## Quick Start

After installation, you can run Mantis directly from anywhere:

```bash
# Basic crawl
mantis run https://example.com

# Advanced options
mantis run https://example.com --max-depth 2 --max-pages 25
mantis run https://example.com --output my_report.json --verbose
mantis run https://example.com --dashboard  # Launch with live dashboard
```

## Usage Examples

### Basic Website Scan
```bash
mantis run https://example.com
```

### Deep Crawl with Custom Limits
```bash
mantis run https://example.com --max-depth 3 --max-pages 50
```

### Generate Custom Report
```bash
mantis run https://example.com --output accessibility_report.json --verbose
```

### Launch with Real-time Dashboard
```bash
mantis run https://example.com --dashboard
```

## Command Line Options

- `url`: Starting URL to crawl (required)
- `--max-depth`: Maximum crawl depth (default: 3)
- `--max-pages`: Maximum number of pages to crawl (default: 10)
- `--output`: Output file for JSON report (optional)
- `--verbose`: Enable verbose logging
- `--dashboard`: Launch real-time monitoring dashboard
- `--scan-type`: One of 'all', 'ui', 'accessibility' or 'performance'. Defaults to 'all'.

## Requirements

- Python 3.8+
- Playwright browsers (automatically installed with `playwright install`)

## Development

```bash
# Clone the repo
git clone https://github.com/yourusername/mantis.git
cd mantis

# Install in development mode
pip install -e .[dev]

# Install pre-commit hooks
pre-commit install

# Run tests
pytest
```

## Contributing

We welcome contributions! Please see our contributing guidelines for more details.

## License

MIT License - see LICENSE file for details.
