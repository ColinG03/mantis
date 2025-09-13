#!/usr/bin/env python3
"""
Simple example of using the Mantis Inspector with the new simplified interface.

The orchestrator just needs to call inspector.inspect_page(url) for each page.
"""

import asyncio
from src.inspector import get_inspector


async def main():
    """Example of the simplified inspector usage"""
    
    # Get the singleton inspector instance
    inspector = await get_inspector()
    
    try:
        print("🔍 Starting simplified inspection...")
        
        # Just pass a URL - that's it!
        result = await inspector.inspect_page("https://example.com")
        
        # Display results
        print(f"\n✅ Inspection completed for {result.page_url}")
        print(f"📊 Status: {result.status}")
        print(f"🔗 Found {len(result.outlinks)} outlinks")
        print(f"🐛 Found {len(result.findings)} issues")
        print(f"📱 Tested {len(result.viewport_artifacts)} viewports")
        
        # Show sample issues
        if result.findings:
            print(f"\n📋 Sample issues:")
            for i, bug in enumerate(result.findings[:3]):
                print(f"  {i+1}. [{bug.severity.upper()}] {bug.summary}")
        
        # Show performance
        if result.timings:
            load_time = result.timings.get('total_load_time', 0)
            print(f"\n⚡ Page loaded in {load_time:.0f}ms")
        
        return result
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None
    
    finally:
        # Clean up when done
        await inspector.close()


async def inspect_multiple_pages():
    """Example of inspecting multiple pages with the same inspector"""
    
    inspector = await get_inspector()
    
    urls = [
        "https://example.com",
        "https://example.com/about", 
        "https://example.com/contact"
    ]
    
    try:
        results = []
        
        for url in urls:
            print(f"🔍 Inspecting {url}...")
            result = await inspector.inspect_page(url)
            results.append(result)
            
            # Show quick summary
            print(f"  Found {len(result.findings)} issues")
        
        # Overall summary
        total_issues = sum(len(r.findings) for r in results)
        print(f"\n📊 Total: {total_issues} issues across {len(results)} pages")
        
        return results
        
    finally:
        await inspector.close()


if __name__ == "__main__":
    # Run single page example
    print("=== Single Page Example ===")
    result = asyncio.run(main())
    
    print("\n=== Multiple Pages Example ===")
    results = asyncio.run(inspect_multiple_pages())
