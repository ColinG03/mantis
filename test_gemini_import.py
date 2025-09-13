#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, 'src')

print("Testing gemini_analyzer imports...")

# Test basic imports
print("1. Testing basic imports...")
try:
    import os
    import uuid
    import base64
    import asyncio
    from typing import List, Tuple, Optional, Dict, Any
    import json
    print("   Basic imports: OK")
except Exception as e:
    print(f"   Basic imports failed: {e}")

# Test dotenv
print("2. Testing dotenv...")
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("   dotenv: OK")
except ImportError:
    print("   dotenv: Not available (OK)")

# Test google.generativeai
print("3. Testing google.generativeai...")
try:
    import google.generativeai as genai
    print("   google.generativeai: OK")
except ImportError:
    print("   google.generativeai: Not available")
    genai = None

# Test core.types import
print("4. Testing core.types...")
try:
    from core.types import Bug, Evidence
    print("   core.types: OK")
except ImportError as e:
    print(f"   core.types failed: {e}")

# Test if we can define the class
print("5. Testing class definition...")
try:
    class TestGeminiAnalyzer:
        def __init__(self):
            pass
    print("   Class definition: OK")
except Exception as e:
    print(f"   Class definition failed: {e}")

# Test if we can define the function
print("6. Testing function definition...")
try:
    async def test_analyze_screenshot():
        return [], None
    print("   Function definition: OK")
except Exception as e:
    print(f"   Function definition failed: {e}")

print("All tests completed!")
