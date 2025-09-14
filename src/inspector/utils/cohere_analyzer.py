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
    import cohere
except ImportError:
    cohere = None

try:
    from ...core.types import Bug, Evidence
except ImportError:
    from core.types import Bug, Evidence


class CohereAnalyzer:
    """
    Analyzes screenshots using Cohere's Command-A-Vision (command-a-vision-07-2025) model to detect visual layout issues and severe UX problems.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Cohere analyzer.
        
        Args:
            api_key: Cohere API key. If None, will try to get from COHERE_API_KEY env var.
        """
        if cohere is None:
            raise ImportError("cohere package is required. Install with: pip install cohere")
        
        self.api_key = api_key or os.getenv("COHERE_API_KEY")
        if not self.api_key:
            raise ValueError("Cohere API key is required. Set COHERE_API_KEY environment variable or pass api_key parameter.")
        
        # Initialize Cohere client
        self.client = cohere.ClientV2(api_key=self.api_key)
        self.model = 'command-a-vision-07-2025'  # Using the latest Command-A-Vision multimodal model
        
        # Generation config for consistent responses
        self.generation_config = {
            "temperature": 0.1,  # Low temperature for consistent bug detection
            "max_tokens": 4000,  # Command-A-Vision supports up to 8K output tokens
        }
    
    async def analyze_screenshot(self, image_data: str, viewport: str, page_url: str) -> Tuple[List[Bug], str]:
        """
        Analyze a screenshot for visual layout issues and UX problems.
        
        Args:
            image_data: Base64 encoded PNG image data
            viewport: Viewport description (e.g., "desktop 1280x800")
            page_url: URL of the page being analyzed
            
        Returns:
            Tuple of (List of Bug objects, error message if any)
        """
        try:
            prompt = self._create_analysis_prompt(viewport, page_url)
            
            # Prepare the message with image using Cohere's format
            messages = [{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_data}"}
                    }
                ]
            }]
            
            # Make API call with timeout
            response = await asyncio.wait_for(
                self._make_api_call(messages),
                timeout=30.0
            )
            
            if not response or not response.message or not response.message.content:
                return [], "Cohere API returned empty response"
            
            # Extract text from response
            response_text = ""
            for content in response.message.content:
                if hasattr(content, 'text'):
                    response_text += content.text
            
            if not response_text:
                return [], "Cohere API returned no text content"
            
            # Parse the response
            bugs = self._parse_cohere_response(response_text, page_url, viewport)
            return bugs, ""
            
        except asyncio.TimeoutError:
            return [], "Cohere API timeout after 30 seconds"
        except Exception as e:
            return [], f"Cohere API error: {str(e)}"
    
    async def _make_api_call(self, messages: List[Dict[str, Any]]) -> Any:
        """Make async API call to Cohere"""
        # Cohere doesn't have native async support, so we'll run in executor
        loop = asyncio.get_event_loop()
        
        def sync_call():
            return self.client.chat(
                model=self.model,
                messages=messages,
                temperature=self.generation_config["temperature"],
                max_tokens=self.generation_config["max_tokens"]
            )
        
        return await loop.run_in_executor(None, sync_call)
    
    def _create_analysis_prompt(self, viewport: str, page_url: str) -> str:
        """Create the analysis prompt for Cohere"""
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


    def _parse_cohere_response(self, response_text: str, page_url: str, viewport: str) -> List[Bug]:
        """
        Parse Cohere's response and convert to Bug objects.
        
        Args:
            response_text: Raw response from Cohere
            page_url: URL of the analyzed page
            viewport: Viewport description
            
        Returns:
            List of Bug objects
        """
        try:
            # Clean up response - remove any markdown formatting
            clean_response = response_text.strip()
            
            # Handle various markdown patterns
            if clean_response.startswith('```json'):
                clean_response = clean_response[7:]
            elif clean_response.startswith('```'):
                clean_response = clean_response[3:]
            
            if clean_response.endswith('```'):
                clean_response = clean_response[:-3]
            
            # Remove common prefixes that LLMs sometimes add
            prefixes_to_remove = ['Here is the JSON:', 'JSON:', 'Here\'s the analysis:', 'Response:']
            for prefix in prefixes_to_remove:
                if clean_response.startswith(prefix):
                    clean_response = clean_response[len(prefix):].strip()
            
            clean_response = clean_response.strip()
            
            # Parse JSON
            bug_data = json.loads(clean_response)
            
            # Handle case where response is not a list
            if not isinstance(bug_data, list):
                print(f"Warning: Expected list, got {type(bug_data)}. Response: {clean_response[:200]}...")
                # If it's a single object, wrap it in a list
                if isinstance(bug_data, dict):
                    print("Converting single object to list")
                    bug_data = [bug_data]
                else:
                    return []
            
            bugs = []
            for item in bug_data:
                if not isinstance(item, dict):
                    continue
                    
                # Validate and normalize fields
                bug_type = item.get('type', 'UI')
                if bug_type != 'UI': 
                    bug_type = 'UI'
                
                severity = item.get('severity', 'medium').lower()
                if severity not in ['low', 'medium', 'high', 'critical']:
                    severity = 'medium'  # Default fallback
                
                # Create Bug object
                bug = Bug(
                    id=item.get('id', str(uuid.uuid4())),
                    type=bug_type,
                    severity=severity,
                    page_url=page_url,
                    summary=item.get('summary', 'Visual issue detected'),
                    suggested_fix=item.get('suggested_fix', ''),
                    impact_description=item.get('impact_description', ''),
                    affected_elements=item.get('affected_elements', []),
                    reproduction_steps=item.get('reproduction_steps', []),
                    fix_steps=item.get('fix_steps', []),
                    wcag_guidelines=item.get('wcag_guidelines', []),
                    evidence=Evidence(
                        screenshot_path="",  # Will be set by caller
                        viewport=viewport,
                        console_log="",  # Will be set by caller
                        wcag=None,
                        action_log=""  # Will be set by caller
                    )
                )
                bugs.append(bug)
            
            return bugs
            
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON response: {e}")
            print(f"Response was: {response_text[:500]}...")
            return []
        except Exception as e:
            print(f"Error parsing Cohere response: {e}")
            return []


# Convenience function for backward compatibility
async def analyze_screenshot(image_path_or_data: str, viewport: str, page_url: str, api_key: Optional[str] = None) -> Tuple[List[Bug], str]:
    """
    Analyze a screenshot using Cohere vision model.
    
    Args:
        image_path_or_data: Either a file path to a screenshot OR base64 encoded PNG image data
        viewport: Viewport description (e.g., "desktop 1280x800")
        page_url: URL of the page being analyzed
        api_key: Optional Cohere API key
        
    Returns:
        Tuple of (List of Bug objects, error message if any)
    """
    analyzer = CohereAnalyzer(api_key=api_key)
    
    # Check if input is a file path or base64 data
    if os.path.exists(image_path_or_data):
        # It's a file path - convert to base64
        try:
            with open(image_path_or_data, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            return [], f"Failed to read image file: {str(e)}"
    else:
        # Assume it's already base64 data
        image_data = image_path_or_data
    
    return await analyzer.analyze_screenshot(image_data, viewport, page_url)