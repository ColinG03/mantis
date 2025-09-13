"""
Pytest configuration and shared fixtures for the test suite.
"""
import os
import sys
import tempfile
import base64
import pytest
from pathlib import Path

# Add the src directory to the path for imports
test_dir = Path(__file__).parent
src_dir = test_dir.parent
sys.path.insert(0, str(src_dir))


@pytest.fixture(scope="session")
def test_image_1x1_png():
    """
    Creates a minimal 1x1 PNG image for testing.
    This is a session-scoped fixture that creates the file once and reuses it.
    """
    # Minimal 1x1 transparent PNG in base64
    png_data = base64.b64decode(
        'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=='
    )
    
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
        tmp_file.write(png_data)
        tmp_file.flush()
        yield tmp_file.name
    
    # Cleanup after session
    try:
        os.unlink(tmp_file.name)
    except OSError:
        pass


@pytest.fixture
def temp_image_file():
    """
    Creates a temporary image file for a single test.
    Use this when you need to modify the image or test file-specific operations.
    """
    png_data = base64.b64decode(
        'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=='
    )
    
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
        tmp_file.write(png_data)
        tmp_file.flush()
        yield tmp_file.name
    
    # Cleanup after test
    try:
        os.unlink(tmp_file.name)
    except OSError:
        pass


@pytest.fixture
def sample_gemini_responses():
    """Sample responses that Gemini might return"""
    return {
        'valid_bugs': '''[
            {
                "summary": "Header text overflows container on mobile",
                "severity": "high", 
                "suggested_fix": "Add responsive text wrapping"
            },
            {
                "summary": "Button overlaps footer content",
                "severity": "medium",
                "suggested_fix": "Adjust button positioning and z-index"
            }
        ]''',
        
        'no_bugs': '[]',
        
        'single_bug': '''[
            {
                "summary": "Navigation menu cuts off on small screens",
                "severity": "critical",
                "suggested_fix": "Implement hamburger menu for mobile"
            }
        ]''',
        
        'minimal_bug': '''[
            {
                "summary": "Layout issue detected"
            }
        ]''',
        
        'with_markdown': '''```json
[
    {
        "summary": "Dropdown extends beyond viewport",
        "severity": "medium"
    }
]
```''',
        
        'malformed_json': '{"incomplete": json',
        
        'not_array': '{"error": "This is not an array"}',
        
        'empty_response': '',
        
        'whitespace_only': '   \n\t   ',
    }


@pytest.fixture
def mock_environment_variables():
    """Context manager for mocking environment variables"""
    class EnvVarMocker:
        def __init__(self):
            self.original_env = {}
        
        def set(self, **kwargs):
            """Set environment variables, storing originals for restoration"""
            for key, value in kwargs.items():
                if key in os.environ:
                    self.original_env[key] = os.environ[key]
                else:
                    self.original_env[key] = None
                os.environ[key] = value
        
        def clear(self, *keys):
            """Clear specific environment variables"""
            for key in keys:
                if key in os.environ:
                    self.original_env[key] = os.environ[key]
                    del os.environ[key]
                else:
                    self.original_env[key] = None
        
        def restore(self):
            """Restore original environment variables"""
            for key, value in self.original_env.items():
                if value is None:
                    if key in os.environ:
                        del os.environ[key]
                else:
                    os.environ[key] = value
            self.original_env.clear()
    
    mocker = EnvVarMocker()
    yield mocker
    mocker.restore()


@pytest.fixture
def sample_test_contexts():
    """Sample context strings for testing"""
    return [
        "baseline view",
        "after clicking Home dropdown",
        "after filling contact form with long text",
        "after opening mobile navigation menu",
        "after form submission",
        "after modal dialog opened",
        "after accordion expanded",
        "viewport change to mobile",
        "after page scroll",
        "after keyboard navigation"
    ]


@pytest.fixture
def sample_viewports():
    """Sample viewport configurations for testing"""
    return [
        "1920x1080",  # Large desktop
        "1280x800",   # Standard desktop
        "768x1024",   # Tablet
        "375x667",    # Mobile
        "320x568",    # Small mobile
        "1440x900",   # Laptop
        "2560x1440",  # High-res desktop
    ]


@pytest.fixture
def sample_page_urls():
    """Sample page URLs for testing"""
    return [
        "https://example.com",
        "https://test-site.com/products",
        "https://ecommerce.com/checkout",
        "https://blog.example.com/article/123",
        "https://app.test.com/dashboard",
        "https://mobile.site.com/menu",
        "http://localhost:3000/dev",
        "https://staging.myapp.com/forms",
    ]
