#!/usr/bin/env python3
"""
Script to test live Gemini API calls and see actual responses.

This script will make real API calls to Gemini and show you exactly what it returns.
WARNING: This consumes API quota!

Usage:
    export GEMINI_API_KEY="your-api-key-here"
    python test_live_gemini.py
"""

import os
import sys
import asyncio
import tempfile
import base64
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from inspector.utils.gemini_analyzer import GeminiAnalyzer, analyze_screenshot


async def create_test_image():
    """Create a simple test image that looks like a webpage"""
    try:
        from PIL import Image, ImageDraw
        
        # Create a simple webpage-like image
        img = Image.new('RGB', (400, 300), color='white')
        draw = ImageDraw.Draw(img)
        
        # Draw a header
        draw.rectangle([0, 0, 400, 60], fill='#2196F3')
        
        # Draw some content boxes
        draw.rectangle([20, 80, 180, 120], fill='#f0f0f0')
        draw.rectangle([200, 80, 380, 120], fill='#f0f0f0')
        
        # Draw a button
        draw.rectangle([20, 140, 120, 170], fill='#4CAF50')
        
        # Draw text lines
        draw.rectangle([20, 190, 300, 200], fill='#ddd')
        draw.rectangle([20, 210, 250, 220], fill='#ddd')
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            img.save(tmp_file, format='PNG')
            return tmp_file.name
            
    except ImportError:
        print("PIL not available, using minimal PNG...")
        # Fallback to minimal PNG
        png_data = base64.b64decode(
            'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=='
        )
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            tmp_file.write(png_data)
            return tmp_file.name


async def test_basic_api_call():
    """Test a basic API call and show the response"""
    print("="*60)
    print("🧪 TESTING BASIC GEMINI API CALL")
    print("="*60)
    
    # Create test image
    image_path = await create_test_image()
    
    try:
        # Initialize analyzer
        analyzer = GeminiAnalyzer()
        
        print(f"📤 Making API call...")
        print(f"   Image: {image_path}")
        print(f"   Context: 'baseline view of test webpage'")
        print(f"   Viewport: 400x300")
        
        # Make the call
        bugs, error = await analyzer.analyze_screenshot(
            screenshot_path=image_path,
            context="baseline view of test webpage",
            viewport="400x300", 
            page_url="https://test-example.com"
        )
        
        print(f"\n📥 RESPONSE RECEIVED:")
        print(f"   Error: {error}")
        print(f"   Number of bugs: {len(bugs)}")
        
        if error:
            print(f"\n❌ Error Details:")
            print(f"   {error}")
        else:
            print(f"\n✅ API call successful!")
            
            if bugs:
                print(f"\n🐛 Bugs found by Gemini:")
                for i, bug in enumerate(bugs, 1):
                    print(f"\n   Bug #{i}:")
                    print(f"      Summary: {bug.summary}")
                    print(f"      Severity: {bug.severity}")
                    print(f"      Type: {bug.type}")
                    print(f"      Suggested Fix: {bug.suggested_fix}")
                    print(f"      Page URL: {bug.page_url}")
                    print(f"      Evidence Viewport: {bug.evidence.viewport}")
            else:
                print(f"\n✨ No visual issues detected by Gemini!")
                
    finally:
        # Cleanup
        try:
            os.unlink(image_path)
        except:
            pass


