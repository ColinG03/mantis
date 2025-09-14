"""
Factory for creating screenshot analyzers based on model configuration.
"""

import base64
import os
from typing import List, Tuple, Optional

try:
    from ...core.types import Bug
except ImportError:
    from core.types import Bug


async def analyze_screenshot(
    screenshot_path: str, 
    viewport: str, 
    page_url: str, 
    model: str = 'cohere',
    verbose: bool = False
) -> Tuple[List[Bug], Optional[str]]:
    """
    Analyze a screenshot using the specified model.
    
    Args:
        screenshot_path: Path to the screenshot file
        viewport: Viewport size (e.g., "1280x800")
        page_url: URL being tested
        model: Which model to use ('cohere' or 'gemini')
        
    Returns:
        Tuple of (bugs_found, error_message)
        - bugs_found: List of Bug objects for visual issues found
        - error_message: None if successful, error string if API failed
    """
    if model.lower() == 'gemini':
        return await _analyze_with_gemini(screenshot_path, viewport, page_url, verbose)
    else:  # Default to cohere
        return await _analyze_with_cohere(screenshot_path, viewport, page_url, verbose)


async def _analyze_with_gemini(
    screenshot_path: str, 
    viewport: str, 
    page_url: str,
    verbose: bool = False
) -> Tuple[List[Bug], Optional[str]]:
    """Analyze screenshot using Gemini model"""
    try:
        from .gemini_analyzer import analyze_screenshot as gemini_analyze
        return await gemini_analyze(screenshot_path, viewport, page_url, verbose)
    except ImportError as e:
        return [], f"Gemini analyzer not available: {str(e)}"
    except Exception as e:
        return [], f"Gemini analysis error: {str(e)}"


async def _analyze_with_cohere(
    screenshot_path: str, 
    viewport: str, 
    page_url: str,
    verbose: bool = False
) -> Tuple[List[Bug], Optional[str]]:
    """Analyze screenshot using Cohere model"""
    try:
        from .cohere_analyzer import analyze_screenshot as cohere_analyze
        
        # Check if input is a file path and convert to base64 if needed
        if os.path.exists(screenshot_path):
            # It's a file path - convert to base64
            try:
                with open(screenshot_path, "rb") as image_file:
                    image_data = base64.b64encode(image_file.read()).decode('utf-8')
            except Exception as e:
                return [], f"Failed to read image file: {str(e)}"
        else:
            # Assume it's already base64 data
            image_data = screenshot_path
        
        # Cohere analyzer expects base64 image data, viewport description, and URL
        viewport_desc = f"viewport {viewport}"
        bugs, error = await cohere_analyze(image_data, viewport_desc, page_url, verbose)
        return bugs, error if error else None
        
    except ImportError as e:
        return [], f"Cohere analyzer not available: {str(e)}"
    except Exception as e:
        return [], f"Cohere analysis error: {str(e)}"


def get_supported_models() -> List[str]:
    """Get list of supported models"""
    return ['cohere', 'gemini']


def is_model_available(model: str) -> bool:
    """Check if a specific model is available"""
    if model.lower() == 'gemini':
        try:
            import google.generativeai
            return True
        except ImportError:
            return False
    elif model.lower() == 'cohere':
        try:
            import cohere
            return True
        except ImportError:
            return False
    return False
