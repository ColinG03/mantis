#!/usr/bin/env python3
"""
Simple test script for the Mantis Inspector.

This mimics how the orchestrator would use the inspector:
1. Get inspector instance
2. Navigate to URL
3. Capture screenshot
4. Return results

Usage:
    python test_inspector.py
    python test_inspector.py https://example.com
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

from inspector.main import get_inspector


async def test_inspector(url: str = "https://example.com"):
    """
    Test the inspector by navigating to a URL and capturing evidence.
    
    Args:
        url: URL to test (defaults to example.com)
    """
    print(f"🧪 Testing Mantis Inspector")
    print(f"🌐 Target URL: {url}")
    print(f"📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)
    
    inspector = None
    
    try:
        # Get the inspector instance (singleton)
        print("🔧 Initializing inspector...")
        inspector = await get_inspector()
        print("✅ Inspector ready")
        
        # Test navigation and screenshot capture
        print(f"🚀 Navigating to {url}...")
        result = await inspector.inspect_page(url)
        
        # Display results
        print(f"✅ Navigation complete!")
        print(f"📊 Status Code: {result.status}")
        print(f"🔗 Found {len(result.outlinks)} outlinks")
        print(f"🐛 Found {len(result.findings)} issues")
        print(f"📸 Captured {len(result.viewport_artifacts)} viewport screenshots")
        
        # Show screenshot paths
        if result.viewport_artifacts:
            print(f"\n📷 Screenshots saved:")
            for i, screenshot_path in enumerate(result.viewport_artifacts, 1):
                if os.path.exists(screenshot_path):
                    file_size = os.path.getsize(screenshot_path) / 1024  # KB
                    print(f"  {i}. {screenshot_path} ({file_size:.1f} KB)")
                else:
                    print(f"  {i}. {screenshot_path} (file not found)")
        
        # Show sample outlinks
        if result.outlinks:
            print(f"\n🔗 Sample outlinks found:")
            for i, link in enumerate(result.outlinks[:5], 1):
                print(f"  {i}. {link}")
            if len(result.outlinks) > 5:
                print(f"  ... and {len(result.outlinks) - 5} more")
        
        # Show sample issues
        if result.findings:
            print(f"\n🐛 Issues found:")
            for i, bug in enumerate(result.findings[:3], 1):
                print(f"  {i}. [{bug.severity.upper()}] {bug.summary}")
                if bug.evidence.screenshot_path:
                    print(f"     Screenshot: {bug.evidence.screenshot_path}")
                if bug.evidence.console_log:
                    # Show first line of console log
                    first_log_line = bug.evidence.console_log.split('\n')[0]
                    print(f"     Console: {first_log_line}")
            
            if len(result.findings) > 3:
                print(f"  ... and {len(result.findings) - 3} more issues")
        
        # Show performance metrics
        if result.timings:
            print(f"\n⚡ Performance:")
            load_time = result.timings.get('total_load_time', 0)
            nav_time = result.timings.get('navigation_duration', 0)
            print(f"  Navigation: {nav_time:.0f}ms")
            if load_time > 0:
                print(f"  Page Load: {load_time:.0f}ms")
        
        print(f"\n✅ Test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        print(f"   Error type: {type(e).__name__}")
        return False
        
    finally:
        # Always clean up
        if inspector:
            print(f"🧹 Cleaning up...")
            try:
                await inspector.close()
                print(f"✅ Cleanup complete")
            except Exception as cleanup_error:
                print(f"⚠️  Cleanup error: {cleanup_error}")


async def test_multiple_urls():
    """Test the inspector with multiple URLs"""
    urls = [
        "https://example.com",
        "https://httpbin.org/html",  # Simple HTML page
        "https://httpbin.org/json",  # JSON response
    ]
    
    print(f"🧪 Testing Multiple URLs")
    print("-" * 50)
    
    inspector = await get_inspector()
    results = []
    
    try:
        for i, url in enumerate(urls, 1):
            print(f"\n🌐 Test {i}/{len(urls)}: {url}")
            
            try:
                result = await inspector.inspect_page(url)
                results.append((url, result, True))
                print(f"  ✅ Success - {len(result.findings)} issues, {len(result.outlinks)} links")
                
            except Exception as e:
                results.append((url, None, False))
                print(f"  ❌ Failed - {str(e)}")
        
        # Summary
        print(f"\n📊 Summary:")
        successful = sum(1 for _, _, success in results if success)
        print(f"  Successful: {successful}/{len(urls)}")
        
        total_issues = sum(len(result.findings) for _, result, success in results if success and result)
        print(f"  Total Issues: {total_issues}")
        
        return results
        
    finally:
        await inspector.close()


def main():
    """Main entry point"""
    # Get URL from command line or use default
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = "https://example.com"
    
    # Validate URL
    if not url.startswith(('http://', 'https://')):
        url = f"https://{url}"
    
    print(f"Starting inspector test...")
    
    # Run single URL test
    success = asyncio.run(test_inspector(url))
    
    if success:
        print(f"\n" + "="*50)
        print(f"🎉 Inspector test passed!")
        
        # Ask if user wants to test multiple URLs
        try:
            response = input(f"\nRun multi-URL test? (y/N): ").strip().lower()
            if response in ['y', 'yes']:
                asyncio.run(test_multiple_urls())
        except KeyboardInterrupt:
            print(f"\n👋 Test interrupted by user")
    else:
        print(f"\n💥 Inspector test failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
