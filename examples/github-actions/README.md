# 🦗 Mantis GitHub Actions - Example Workflows

This directory contains ready-to-use GitHub Actions workflow examples for integrating Mantis accessibility and UI scanning into your projects.

## 📁 Available Examples

### [`basic-scan.yml`](./basic-scan.yml)
**Perfect for getting started!**
- Scans your website on every push and PR
- Simple 10-line configuration
- Automatically uploads detailed reports

### [`vercel-integration.yml`](./vercel-integration.yml)
**For Vercel users**
- Waits for Vercel deployment to complete
- Automatically scans the live preview URL
- Blocks deployments with critical issues

### [`scheduled-scan.yml`](./scheduled-scan.yml)
**For production monitoring**
- Weekly automated scans of production and staging
- Comprehensive site audits
- Different scan types per environment

## 🚀 Quick Start

1. **Copy any example** to `.github/workflows/` in your repository
2. **Update the URL** to your website
3. **Add your Cohere API key** as a repository secret named `COHERE_API_KEY`
4. **Commit and push** - Mantis will start scanning automatically!

## 📖 Complete Documentation

For detailed configuration options, advanced examples, and troubleshooting:

👉 **[Read the full GitHub Actions documentation](../docs/GITHUB_ACTIONS.md)**

## 🛠️ Need Help?

- 📖 [Main Documentation](https://github.com/ColinG03/mantis)
- 🐛 [Report Issues](https://github.com/ColinG03/mantis/issues)
- 💬 [Ask Questions](https://github.com/ColinG03/mantis/discussions)

---

**Make your website accessible with just a few lines of YAML!** 🌟
