# 🦗 Mantis GitHub Actions Integration

Automatically scan your websites for accessibility and UI issues on every deployment with Mantis GitHub Actions.

## 🚀 Quick Start

### 1. Add Mantis to Your Repository

Create `.github/workflows/mantis.yml` in your repository:

```yaml
name: Mantis Accessibility & UI Scan

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
  workflow_dispatch:

jobs:
  accessibility-check:
    uses: ColinG03/mantis/.github/workflows/mantis-scan.yml@v1
    with:
      url: https://your-website.com  # Change this to your URL
      max_pages: 25
      fail_on: "critical"
    secrets:
      COHERE_API_KEY: ${{ secrets.COHERE_API_KEY }}
```

### 2. Add Your Cohere API Key

1. Go to your repository **Settings** → **Secrets and variables** → **Actions**
2. Click **"New repository secret"**
3. **Name:** `COHERE_API_KEY`
4. **Value:** Your [Cohere API key](https://cohere.ai/) (get one free at cohere.ai)
5. Click **"Add secret"**

### 3. Done! 🎉

Your next push will automatically:
- Scan your website for accessibility issues
- Generate detailed HTML and JSON reports
- Show results in the GitHub Actions summary
- Optionally fail CI if critical issues are found

## 📊 What You Get

### Comprehensive Scanning
- **♿ Accessibility**: WCAG 2.1 compliance, screen reader compatibility, keyboard navigation
- **🎨 UI/Visual**: Layout issues, responsive design problems, visual inconsistencies
- **⚙️ Logic**: Broken links, form validation, navigation flows
- **🚀 Performance**: Page load times, optimization recommendations

### Rich Reports
- **📋 GitHub Summary**: Quick overview with issue counts and severity breakdown
- **📄 JSON Report**: Machine-readable data for further analysis
- **🌐 Interactive HTML Dashboard**: Beautiful, detailed report with screenshots and fix suggestions
- **📎 Artifacts**: All reports automatically uploaded and available for 30 days

### Quality Gates
Automatically prevent deployments with critical issues:
```yaml
fail_on: "critical"  # Block deploys if critical accessibility issues found
fail_on: "high"      # Block on critical OR high severity issues
fail_on: "none"      # Never block (just report)
```

## ⚙️ Configuration Options

| Parameter | Description | Default | Options |
|-----------|-------------|---------|---------|
| `url` | Website URL to scan | *Required* | Any valid HTTP/HTTPS URL |
| `max_depth` | How deep to crawl your site | `2` | 1-5 (higher = more pages) |
| `max_pages` | Maximum pages to scan | `25` | 1-500 |
| `scan_type` | What to scan for | `"all"` | `all`, `accessibility`, `ui`, `interactive`, `performance` |
| `fail_on` | When to fail the workflow | `"none"` | `none`, `high`, `critical` |
| `verbose` | Detailed logging | `false` | `true`, `false` |

## 🌟 Advanced Examples

### Vercel Integration
Automatically scan every Vercel deployment:

```yaml
name: Scan Vercel Deployment

on:
  push:
    branches: [ main, develop ]

jobs:
  wait-for-vercel:
    runs-on: ubuntu-latest
    outputs:
      url: ${{ steps.vercel.outputs.url }}
    steps:
      - uses: actions/checkout@v4
      - name: Wait for Vercel deployment
        uses: patrickedqvist/wait-for-vercel-preview@v1.3.1
        id: vercel
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
          max_timeout: 600

  mantis-scan:
    needs: wait-for-vercel
    if: needs.wait-for-vercel.outputs.url != ''
    uses: ColinG03/mantis/.github/workflows/mantis-scan.yml@v1
    with:
      url: ${{ needs.wait-for-vercel.outputs.url }}
      max_depth: 3
      max_pages: 50
      fail_on: "high"  # Block bad deployments
    secrets:
      COHERE_API_KEY: ${{ secrets.COHERE_API_KEY }}
```

### Scheduled Production Monitoring
Monitor your live site weekly:

```yaml
name: Weekly Accessibility Audit

on:
  schedule:
    - cron: '0 9 * * 1'  # Every Monday at 9 AM UTC
  workflow_dispatch:  # Manual trigger

jobs:
  production-audit:
    uses: ColinG03/mantis/.github/workflows/mantis-scan.yml@v1
    with:
      url: https://your-production-site.com
      max_pages: 100
      max_depth: 3
      scan_type: "accessibility"  # Focus on accessibility compliance
      verbose: true
    secrets:
      COHERE_API_KEY: ${{ secrets.COHERE_API_KEY }}
```

### Multi-Environment Testing
Test multiple environments in parallel:

```yaml
name: Multi-Environment Accessibility Check

on:
  workflow_dispatch:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM UTC

jobs:
  production-scan:
    uses: ColinG03/mantis/.github/workflows/mantis-scan.yml@v1
    with:
      url: https://production.example.com
      max_pages: 50
      fail_on: "critical"
    secrets:
      COHERE_API_KEY: ${{ secrets.COHERE_API_KEY }}

  staging-scan:
    uses: ColinG03/mantis/.github/workflows/mantis-scan.yml@v1
    with:
      url: https://staging.example.com
      max_pages: 30
      scan_type: "all"
      fail_on: "high"
    secrets:
      COHERE_API_KEY: ${{ secrets.COHERE_API_KEY }}

  dev-scan:
    uses: ColinG03/mantis/.github/workflows/mantis-scan.yml@v1
    with:
      url: https://dev.example.com
      max_pages: 20
      scan_type: "accessibility"
      fail_on: "none"  # Don't block dev environment
    secrets:
      COHERE_API_KEY: ${{ secrets.COHERE_API_KEY }}
```

### Focus on Specific Issues
Target specific types of problems:

```yaml
jobs:
  accessibility-only:
    uses: ColinG03/mantis/.github/workflows/mantis-scan.yml@v1
    with:
      url: https://your-site.com
      scan_type: "accessibility"  # WCAG compliance only
      fail_on: "high"
    secrets:
      COHERE_API_KEY: ${{ secrets.COHERE_API_KEY }}

  performance-check:
    uses: ColinG03/mantis/.github/workflows/mantis-scan.yml@v1
    with:
      url: https://your-site.com
      scan_type: "performance"  # Speed and optimization only
      max_pages: 10  # Performance scans are slower
    secrets:
      COHERE_API_KEY: ${{ secrets.COHERE_API_KEY }}
```

## 🔍 Understanding Results

### Severity Levels
- **🔴 Critical**: Severe accessibility violations, complete functionality failures
- **🟠 High**: Significant usability issues, major accessibility barriers
- **🟡 Medium**: Moderate issues that affect some users
- **🔵 Low**: Minor improvements, best practice recommendations

### Issue Types
- **Accessibility**: WCAG violations, screen reader issues, keyboard navigation problems
- **UI**: Visual bugs, responsive design issues, layout problems
- **Logic**: Broken links, form errors, navigation failures
- **Performance**: Slow loading, optimization opportunities

### Reports Location
After each scan, download the artifacts:
1. Go to your workflow run in GitHub Actions
2. Scroll to the bottom to find "Artifacts"
3. Download `mantis-scan-report-{run-number}`
4. Extract and open `mantis_report.html` for the interactive dashboard

## 🛠️ Troubleshooting

### Common Issues

**"COHERE_API_KEY not found"**
- Make sure you've added the secret to your repository settings
- Check that the secret name is exactly `COHERE_API_KEY`

**"Website not accessible"**
- Ensure your URL is publicly accessible (not behind authentication)
- Check that the URL is correct and returns HTTP 200

**"Workflow fails immediately"**
- Check that you're using the latest version: `@v1`
- Verify your YAML syntax is correct

**"No issues found but I expected some"**
- Try increasing `max_pages` and `max_depth`
- Check that your website is accessible to the scanner
- Use `verbose: true` for detailed logging

### Getting Help

- 📖 [Mantis Documentation](https://github.com/ColinG03/mantis)
- 🐛 [Report Issues](https://github.com/ColinG03/mantis/issues)
- 💬 [Discussions](https://github.com/ColinG03/mantis/discussions)

## 🎯 Best Practices

### For Development Teams
```yaml
# Run on every PR to catch issues early
on:
  pull_request:
    branches: [ main ]
with:
  fail_on: "critical"  # Block PRs with critical issues
```

### For Production Monitoring
```yaml
# Regular production checks
on:
  schedule:
    - cron: '0 9 * * 1'  # Weekly Monday morning
with:
  max_pages: 100  # Comprehensive scan
  fail_on: "none"  # Don't fail, just report
```

### For CI/CD Pipelines
```yaml
# Block bad deployments
with:
  fail_on: "high"
  max_pages: 50
  scan_type: "accessibility"  # Focus on compliance
```

## 📈 Performance Tips

- **Start small**: Begin with `max_pages: 10` to test, then increase
- **Use focused scans**: `scan_type: "accessibility"` is faster than `"all"`
- **Cache results**: Mantis automatically handles caching for faster subsequent runs
- **Parallel environments**: Run multiple environment scans in parallel jobs

## 🔐 Security & Privacy

- Your Cohere API key is securely stored in GitHub Secrets
- Mantis only accesses publicly available pages
- No data is stored or transmitted outside of GitHub and Cohere
- All artifacts are automatically deleted after 30 days

---

**Ready to make your website more accessible?** Add Mantis to your repository today and catch accessibility issues before they reach your users! 🚀
