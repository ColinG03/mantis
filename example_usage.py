#!/usr/bin/env python3
"""
Example usage of the Mantis UI Inspector.

This demonstrates how to set up and run the inspector with various checks
to find UI bugs and accessibility issues on a webpage.
"""

import asyncio
import os
from src.core.types import InspectorOptions
from src.inspector import Inspector, AccessibilityCheck, VisualLayoutCheck


async def main():
    """Example of running the inspector on a webpage"""
    
    # Create inspector instance
    inspector = Inspector()
    
    # Register checks to run
    inspector.register_check(AccessibilityCheck())
    inspector.register_check(VisualLayoutCheck())
    
    # Configure inspection options
    options = InspectorOptions(
        url="https://example.com",  # Replace with your target URL
        viewport_set=[
            {"width": 1280, "height": 800},  # Desktop
            {"width": 768, "height": 1024},  # Tablet
            {"width": 375, "height": 667}    # Mobile
        ],
        action_budget=10,  # Limit interactive actions
        allow_interactions=True,
        same_host_only=True,
        seed_host="example.com",
        auth_cookies=None,  # Add cookies if authentication needed
        headers=None,       # Add custom headers if needed
        timeouts={
            "nav_ms": 30000,    # 30 second navigation timeout
            "action_ms": 5000   # 5 second action timeout
        },
        out_dir="./mantis_output"  # Output directory for evidence
    )
    
    # Create output directory
    os.makedirs(options.out_dir, exist_ok=True)
    
    try:
        print(f"🔍 Starting inspection of {options.url}")
        print(f"📱 Testing {len(options.viewport_set)} viewports")
        print(f"🔧 Running {len(inspector.checks)} check types")
        
        # Run the inspection
        result = await inspector.inspect_page(options)
        
        # Display results
        print(f"\n✅ Inspection completed!")
        print(f"📊 Status Code: {result.status}")
        print(f"🔗 Found {len(result.outlinks)} outlinks")
        print(f"🐛 Found {len(result.findings)} issues")
        print(f"📸 Generated {len(result.viewport_artifacts)} viewport screenshots")
        
        # Group findings by severity
        severity_counts = {}
        for bug in result.findings:
            severity_counts[bug.severity] = severity_counts.get(bug.severity, 0) + 1
        
        print(f"\n📈 Issues by severity:")
        for severity, count in severity_counts.items():
            print(f"  {severity}: {count}")
        
        # Show first few issues as examples
        if result.findings:
            print(f"\n🔍 Sample issues found:")
            for i, bug in enumerate(result.findings[:3]):
                print(f"  {i+1}. [{bug.severity.upper()}] {bug.summary}")
                if bug.suggested_fix:
                    print(f"     💡 Fix: {bug.suggested_fix}")
        
        # Show performance metrics
        if result.timings:
            print(f"\n⚡ Performance metrics:")
            for metric, value in result.timings.items():
                if isinstance(value, (int, float)):
                    print(f"  {metric}: {value:.2f}ms")
        
        print(f"\n📁 Evidence saved to: {options.out_dir}")
        
        return result
        
    except Exception as e:
        print(f"❌ Inspection failed: {str(e)}")
        return None


if __name__ == "__main__":
    # Run the example
    result = asyncio.run(main())
    
    if result:
        print(f"\n🎉 Inspection completed successfully!")
        print(f"   Found {len(result.findings)} total issues")
    else:
        print(f"\n💥 Inspection failed!")
