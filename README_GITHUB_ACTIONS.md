# 🦗 Mantis - Web Accessibility & UI Testing Tool

**Automated accessibility and UI bug detection powered by AI**

Mantis crawls your website and uses advanced AI analysis to detect accessibility violations, UI inconsistencies, broken functionality, and performance issues. Perfect for developers, QA teams, and accessibility professionals.

[![GitHub Actions](https://img.shields.io/badge/GitHub-Actions-blue?logo=github)](https://github.com/ColinG03/mantis/tree/main/examples/github-actions)
[![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

## ✨ Features

- **🔍 Comprehensive Scanning**: Accessibility (WCAG 2.1), UI/Visual, Logic, and Performance testing
- **🤖 AI-Powered Analysis**: Uses Cohere's advanced AI for intelligent issue detection and fix suggestions
- **🚀 GitHub Actions Integration**: Add automated testing to your CI/CD pipeline in minutes
- **📊 Rich Reports**: Interactive HTML dashboards and machine-readable JSON output
- **🎯 Multiple Scan Types**: Focus on specific areas or run comprehensive audits
- **⚡ Fast & Efficient**: Parallel processing and smart crawling algorithms

## 🚀 Quick Start with GitHub Actions

### Add to Your Repository (30 seconds)

Create `.github/workflows/mantis.yml`:

```yaml
name: Mantis Accessibility Scan

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  accessibility-check:
    uses: ColinG03/mantis/.github/workflows/mantis-scan.yml@v1
    with:
      url: https://your-website.com
      fail_on: "critical"
    secrets:
      COHERE_API_KEY: ${{ secrets.COHERE_API_KEY }}
```

**That's it!** 🎉 Your next push will automatically scan your website.

[**📖 Complete GitHub Actions Guide →**](docs/GITHUB_ACTIONS.md)

## 🛠️ Local Installation

### Prerequisites
- Python 3.8+
- Node.js (for Playwright browser automation)

### Install
```bash
# Clone the repository
git clone https://github.com/ColinG03/mantis.git
cd mantis

# Install dependencies
pip install -e .
pip install playwright axe-playwright-python

# Install browser
python -m playwright install chromium

# Set up your Cohere API key
export COHERE_API_KEY="your-api-key-here"
```

### Run Your First Scan
```bash
# Basic scan
mantis run https://example.com

# Advanced scan with options
mantis run https://example.com \
  --max-depth 3 \
  --max-pages 50 \
  --scan-type accessibility \
  --output my-report.json \
  --verbose
```

## 📊 What Mantis Detects

### 🔴 Critical Issues
- **Accessibility**: Missing alt text, keyboard navigation failures, color contrast violations
- **Functionality**: Broken forms, dead links, JavaScript errors
- **UI**: Layout breaks, overlapping elements, missing content

### 🟠 High Severity
- **WCAG Violations**: Heading structure, focus management, ARIA usage
- **Usability**: Poor responsive design, slow loading, navigation issues
- **Performance**: Optimization opportunities, resource loading problems

### 🟡 Medium & 🔵 Low Severity
- **Best Practices**: SEO improvements, code quality, minor UX enhancements
- **Recommendations**: Performance optimizations, accessibility improvements

## 🎯 Scan Types

| Type | Focus | Use Case |
|------|-------|----------|
| `all` | Everything | Comprehensive audit |
| `accessibility` | WCAG compliance | Accessibility certification |
| `ui` | Visual issues | Design QA |
| `performance` | Speed & optimization | Performance tuning |
| `interactive` | User interactions | Functionality testing |

## 📈 Example Reports

### GitHub Actions Summary
![GitHub Summary](https://via.placeholder.com/800x400/f8f9fa/000?text=GitHub+Actions+Summary+View)

### Interactive HTML Dashboard
![HTML Report](https://via.placeholder.com/800x400/f8f9fa/000?text=Interactive+HTML+Dashboard)

### Command Line Output
```
🦗 CRAWL SUMMARY
════════════════════════════════════════════════════════════
🌐 Seed URL: https://example.com
📄 Pages crawled: 25
🐛 Total bugs found: 12
📅 Scanned at: 2024-01-15 10:30:45

🔍 Bug Breakdown:
  🔴 Critical: 2
  🟠 High: 4
  🟡 Medium: 4
  🔵 Low: 2

📋 By Type:
  ♿ Accessibility: 8
  🎨 UI: 3
  ⚙️ Logic: 1
```

## 🌟 GitHub Actions Examples

### Basic Setup
```yaml
uses: ColinG03/mantis/.github/workflows/mantis-scan.yml@v1
with:
  url: https://your-site.com
```

### Vercel Integration
```yaml
# Wait for deployment, then scan
needs: wait-for-vercel
uses: ColinG03/mantis/.github/workflows/mantis-scan.yml@v1
with:
  url: ${{ needs.wait-for-vercel.outputs.url }}
  fail_on: "high"
```

### Scheduled Monitoring
```yaml
# Weekly production scans
on:
  schedule:
    - cron: '0 9 * * 1'
uses: ColinG03/mantis/.github/workflows/mantis-scan.yml@v1
with:
  url: https://production.com
  max_pages: 100
```

[**See all examples →**](examples/github-actions/)

## 🔧 Configuration

### CLI Options
```bash
mantis run <URL> [OPTIONS]

Options:
  --max-depth INTEGER     Maximum crawl depth (default: 3)
  --max-pages INTEGER     Maximum pages to crawl (default: 50)
  --output PATH          Output file path (default: crawl_report.json)
  --scan-type TEXT       Scan type: all|accessibility|ui|interactive|performance
  --verbose              Enable detailed logging
  --dashboard            Launch web dashboard after scan
```

### GitHub Actions Options
```yaml
with:
  url: "https://example.com"           # Required
  max_depth: 2                         # Optional, default: 2
  max_pages: 25                        # Optional, default: 25
  scan_type: "all"                     # Optional, default: "all"
  fail_on: "critical"                  # Optional, default: "none"
  verbose: false                       # Optional, default: false
```

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Orchestrator  │───▶│    Inspector     │───▶│   AI Analysis   │
│   (Crawler)     │    │   (Scanners)     │    │   (Cohere)      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   URL Queue     │    │   Playwright     │    │  Bug Reports    │
│   Link Discovery│    │   Screenshots    │    │  Fix Suggestions│
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Core Components
- **🕷️ Orchestrator**: Intelligent web crawling and URL discovery
- **🔍 Inspector**: Multi-scanner architecture (accessibility, UI, performance)
- **🎭 Playwright**: Browser automation and screenshot capture
- **🤖 AI Analysis**: Cohere-powered intelligent issue detection
- **📊 Reporting**: HTML dashboards and JSON data export

## 🚀 Use Cases

### Development Teams
- **PR Checks**: Catch accessibility issues before they reach production
- **Continuous Monitoring**: Weekly scans of staging environments
- **Quality Gates**: Block deployments with critical issues

### QA Teams
- **Regression Testing**: Automated UI and accessibility testing
- **Cross-browser Testing**: Consistent results across environments
- **Compliance Audits**: WCAG 2.1 compliance verification

### Accessibility Professionals
- **Comprehensive Audits**: Detailed WCAG analysis with AI insights
- **Fix Prioritization**: Severity-based issue ranking
- **Progress Tracking**: Historical scan comparison

### DevOps Teams
- **Pipeline Integration**: Zero-config GitHub Actions setup
- **Artifact Management**: Automated report generation and storage
- **Scalable Scanning**: Efficient crawling for large sites

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** and add tests
4. **Commit your changes**: `git commit -m 'Add amazing feature'`
5. **Push to the branch**: `git push origin feature/amazing-feature`
6. **Open a Pull Request**

### Development Setup
```bash
# Clone and install
git clone https://github.com/ColinG03/mantis.git
cd mantis
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
black src/
flake8 src/
```

## 📚 Documentation

- **[GitHub Actions Integration](docs/GITHUB_ACTIONS.md)** - Complete CI/CD setup guide
- **[API Reference](docs/API.md)** - Detailed API documentation
- **[Configuration Guide](docs/CONFIG.md)** - Advanced configuration options
- **[Contributing Guide](CONTRIBUTING.md)** - How to contribute to Mantis

## 🆘 Support

- **🐛 Bug Reports**: [GitHub Issues](https://github.com/ColinG03/mantis/issues)
- **💬 Questions**: [GitHub Discussions](https://github.com/ColinG03/mantis/discussions)
- **📖 Documentation**: [GitHub Wiki](https://github.com/ColinG03/mantis/wiki)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **[Playwright](https://playwright.dev/)** - Reliable browser automation
- **[Cohere](https://cohere.ai/)** - Advanced AI analysis capabilities
- **[axe-core](https://github.com/dequelabs/axe-core)** - Accessibility testing engine
- **Community contributors** - Thank you for making Mantis better!

---

<div align="center">

**Ready to make the web more accessible?**

[**🚀 Get Started with GitHub Actions**](docs/GITHUB_ACTIONS.md) • [**📥 Install Locally**](#local-installation) • [**📖 Read the Docs**](docs/)

**Made with ❤️ by developers, for developers**

*Bringing automated accessibility testing to every development workflow*

</div>
