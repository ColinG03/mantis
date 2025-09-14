# 🦗 Mantis - Web Accessibility & UI Testing Tool

**Automated accessibility and UI bug detection powered by AI**

[![PyPI version](https://badge.fury.io/py/mantis-web-crawler.svg)](https://badge.fury.io/py/mantis-web-crawler)
[![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python)](https://python.org)
[![GitHub Actions](https://img.shields.io/badge/GitHub-Actions-blue?logo=github)](https://github.com/ColinG03/mantis/tree/main/examples/github-actions)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

Mantis crawls your website and uses advanced AI analysis to detect accessibility violations, UI inconsistencies, broken functionality, and performance issues. Perfect for developers, QA teams, and accessibility professionals.

*Originally created for Hack The North 2025*

## ✨ What Makes Mantis Special

- **🤖 AI-Powered Analysis**: Uses Cohere's advanced AI for intelligent issue detection and actionable fix suggestions
- **⚡ One-Line GitHub Integration**: Add automated testing to any repository in 30 seconds
- **🔍 Comprehensive Scanning**: WCAG 2.1 accessibility, UI/Visual, Logic, and Performance testing
- **📊 Professional Reports**: Interactive HTML dashboards and machine-readable JSON output
- **🎯 Smart Crawling**: Efficiently discovers and tests your entire site structure
- **🚀 Zero Config**: Works out of the box with sensible defaults

## 🚀 Quick Start

### Option 1: GitHub Actions (Recommended)

Add automated testing to your repository in **30 seconds**:

Create `.github/workflows/mantis.yml`:

```yaml
name: Mantis Accessibility Scan

on: [push, pull_request]

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

### Option 2: Install Locally

```bash
# Install from PyPI
pip install mantis-web-crawler

# Install browser dependencies
playwright install chromium

# Set your Cohere API key
export COHERE_API_KEY="your-api-key-here"

# Run your first scan
mantis run https://example.com
```

## 📊 What Mantis Detects

| Severity | Issue Types | Examples |
|----------|------------|----------|
| 🔴 **Critical** | Accessibility violations, broken functionality | Missing alt text, keyboard navigation failures, dead links |
| 🟠 **High** | Major usability issues | Poor color contrast, broken forms, WCAG violations |
| 🟡 **Medium** | UX improvements | Responsive design issues, slow loading |
| 🔵 **Low** | Best practices | SEO optimizations, minor accessibility enhancements |

### Comprehensive Coverage
- **♿ Accessibility**: WCAG 2.1 compliance, screen reader compatibility, keyboard navigation
- **🎨 UI/Visual**: Layout issues, responsive design, visual inconsistencies
- **⚙️ Logic**: Broken links, form validation, navigation flows
- **🚀 Performance**: Page load times, optimization opportunities

## 🎯 Usage Examples

### Basic Website Scan
```bash
mantis run https://example.com
```

### Advanced Configuration
```bash
# Deep crawl with custom settings
mantis run https://example.com \
  --max-depth 3 \
  --max-pages 50 \
  --scan-type accessibility \
  --output detailed-report.json \
  --verbose

# Launch with real-time dashboard
mantis run https://example.com --dashboard
```

### Focus on Specific Issues
```bash
# Accessibility compliance only
mantis run https://example.com --scan-type accessibility

# Performance optimization
mantis run https://example.com --scan-type performance

# UI and visual issues
mantis run https://example.com --scan-type ui
```

## 🌟 GitHub Actions Examples

### Vercel Integration
Automatically scan every deployment:

```yaml
name: Scan Vercel Deployment

on:
  push:
    branches: [ main ]

jobs:
  wait-for-vercel:
    runs-on: ubuntu-latest
    outputs:
      url: ${{ steps.vercel.outputs.url }}
    steps:
      - uses: actions/checkout@v4
      - uses: patrickedqvist/wait-for-vercel-preview@v1.3.1
        id: vercel
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
          max_timeout: 600

  mantis-scan:
    needs: wait-for-vercel
    uses: ColinG03/mantis/.github/workflows/mantis-scan.yml@v1
    with:
      url: ${{ needs.wait-for-vercel.outputs.url }}
      fail_on: "high"  # Block deployments with serious issues
    secrets:
      COHERE_API_KEY: ${{ secrets.COHERE_API_KEY }}
```

### Scheduled Production Monitoring
```yaml
name: Weekly Accessibility Audit

on:
  schedule:
    - cron: '0 9 * * 1'  # Every Monday at 9 AM

jobs:
  production-audit:
    uses: ColinG03/mantis/.github/workflows/mantis-scan.yml@v1
    with:
      url: https://your-production-site.com
      max_pages: 100
      scan_type: "accessibility"
    secrets:
      COHERE_API_KEY: ${{ secrets.COHERE_API_KEY }}
```

[**See all GitHub Actions examples →**](examples/github-actions/)

## 📋 Configuration Options

### CLI Parameters
```bash
mantis run <URL> [OPTIONS]
```

| Option | Description | Default |
|--------|-------------|---------|
| `--max-depth` | Maximum crawl depth | `3` |
| `--max-pages` | Maximum pages to scan | `50` |
| `--output` | Output file path | `crawl_report.json` |
| `--scan-type` | Focus area: `all`, `accessibility`, `ui`, `interactive`, `performance` | `all` |
| `--verbose` | Detailed logging | `false` |
| `--dashboard` | Launch web dashboard | `false` |

### GitHub Actions Parameters
```yaml
with:
  url: "https://example.com"           # Required
  max_depth: 2                         # Optional
  max_pages: 25                        # Optional
  scan_type: "all"                     # Optional
  fail_on: "critical"                  # Optional: none, high, critical
  verbose: false                       # Optional
```

## 📊 Example Output

### Command Line Summary
```
🦗 CRAWL SUMMARY
════════════════════════════════════════════════════════════
🌐 Seed URL: https://example.com
📄 Pages crawled: 25
🐛 Total bugs found: 12
📅 Scanned at: 2024-01-15 10:30:45

🔍 Bug Breakdown:
  🔴 Critical: 2    🟠 High: 4
  🟡 Medium: 4      🔵 Low: 2

📋 By Type:
  ♿ Accessibility: 8    🎨 UI: 3    ⚙️ Logic: 1

🔎 Sample Issues:
  1. 🔴 [CRITICAL] Missing alt text for product images
     📍 Page: https://example.com/products
  2. 🟠 [HIGH] Insufficient color contrast in navigation
     📍 Page: https://example.com/
```

### GitHub Actions Summary
- **📋 Detailed overview** in Actions tab with issue breakdown
- **📎 Downloadable artifacts** with interactive HTML dashboard
- **🚦 Quality gates** that can block deployments with critical issues
- **📝 Automated comments** on commits with scan results

## 🔧 Advanced Features

### Real-time Dashboard
```bash
mantis run https://example.com --dashboard
```
- Live crawl progress with WebSocket updates
- Real-time issue discovery
- Interactive filtering and sorting
- Export capabilities

### AI-Powered Analysis
- **Intelligent issue detection** using Cohere's language models
- **Contextual fix suggestions** tailored to your specific issues
- **Severity assessment** based on impact and user experience
- **Actionable recommendations** with implementation guidance

### Flexible Reporting
- **JSON output** for integration with other tools
- **Interactive HTML dashboard** for human review
- **GitHub Actions summaries** for CI/CD integration
- **Screenshot evidence** for visual issues

## 🏗️ Use Cases

### Development Teams
- **Pull Request Checks**: Catch accessibility issues before code review
- **Deployment Gates**: Block releases with critical accessibility violations
- **Regression Testing**: Ensure new features don't break existing accessibility

### QA Teams
- **Automated Testing**: Comprehensive UI and accessibility coverage
- **Compliance Audits**: WCAG 2.1 compliance verification
- **Cross-Environment Testing**: Consistent results across staging and production

### Accessibility Professionals
- **Detailed Audits**: AI-powered analysis with actionable insights
- **Progress Tracking**: Monitor accessibility improvements over time
- **Team Education**: Share findings and fix suggestions with developers

### DevOps Teams
- **Pipeline Integration**: Zero-config GitHub Actions setup
- **Scalable Testing**: Efficient scanning for sites of any size
- **Automated Reporting**: Self-service accessibility insights

## 🛠️ Development & Contributing

### Setup Development Environment
```bash
# Clone the repository
git clone https://github.com/ColinG03/mantis.git
cd mantis

# Install in development mode
pip install -e ".[dev]"

# Install browser dependencies
playwright install chromium

# Run tests
pytest

# Run linting
black src/
flake8 src/
```

### Contributing
We welcome contributions! Whether it's:
- 🐛 Bug reports and fixes
- ✨ New features and scan types
- 📖 Documentation improvements
- 🧪 Test coverage
- 💡 Ideas and suggestions

[**📖 Contributing Guide →**](CONTRIBUTING.md)

## 📚 Documentation

- **[GitHub Actions Integration](docs/GITHUB_ACTIONS.md)** - Complete CI/CD setup guide
- **[API Reference](docs/API.md)** - Detailed API documentation  
- **[Configuration Guide](docs/CONFIG.md)** - Advanced configuration options
- **[Example Workflows](examples/github-actions/)** - Ready-to-use GitHub Actions examples

## 🆘 Support & Community

- **🐛 Bug Reports**: [GitHub Issues](https://github.com/ColinG03/mantis/issues)
- **💬 Questions & Discussions**: [GitHub Discussions](https://github.com/ColinG03/mantis/discussions)
- **📖 Documentation**: [GitHub Wiki](https://github.com/ColinG03/mantis/wiki)
- **📦 PyPI Package**: [mantis-web-crawler](https://pypi.org/project/mantis-web-crawler/)

## 🚀 Getting Started Checklist

- [ ] **Install Mantis**: `pip install mantis-web-crawler`
- [ ] **Get Cohere API key**: [Sign up at cohere.ai](https://cohere.ai/) (free tier available)
- [ ] **Run first scan**: `mantis run https://your-website.com`
- [ ] **Add to GitHub Actions**: Copy our basic workflow example
- [ ] **Set up secrets**: Add `COHERE_API_KEY` to your repository
- [ ] **Customize configuration**: Adjust scan settings for your needs

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **[Cohere](https://cohere.ai/)** - Advanced AI analysis capabilities
- **[Playwright](https://playwright.dev/)** - Reliable browser automation
- **[axe-core](https://github.com/dequelabs/axe-core)** - Accessibility testing engine
- **Open source community** - Thank you for making the web more accessible!

---

<div align="center">

**Ready to make your website more accessible?**

[**🚀 Install from PyPI**](#quick-start) • [**📖 GitHub Actions Guide**](docs/GITHUB_ACTIONS.md) • [**🌟 View Examples**](examples/github-actions/)

**Made with ❤️ for developers, designers, and accessibility advocates**

*Bringing automated accessibility testing to every development workflow*

Michael and Colin :)
</div>
</div>