async def test_raw_api_response():
    """Test raw API response to see exactly what Gemini returns"""
    print("\n" + "="*60)  
    print("🔍 TESTING RAW API RESPONSE")
    print("="*60)
    
    try:
        import google.generativeai as genai
        
        # Configure Gemini
        api_key = os.getenv("GEMINI_API_KEY")
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Create test image
        image_path = await create_test_image()
        
        # Read and encode image
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        
        # Create prompt (same as analyzer uses)
        prompt = """You are analyzing a screenshot of a web page for visual layout issues and severe UX problems.

**Context:** baseline view of test webpage
**Viewport:** 400x300
**Page URL:** https://test-example.com

**Focus on detecting these types of issues:**
1. **Visual Layout Problems:**
   - Text overflow or cutoff
   - Elements overlapping inappropriately
   - Broken responsive design
   - Content extending beyond containers
   - Severely misaligned elements
   - Broken grid layouts

2. **Severe UX Issues:**
   - Completely unusable interfaces
   - Major visual breakage that prevents interaction
   - Confusing or broken layouts
   - Critical content that's hidden or inaccessible

**DO NOT report:**
- Accessibility issues (color contrast, focus indicators)
- Functional issues (whether buttons work)
- Minor aesthetic preferences
- Small spacing inconsistencies

**Response Format:**
Return a JSON array of bug objects. Each bug should have:
- "summary": Brief description of the visual issue
- "severity": One of "low", "medium", "high", "critical"
- "suggested_fix": Optional brief suggestion

If no significant visual issues are found, return an empty array: []

Analyze the screenshot and respond with JSON only:"""
        
        print(f"📤 Sending direct API request...")
        print(f"   Model: gemini-2.0-flash-exp")
        print(f"   Prompt length: {len(prompt)} chars")
        print(f"   Image data length: {len(image_data)} chars")
        
        # Make direct API call
        image_part = {"mime_type": "image/png", "data": image_data}
        
        response = await asyncio.wait_for(
            asyncio.to_thread(
                model.generate_content,
                [prompt, image_part],
                generation_config={
                    "temperature": 0.1,
                    "top_p": 0.8, 
                    "top_k": 40,
                    "max_output_tokens": 2048,
                }
            ),
            timeout=30.0
        )
        
        print(f"\n📥 RAW GEMINI RESPONSE:")
        print(f"   Response object type: {type(response)}")
        
        if response and hasattr(response, 'text') and response.text:
            print(f"   Response text length: {len(response.text)} chars")
            print(f"\n" + "─"*50)
            print("FULL RESPONSE TEXT:")
            print("─"*50)
            print(response.text)
            print("─"*50)
            
            # Try to parse as JSON
            try:
                import json
                clean_text = response.text.strip()
                if clean_text.startswith("```json"):
                    clean_text = clean_text[7:]
                if clean_text.endswith("```"):
                    clean_text = clean_text[:-3]
                clean_text = clean_text.strip()
                
                parsed = json.loads(clean_text)
                print(f"\n✅ SUCCESSFULLY PARSED AS JSON:")
                print(f"   Type: {type(parsed)}")
                if isinstance(parsed, list):
                    print(f"   Array length: {len(parsed)}")
                    for i, item in enumerate(parsed):
                        print(f"   Item {i}: {item}")
                else:
                    print(f"   Content: {parsed}")
                    
            except json.JSONDecodeError as e:
                print(f"\n❌ FAILED TO PARSE AS JSON:")
                print(f"   Error: {e}")
                print(f"   Raw text might contain explanations or formatting")
        else:
            print(f"   ❌ No response text received")
            
        # Cleanup
        try:
            os.unlink(image_path)
        except:
            pass
            
    except Exception as e:
        print(f"\n❌ Raw API test failed: {e}")


async def test_different_contexts():
    """Test how different contexts affect the response"""
    print("\n" + "="*60)
    print("🎭 TESTING DIFFERENT CONTEXTS")
    print("="*60)
    
    contexts = [
        "baseline view",
        "after clicking dropdown menu",
        "form filled with very long text content",
        "mobile navigation menu opened",
        "modal dialog displayed over content"
    ]
    
    analyzer = GeminiAnalyzer()
    image_path = await create_test_image()
    
    try:
        for i, context in enumerate(contexts, 1):
            print(f"\n🧪 Test {i}: '{context}'")
            
            bugs, error = await analyzer.analyze_screenshot(
                screenshot_path=image_path,
                context=context,
                viewport="400x300",
                page_url=f"https://context-test-{i}.com"
            )
            
            print(f"   Result: {len(bugs)} bugs found")
            if error:
                print(f"   Error: {error}")
            elif bugs:
                for bug in bugs[:2]:  # Show first 2 bugs
                    print(f"   - {bug.summary} ({bug.severity})")
                    
    finally:
        try:
            os.unlink(image_path)
        except:
            pass


async def main():
    """Main test function"""
    # Check for API key
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ GEMINI_API_KEY environment variable not set!")
        print("\nTo run this test:")
        print("1. Get a Gemini API key from https://makersuite.google.com/app/apikey")
        print("2. Set it: export GEMINI_API_KEY='your-key-here'")
        print("3. Run: python test_live_gemini.py")
        return 1
    
    print("🔴 WARNING: This will make real API calls and consume quota!")
    print("Press Enter to continue or Ctrl+C to cancel...")
    try:
        input()
    except KeyboardInterrupt:
        print("\nCancelled by user")
        return 0
    
    try:
        # Run all tests
        await test_basic_api_call()
        await test_raw_api_response() 
        await test_different_contexts()
        
        print("\n" + "="*60)
        print("✅ ALL LIVE TESTS COMPLETED!")
        print("="*60)
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
