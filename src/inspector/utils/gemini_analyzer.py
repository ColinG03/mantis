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
    
    def __init__(self, api_key: Optional[str] = None, verbose: bool = False):
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
        self.verbose = verbose
        
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
        return f"""
You are an expert UI/UX auditor. You are given a single static screenshot from the {viewport} viewport of {page_url}. 

Your job is to detect ONLY severe, visible visual layout problems that make the page hard or impossible to read or use.

CRITICAL INSTRUCTION: 
Respond with **VALID JSON ONLY** — no explanations, no prose, no markdown. 
If no problems are detected, return exactly: []

=============================
STRICT RULES (WHAT TO IGNORE)
=============================
- IGNORE anything that is simply off-screen or partially out of view because scrolling would reveal it.
- IGNORE dropdown menus, modals, or popovers that cover content behind them. This is expected behavior unless the menu itself is broken (e.g. misaligned, visually corrupted, overlapping itself).
- IGNORE minor spacing, padding, or alignment preferences unless they make text unreadable or cause elements to collide.
- IGNORE color, contrast, fonts, or styling complaints — these are not visual bugs for this task.
- IGNORE missing features or functionality — you are only analyzing what is visible.
- IGNORE anything that would require interaction to confirm (hover states, animations, clickable links).
- IGNORE performance issues, loading times, or accessibility issues unrelated to visual layout.

=============================
WHAT COUNTS AS A REAL BUG
=============================
You must ONLY report issues that meet ALL these conditions:
1. **CLEARLY VISIBLE in the screenshot**
2. **SEVERE enough** that they would confuse a typical user, make text unreadable, or break the layout
3. **NOT fixable by scrolling** — the problem must exist entirely within the visible frame

=============================
TYPES OF ISSUES TO REPORT
=============================
Report ONLY if they are obvious and severe:
- **Layout Breaks**: Overlapping text or elements that cannot be read, elements cut off in the middle (not just cropped by viewport bottom).
- **Critical Misalignment**: UI elements that are completely out of place (e.g. buttons floating on top of unrelated sections, forms disjointed).
- **Broken or Missing Assets**: Images showing "broken" icons or missing file placeholders.
- **Unreadable Text**: Text rendered outside its container, overlapping with other text, or clipped so words are incomplete.
- **Navigation Problems**: Entire navbars missing, completely broken hamburger menus (e.g. icon overlaps other UI, menu renders in wrong position).

=============================
OUTPUT FORMAT
=============================
Return a JSON array where each object has:
- "summary": Brief description of the issue
- "severity": One of "low", "medium", "high", "critical"
- "suggested_fix": Optional short suggestion for how to fix the issue

If no valid issues are found, respond with:
[]

EXAMPLE OUTPUT (when issues exist):
[
  {{
    "summary": "Main heading text overlaps with hero image, making it unreadable",
    "severity": "high",
    "suggested_fix": "Adjust CSS so heading text is fully visible and not overlapping image"
  }},
  {{
    "summary": "Submit button is half cut off by the viewport bottom",
    "severity": "high",
    "suggested_fix": "Adjust CSS so button is fully visible and not overlapping viewport bottom"
  }}
]
"""

    
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
                if self.verbose:
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
                    suggested_fix=bug_data.get("suggested_fix", ""),
                    impact_description=bug_data.get("impact_description", ""),
                    affected_elements=bug_data.get("affected_elements", []),
                    reproduction_steps=bug_data.get("reproduction_steps", []),
                    fix_steps=bug_data.get("fix_steps", []),
                    wcag_guidelines=bug_data.get("wcag_guidelines", []),
                    evidence=evidence
                )
                bugs.append(bug)
            
            return bugs
            
        except json.JSONDecodeError as e:
            if self.verbose:
                print(f"Warning: Failed to parse Gemini JSON response: {str(e)}")
                print(f"Response was: {response_text[:200]}...")
            return []
        except Exception as e:
            if self.verbose:
                print(f"Warning: Error parsing Gemini response: {str(e)}")
            return []
    
    async def analyze_screenshot(self, screenshot_path: str, viewport: str, page_url: str, model: str, verbose: bool = False) -> Tuple[List[Bug], Optional[str]]:
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
async def analyze_screenshot(screenshot_path: str, context: str, viewport: str, page_url: str, verbose: bool = False) -> Tuple[List[Bug], Optional[str]]:
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
        analyzer = GeminiAnalyzer(verbose=verbose)
        return await analyzer.analyze_screenshot(screenshot_path, context, viewport, page_url)
    except Exception as e:
        return [], f"Failed to initialize Gemini analyzer: {str(e)}"
