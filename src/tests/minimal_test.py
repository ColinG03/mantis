#!/usr/bin/env python3
"""
Minimal test script for the Mantis Inspector.

Just tests navigation and screenshot capture as the orchestrator would use it.

Usage:
    python minimal_test.py
"""

import asyncio
import sys
import os

# Add the project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

from inspector.main import get_inspector


async def minimal_test():
    """
    Minimal test: navigate to URL and capture screenshot.
    This is exactly how the orchestrator would use the inspector.
    """
    url = "https://www.compile-news.com/home"
    
    print(f"🔍 Testing inspector with {url}")
    
    # Get inspector with testing mode enabled (saves to permanent location)
    inspector = await get_inspector(testing_mode=True)
    
    try:
        # This is the core orchestrator call
        result = await inspector.inspect_page(url)
        
        # Simple results
        print(f"✅ Status: {result.status}")
        print(f"📸 Screenshots: {len(result.viewport_artifacts)}")
        print(f"🔗 Links: {len(result.outlinks)}")
        print(f"🐛 Issues: {len(result.findings)}")
        if result.findings:
            print(f"\n🐛 Issues found:")
            for i, bug in enumerate(result.findings[:5], 1):
                print(f"  {i}. [{bug.severity.upper()}] {bug.type}: {bug.summary}")
                if bug.evidence.screenshot_path:
                    print(f"     📸 Screenshot: {os.path.basename(bug.evidence.screenshot_path)}")
                if bug.evidence.console_log:
                    log_preview = bug.evidence.console_log.split('\n')[0][:100]
                    print(f"     📝 Console: {log_preview}...")
            if len(result.findings) > 5:
                print(f"  ... and {len(result.findings) - 5} more issues")
        # Show screenshot paths
        for i, screenshot in enumerate(result.viewport_artifacts, 1):
            if os.path.exists(screenshot):
                size_kb = os.path.getsize(screenshot) / 1024
                print(f"  Screenshot {i}: {screenshot} ({size_kb:.1f} KB)")
        
        return result
        
    finally:
        await inspector.close()


if __name__ == "__main__":
    result = asyncio.run(minimal_test())
    print(f"🎉 Test complete - found {len(result.findings)} issues")