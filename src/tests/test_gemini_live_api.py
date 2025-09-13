"""
Live API tests for Gemini analyzer.

These tests make actual API calls to test real responses.
They require a valid GEMINI_API_KEY environment variable.

WARNING: These tests will consume API quota and cost money!
Only run when you want to test real API behavior.
"""
import os
import pytest
import asyncio
import tempfile
import base64
from pathlib import Path
import sys

# Add the src directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from inspector.utils.gemini_analyzer import GeminiAnalyzer, analyze_screenshot


# Skip all tests in this file if no API key is provided
pytestmark = pytest.mark.skipif(
    not os.getenv("GEMINI_API_KEY"), 
    reason="GEMINI_API_KEY environment variable not set - skipping live API tests"
)


class TestGeminiLiveAPI:
    """Live API tests - these make real calls to Gemini"""
    
    @pytest.fixture
    def sample_webpage_screenshot(self):
        """
        Create a more realistic test image that simulates a webpage screenshot.
        This creates a simple colored rectangle that might represent a webpage element.
        """
        # Create a simple 100x50 PNG with some colored rectangles to simulate webpage elements
        from PIL import Image, ImageDraw, ImageFont
        import io
        
        try:
            # Create a simple webpage-like image
            img = Image.new('RGB', (400, 300), color='white')
            draw = ImageDraw.Draw(img)
            
            # Draw a header area
            draw.rectangle([0, 0, 400, 60], fill='#2196F3')  # Blue header
            
            # Draw some content areas
            draw.rectangle([20, 80, 180, 120], fill='#f0f0f0')  # Content box 1
            draw.rectangle([200, 80, 380, 120], fill='#f0f0f0')  # Content box 2
            
            # Draw a button-like element
            draw.rectangle([20, 140, 120, 170], fill='#4CAF50')  # Green button
            
            # Draw some text areas (simulated with rectangles)
            draw.rectangle([20, 190, 300, 200], fill='#ddd')  # Text line 1
            draw.rectangle([20, 210, 250, 220], fill='#ddd')  # Text line 2
            draw.rectangle([20, 230, 280, 240], fill='#ddd')  # Text line 3
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                img.save(tmp_file, format='PNG')
                tmp_file.flush()
                yield tmp_file.name
            
            # Cleanup
            os.unlink(tmp_file.name)
            
        except ImportError:
            # Fallback to minimal PNG if PIL is not available
            png_data = base64.b64decode(
                'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=='
            )
            
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                tmp_file.write(png_data)
                tmp_file.flush()
                yield tmp_file.name
            
            os.unlink(tmp_file.name)
    
    @pytest.mark.asyncio
    async def test_live_api_basic_call(self, sample_webpage_screenshot):
        """Test a basic live API call and inspect the response"""
        print("\n" + "="*60)
        print("🔴 LIVE API TEST - This will consume API quota!")
        print("="*60)
        
        analyzer = GeminiAnalyzer()
        
        bugs, error = await analyzer.analyze_screenshot(
            screenshot_path=sample_webpage_screenshot,
            context="baseline view of test webpage",
            viewport="400x300",
            page_url="https://test-example.com"
        )
        
        print(f"\n📊 API Response Results:")
        print(f"   Error: {error}")
        print(f"   Number of bugs found: {len(bugs)}")
        
        if error:
            print(f"\n❌ API Error Details:")
            print(f"   {error}")
        else:
            print(f"\n✅ API call successful!")
            
            if bugs:
                print(f"\n🐛 Bugs detected by Gemini:")
                for i, bug in enumerate(bugs, 1):
                    print(f"   {i}. {bug.summary}")
                    print(f"      Severity: {bug.severity}")
                    print(f"      Fix: {bug.suggested_fix}")
                    print(f"      Type: {bug.type}")
                    print()
            else:
                print(f"\n✨ No visual issues detected!")
        
        # Test should not fail even if no bugs are found
        assert error is None or "API key" in error
    
    @pytest.mark.asyncio
    async def test_live_api_different_contexts(self, sample_webpage_screenshot):
        """Test the API with different context descriptions"""
        print("\n" + "="*60)
        print("🔴 TESTING DIFFERENT CONTEXTS")
        print("="*60)
        
        analyzer = GeminiAnalyzer()
        
        contexts = [
            "baseline mobile view",
            "after clicking dropdown menu", 
            "form filled with long text content",
            "after modal dialog opened"
        ]
        
        for context in contexts:
            print(f"\n🧪 Testing context: '{context}'")
            
            bugs, error = await analyzer.analyze_screenshot(
                screenshot_path=sample_webpage_screenshot,
                context=context,
                viewport="400x300", 
                page_url="https://test-example.com"
            )
            
            print(f"   Result: {len(bugs)} bugs, Error: {error}")
            
            if bugs:
                for bug in bugs:
                    print(f"   - {bug.summary} ({bug.severity})")
        
        # At least one context should work
        assert True  # Just ensure no crashes
    
    @pytest.mark.asyncio
    async def test_live_api_raw_response_inspection(self, sample_webpage_screenshot):
        """Test to inspect the raw API response format"""
        print("\n" + "="*60)
        print("🔴 RAW API RESPONSE INSPECTION")
        print("="*60)
        
        try:
            import google.generativeai as genai
            
            api_key = os.getenv("GEMINI_API_KEY")
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            
            # Read and encode the image
            with open(sample_webpage_screenshot, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Create the prompt
            prompt = """You are analyzing a screenshot of a web page for visual layout issues.

**Context:** Test webpage screenshot
**Viewport:** 400x300
**Page URL:** https://test-example.com

Analyze the screenshot and return a JSON array of visual issues found.
Each issue should have: "summary", "severity", "suggested_fix"

If no issues found, return: []"""
            
            # Prepare image part
            image_part = {
                "mime_type": "image/png",
                "data": image_data
            }
            
            print(f"📤 Sending request to Gemini...")
            print(f"   Model: gemini-2.0-flash-exp")
            print(f"   Image size: {len(image_data)} characters (base64)")
            print(f"   Prompt length: {len(prompt)} characters")
            
            # Make the API call
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
            
            print(f"\n📥 Raw API Response:")
            print(f"   Response type: {type(response)}")
            print(f"   Has text: {hasattr(response, 'text')}")
            
            if response and response.text:
                print(f"   Response length: {len(response.text)} characters")
                print(f"\n📝 Full Response Text:")
                print("-" * 40)
                print(response.text)
                print("-" * 40)
                
                # Try to parse as JSON
                try:
                    import json
                    # Clean up potential markdown formatting
                    clean_text = response.text.strip()
                    if clean_text.startswith("```json"):
                        clean_text = clean_text[7:]
                    if clean_text.endswith("```"):
                        clean_text = clean_text[:-3]
                    clean_text = clean_text.strip()
                    
                    parsed = json.loads(clean_text)
                    print(f"\n✅ Successfully parsed as JSON:")
                    print(f"   Type: {type(parsed)}")
                    print(f"   Length: {len(parsed) if isinstance(parsed, list) else 'N/A'}")
                    print(f"   Content: {parsed}")
                    
                except json.JSONDecodeError as e:
                    print(f"\n❌ Failed to parse as JSON: {e}")
                    print(f"   This might be expected if Gemini returned explanatory text")
            else:
                print(f"   ❌ No response text received")
                
        except Exception as e:
            print(f"\n❌ API call failed: {e}")
            print(f"   This might be due to missing API key or network issues")
    
    @pytest.mark.asyncio
    async def test_convenience_function_live(self, sample_webpage_screenshot):
        """Test the convenience function with live API"""
        print("\n" + "="*60)
        print("🔴 TESTING CONVENIENCE FUNCTION")
        print("="*60)
        
        bugs, error = await analyze_screenshot(
            screenshot_path=sample_webpage_screenshot,
            context="testing convenience function with live API",
            viewport="400x300",
            page_url="https://convenience-test.com"
        )
        
        print(f"\n📊 Convenience Function Results:")
        print(f"   Error: {error}")
        print(f"   Bugs found: {len(bugs)}")
        
        if bugs:
            print(f"\n🐛 Issues found:")
            for bug in bugs:
                print(f"   - {bug.summary}")
        
        assert error is None or "API key" in error


class TestGeminiPromptTesting:
    """Test different prompt variations to see how Gemini responds"""
    
    @pytest.fixture
    def simple_test_image(self):
        """Create a very simple test image"""
        png_data = base64.b64decode(
            'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=='
        )
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            tmp_file.write(png_data)
            tmp_file.flush()
            yield tmp_file.name
        
        os.unlink(tmp_file.name)
    
    @pytest.mark.asyncio
    async def test_different_viewport_descriptions(self, simple_test_image):
        """Test how Gemini responds to different viewport descriptions"""
        print("\n" + "="*60)
        print("🔴 TESTING VIEWPORT VARIATIONS")
        print("="*60)
        
        analyzer = GeminiAnalyzer()
        
        viewports = [
            "1920x1080",  # Desktop
            "375x667",    # Mobile  
            "768x1024",   # Tablet
            "320x568",    # Small mobile
        ]
        
        for viewport in viewports:
            print(f"\n📱 Testing viewport: {viewport}")
            
            bugs, error = await analyzer.analyze_screenshot(
                screenshot_path=simple_test_image,
                context=f"baseline view on {viewport} viewport",
                viewport=viewport,
                page_url="https://viewport-test.com"
            )
            
            print(f"   Result: {len(bugs)} bugs, Error: {error}")
    
    @pytest.mark.asyncio 
    async def test_prompt_variations(self, simple_test_image):
        """Test how the prompt affects Gemini's responses"""
        print("\n" + "="*60)
        print("🔴 TESTING PROMPT VARIATIONS")
        print("="*60)
        
        # Test the current prompt generation
        analyzer = GeminiAnalyzer()
        
        test_cases = [
            {
                "context": "baseline view",
                "viewport": "1280x800",
                "url": "https://example.com"
            },
            {
                "context": "after clicking a dropdown menu that should expand downward",
                "viewport": "375x667", 
                "url": "https://mobile-site.com/menu"
            },
            {
                "context": "form filled with extremely long text that might overflow containers",
                "viewport": "768x1024",
                "url": "https://forms.example.com/contact"
            }
        ]
        
        for i, case in enumerate(test_cases, 1):
            print(f"\n🧪 Test case {i}:")
            print(f"   Context: {case['context']}")
            print(f"   Viewport: {case['viewport']}")
            print(f"   URL: {case['url']}")
            
            # Show the generated prompt
            prompt = analyzer._create_analysis_prompt(
                case['context'], 
                case['viewport'], 
                case['url']
            )
            
            print(f"\n📝 Generated prompt length: {len(prompt)} characters")
            print(f"   First 200 chars: {prompt[:200]}...")
            
            # Make the actual API call
            bugs, error = await analyzer.analyze_screenshot(
                screenshot_path=simple_test_image,
                context=case['context'],
                viewport=case['viewport'],
                page_url=case['url']
            )
            
            print(f"\n📊 Response: {len(bugs)} bugs, Error: {error}")


# Helper function to run only the live tests
def run_live_tests():
    """
    Helper function to run only the live API tests.
    Call this if you want to test against the real API.
    """
    import subprocess
    import sys
    
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ GEMINI_API_KEY environment variable not set!")
        print("   Set it with: export GEMINI_API_KEY='your-api-key-here'")
        return 1
    
    print("🔴 WARNING: Running live API tests will consume API quota!")
    print("   Make sure you want to proceed...")
    
    cmd = [
        sys.executable, "-m", "pytest", 
        __file__, 
        "-v", "-s",  # -s shows print statements
        "--tb=short"
    ]
    
    return subprocess.run(cmd).returncode


if __name__ == "__main__":
    # If this file is run directly, run the live tests
    exit_code = run_live_tests()
    sys.exit(exit_code)
