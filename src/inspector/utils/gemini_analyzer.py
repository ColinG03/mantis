import os
import uuid
import base64
import asyncio
from typing import List, Tuple, Optional, Dict, Any
import json

try:
    from dotenv import load_dotenv
    load_dotenv()  # Load environment variables from .env file
except ImportError:
    pass  # dotenv is optional, fallback to system env vars

try:
    import google.generativeai as genai
except ImportError:
    genai = None

try:
    from ...core.types import Bug, Evidence
except ImportError:
    from core.types import Bug, Evidence


class GeminiAnalyzer:
    """
    Analyzes screenshots using Gemini 2.5 Flash to detect visual layout issues and severe UX problems.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini analyzer.
        
        Args:
            api_key: Gemini API key. If None, will try to get from GEMINI_API_KEY env var.
        """
        if genai is None:
            raise ImportError("google-generativeai package is required. Install with: pip install google-generativeai")
        
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Gemini API key is required. Set GEMINI_API_KEY environment variable or pass api_key parameter.")
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Generation config for consistent responses
        self.generation_config = {
            "temperature": 0.1,  # Low temperature for consistent bug detection
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": 2048,
        }
    
    def _encode_image(self, image_path: str) -> str:
        """Encode image to base64 for Gemini API"""
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            raise ValueError(f"Failed to encode image {image_path}: {str(e)}")
    
    def _create_analysis_prompt(self, context: str, viewport: str, page_url: str) -> str:
        """
        Create a focused prompt for visual layout bug detection.
        
        Args:
            context: What just happened (e.g., "baseline view", "after clicking Home dropdown")
            viewport: Viewport size (e.g., "1280x800")
            page_url: URL being tested
        """
        return f"""You are analyzing a screenshot of a web page for severe visual layout issues and UX problems. Only report issues that will drastically impair the user's ability to use the page.

**Context:** {context}
**Viewport:** {viewport}
**Page URL:** {page_url}

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
- Spacing inconsistencies
- Viewport cutoffs that can be easily scrolled into view.
- Contrast or color issues.

**Response Format:**
Return a JSON array of bug objects. Each bug should have:
- "summary": Brief description of the visual issue
- "severity": One of "low", "medium", "high", "critical"
- "suggested_fix": Optional brief suggestion

If no significant visual issues are found, return an empty array: []

**Example response:**
[
  {{
    "summary": "Header text overflows container on mobile viewport",
    "severity": "high", 
    "suggested_fix": "Add text wrapping or responsive font sizing"
  }},
  {{
    "summary": "Dropdown menu extends beyond screen boundaries",
    "severity": "medium",
    "suggested_fix": "Implement dropdown position detection and adjustment"
  }}
]

Analyze the screenshot and respond with JSON only:"""
    
    def _parse_gemini_response(self, response_text: str, page_url: str, screenshot_path: str, viewport: str) -> List[Bug]:
        """
        Parse Gemini's JSON response into Bug objects.
        
        Args:
            response_text: Raw response from Gemini
            page_url: URL being tested
            screenshot_path: Path to the analyzed screenshot
            viewport: Viewport size
        """
        try:
            # Clean up response text (remove markdown formatting if present)
            clean_text = response_text.strip()
            if clean_text.startswith("```json"):
                clean_text = clean_text[7:]
            if clean_text.endswith("```"):
                clean_text = clean_text[:-3]
            clean_text = clean_text.strip()
            
            # Parse JSON
            bug_data_list = json.loads(clean_text)
            
            if not isinstance(bug_data_list, list):
                print(f"Warning: Gemini returned non-list response: {type(bug_data_list)}")
                return []
            
            bugs = []
            for bug_data in bug_data_list:
                if not isinstance(bug_data, dict):
                    continue
                
                # Create Evidence object with screenshot
                evidence = Evidence(
                    screenshot_path=screenshot_path,
                    viewport=viewport
                )
                
                # Create Bug object
                bug = Bug(
                    id=str(uuid.uuid4()),
                    type="UI",  # All visual issues map to UI type
                    severity=bug_data.get("severity", "medium"),
                    page_url=page_url,
                    summary=bug_data.get("summary", "Visual layout issue detected"),
                    suggested_fix=bug_data.get("suggested_fix"),
                    evidence=evidence
                )
                bugs.append(bug)
            
            return bugs
            
        except json.JSONDecodeError as e:
            print(f"Warning: Failed to parse Gemini JSON response: {str(e)}")
            print(f"Response was: {response_text[:200]}...")
            return []
        except Exception as e:
            print(f"Warning: Error parsing Gemini response: {str(e)}")
            return []
    
    async def analyze_screenshot(self, screenshot_path: str, context: str, viewport: str, page_url: str) -> Tuple[List[Bug], Optional[str]]:
        """
        Analyze a screenshot for visual layout issues and severe UX problems.
        
        Args:
            screenshot_path: Path to the screenshot file
            context: Description of what just happened (e.g., "after clicking Home dropdown")
            viewport: Viewport size (e.g., "1280x800") 
            page_url: URL being tested
            
        Returns:
            Tuple of (bugs_found, error_message)
            - bugs_found: List of Bug objects for visual issues found
            - error_message: None if successful, error string if API failed
        """
        try:
            # Validate screenshot exists
            if not os.path.exists(screenshot_path):
                return [], f"Screenshot file not found: {screenshot_path}"
            
            # Encode image
            try:
                image_data = self._encode_image(screenshot_path)
            except Exception as e:
                return [], f"Failed to encode screenshot: {str(e)}"
            
            # Create prompt
            prompt = self._create_analysis_prompt(context, viewport, page_url)
            
            # Prepare image part for Gemini
            image_part = {
                "mime_type": "image/png",
                "data": image_data
            }
            
            # Make API call with timeout
            try:
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        self.model.generate_content,
                        [prompt, image_part],
                        generation_config=self.generation_config
                    ),
                    timeout=30.0  # 30 second timeout
                )
                
                if not response or not response.text:
                    return [], "Gemini API returned empty response"
                
                # Parse response into Bug objects
                bugs = self._parse_gemini_response(response.text, page_url, screenshot_path, viewport)
                return bugs, None
                
            except asyncio.TimeoutError:
                return [], "Gemini API timeout after 30 seconds"
            except Exception as e:
                return [], f"Gemini API error: {str(e)}"
                
        except Exception as e:
            return [], f"Unexpected error in analyze_screenshot: {str(e)}"


# Convenience function for easy integration
async def analyze_screenshot(screenshot_path: str, context: str, viewport: str, page_url: str) -> Tuple[List[Bug], Optional[str]]:
    """
    Convenience function to analyze a screenshot without managing GeminiAnalyzer instance.
    
    Args:
        screenshot_path: Path to the screenshot file
        context: Description of what just happened (e.g., "after clicking Home dropdown")
        viewport: Viewport size (e.g., "1280x800")
        page_url: URL being tested
        
    Returns:
        Tuple of (bugs_found, error_message)
    """
    try:
        analyzer = GeminiAnalyzer()
        return await analyzer.analyze_screenshot(screenshot_path, context, viewport, page_url)
    except Exception as e:
        return [], f"Failed to initialize Gemini analyzer: {str(e)}"
