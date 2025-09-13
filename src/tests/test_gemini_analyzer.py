import os
import json
import pytest
import asyncio
import tempfile
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from pathlib import Path
import base64

# Add the src directory to the path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from inspector.utils.gemini_analyzer import GeminiAnalyzer, analyze_screenshot
from core.types import Bug, Evidence


class TestGeminiAnalyzer:
    """Test suite for GeminiAnalyzer class"""
    
    @pytest.fixture
    def mock_api_key(self):
        """Mock API key for testing"""
        return "test_gemini_api_key_12345"
    
    @pytest.fixture
    def mock_genai(self):
        """Mock the google.generativeai module"""
        with patch('inspector.utils.gemini_analyzer.genai') as mock_genai:
            mock_model = Mock()
            mock_genai.GenerativeModel.return_value = mock_model
            yield mock_genai, mock_model
    
    @pytest.fixture
    def sample_image_path(self):
        """Create a temporary image file for testing"""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            # Create a simple 1x1 PNG (minimal valid PNG data)
            png_data = base64.b64decode(
                'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=='
            )
            tmp_file.write(png_data)
            tmp_file.flush()
            yield tmp_file.name
        os.unlink(tmp_file.name)
    
    @pytest.fixture
    def sample_bug_response(self):
        """Sample valid JSON response from Gemini"""
        return json.dumps([
            {
                "summary": "Header text overflows container on mobile viewport",
                "severity": "high",
                "suggested_fix": "Add text wrapping or responsive font sizing"
            },
            {
                "summary": "Dropdown menu extends beyond screen boundaries", 
                "severity": "medium",
                "suggested_fix": "Implement dropdown position detection"
            }
        ])
    
    def test_init_with_api_key(self, mock_genai, mock_api_key):
        """Test GeminiAnalyzer initialization with API key"""
        mock_genai_module, mock_model = mock_genai
        
        analyzer = GeminiAnalyzer(api_key=mock_api_key)
        
        assert analyzer.api_key == mock_api_key
        mock_genai_module.configure.assert_called_once_with(api_key=mock_api_key)
        mock_genai_module.GenerativeModel.assert_called_once_with('gemini-2.0-flash-exp')
        assert analyzer.model == mock_model
    
    @patch.dict(os.environ, {'GEMINI_API_KEY': 'env_api_key'})
    def test_init_with_env_var(self, mock_genai):
        """Test GeminiAnalyzer initialization with environment variable"""
        mock_genai_module, mock_model = mock_genai
        
        analyzer = GeminiAnalyzer()
        
        assert analyzer.api_key == 'env_api_key'
        mock_genai_module.configure.assert_called_once_with(api_key='env_api_key')
    
    def test_init_no_api_key_raises_error(self, mock_genai):
        """Test that missing API key raises ValueError"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Gemini API key is required"):
                GeminiAnalyzer()
    
    @patch('inspector.utils.gemini_analyzer.genai', None)
    def test_init_no_genai_module_raises_error(self):
        """Test that missing genai module raises ImportError"""
        with pytest.raises(ImportError, match="google-generativeai package is required"):
            GeminiAnalyzer(api_key="test_key")
    
    def test_encode_image_success(self, mock_genai, mock_api_key, sample_image_path):
        """Test successful image encoding"""
        analyzer = GeminiAnalyzer(api_key=mock_api_key)
        
        encoded = analyzer._encode_image(sample_image_path)
        
        assert isinstance(encoded, str)
        assert len(encoded) > 0
        # Verify it's valid base64
        base64.b64decode(encoded)
    
    def test_encode_image_file_not_found(self, mock_genai, mock_api_key):
        """Test image encoding with non-existent file"""
        analyzer = GeminiAnalyzer(api_key=mock_api_key)
        
        with pytest.raises(ValueError, match="Failed to encode image"):
            analyzer._encode_image("nonexistent_file.png")
    
    def test_create_analysis_prompt(self, mock_genai, mock_api_key):
        """Test analysis prompt creation"""
        analyzer = GeminiAnalyzer(api_key=mock_api_key)
        
        prompt = analyzer._create_analysis_prompt(
            context="after clicking dropdown",
            viewport="1280x800", 
            page_url="https://example.com"
        )
        
        assert "after clicking dropdown" in prompt
        assert "1280x800" in prompt
        assert "https://example.com" in prompt
        assert "Visual Layout Problems" in prompt
        assert "JSON array" in prompt
    
    def test_parse_gemini_response_valid_json(self, mock_genai, mock_api_key, sample_bug_response):
        """Test parsing valid JSON response from Gemini"""
        analyzer = GeminiAnalyzer(api_key=mock_api_key)
        
        bugs = analyzer._parse_gemini_response(
            response_text=sample_bug_response,
            page_url="https://example.com",
            screenshot_path="/path/to/screenshot.png",
            viewport="1280x800"
        )
        
        assert len(bugs) == 2
        assert all(isinstance(bug, Bug) for bug in bugs)
        assert bugs[0].summary == "Header text overflows container on mobile viewport"
        assert bugs[0].severity == "high"
        assert bugs[0].type == "UI"
        assert bugs[0].page_url == "https://example.com"
        assert bugs[0].evidence.screenshot_path == "/path/to/screenshot.png"
        assert bugs[0].evidence.viewport == "1280x800"
    
    def test_parse_gemini_response_with_markdown(self, mock_genai, mock_api_key):
        """Test parsing response with markdown formatting"""
        analyzer = GeminiAnalyzer(api_key=mock_api_key)
        
        markdown_response = """```json
[
    {
        "summary": "Test issue",
        "severity": "medium"
    }
]
```"""
        
        bugs = analyzer._parse_gemini_response(
            response_text=markdown_response,
            page_url="https://example.com", 
            screenshot_path="/path/to/screenshot.png",
            viewport="1280x800"
        )
        
        assert len(bugs) == 1
        assert bugs[0].summary == "Test issue"
        assert bugs[0].severity == "medium"
    
    def test_parse_gemini_response_empty_array(self, mock_genai, mock_api_key):
        """Test parsing empty array response"""
        analyzer = GeminiAnalyzer(api_key=mock_api_key)
        
        bugs = analyzer._parse_gemini_response(
            response_text="[]",
            page_url="https://example.com",
            screenshot_path="/path/to/screenshot.png", 
            viewport="1280x800"
        )
        
        assert len(bugs) == 0
        assert isinstance(bugs, list)
    
    def test_parse_gemini_response_invalid_json(self, mock_genai, mock_api_key):
        """Test parsing invalid JSON response"""
        analyzer = GeminiAnalyzer(api_key=mock_api_key)
        
        bugs = analyzer._parse_gemini_response(
            response_text="invalid json {",
            page_url="https://example.com",
            screenshot_path="/path/to/screenshot.png",
            viewport="1280x800"
        )
        
        assert len(bugs) == 0
    
    def test_parse_gemini_response_non_list(self, mock_genai, mock_api_key):
        """Test parsing response that's not a list"""
        analyzer = GeminiAnalyzer(api_key=mock_api_key)
        
        bugs = analyzer._parse_gemini_response(
            response_text='{"error": "not a list"}',
            page_url="https://example.com",
            screenshot_path="/path/to/screenshot.png",
            viewport="1280x800"
        )
        
        assert len(bugs) == 0
    
    @pytest.mark.asyncio
    async def test_analyze_screenshot_success(self, mock_genai, mock_api_key, sample_image_path, sample_bug_response):
        """Test successful screenshot analysis"""
        mock_genai_module, mock_model = mock_genai
        
        # Mock the API response
        mock_response = Mock()
        mock_response.text = sample_bug_response
        mock_model.generate_content = Mock(return_value=mock_response)
        
        analyzer = GeminiAnalyzer(api_key=mock_api_key)
        
        with patch('asyncio.to_thread', return_value=mock_response):
            bugs, error = await analyzer.analyze_screenshot(
                screenshot_path=sample_image_path,
                context="baseline view",
                viewport="1280x800",
                page_url="https://example.com"
            )
        
        assert error is None
        assert len(bugs) == 2
        assert bugs[0].summary == "Header text overflows container on mobile viewport"
    
    @pytest.mark.asyncio
    async def test_analyze_screenshot_file_not_found(self, mock_genai, mock_api_key):
        """Test screenshot analysis with non-existent file"""
        analyzer = GeminiAnalyzer(api_key=mock_api_key)
        
        bugs, error = await analyzer.analyze_screenshot(
            screenshot_path="nonexistent.png",
            context="baseline view",
            viewport="1280x800", 
            page_url="https://example.com"
        )
        
        assert bugs == []
        assert "Screenshot file not found" in error
    
    @pytest.mark.asyncio
    async def test_analyze_screenshot_api_timeout(self, mock_genai, mock_api_key, sample_image_path):
        """Test screenshot analysis with API timeout"""
        analyzer = GeminiAnalyzer(api_key=mock_api_key)
        
        with patch('asyncio.wait_for', side_effect=asyncio.TimeoutError()):
            bugs, error = await analyzer.analyze_screenshot(
                screenshot_path=sample_image_path,
                context="baseline view",
                viewport="1280x800",
                page_url="https://example.com"
            )
        
        assert bugs == []
        assert "Gemini API timeout after 30 seconds" in error
    
    @pytest.mark.asyncio
    async def test_analyze_screenshot_api_error(self, mock_genai, mock_api_key, sample_image_path):
        """Test screenshot analysis with API error"""
        mock_genai_module, mock_model = mock_genai
        mock_model.generate_content = Mock(side_effect=Exception("API Error"))
        
        analyzer = GeminiAnalyzer(api_key=mock_api_key)
        
        with patch('asyncio.to_thread', side_effect=Exception("API Error")):
            bugs, error = await analyzer.analyze_screenshot(
                screenshot_path=sample_image_path,
                context="baseline view", 
                viewport="1280x800",
                page_url="https://example.com"
            )
        
        assert bugs == []
        assert "Gemini API error" in error
    
    @pytest.mark.asyncio
    async def test_analyze_screenshot_empty_response(self, mock_genai, mock_api_key, sample_image_path):
        """Test screenshot analysis with empty API response"""
        mock_genai_module, mock_model = mock_genai
        
        mock_response = Mock()
        mock_response.text = None
        mock_model.generate_content = Mock(return_value=mock_response)
        
        analyzer = GeminiAnalyzer(api_key=mock_api_key)
        
        with patch('asyncio.to_thread', return_value=mock_response):
            bugs, error = await analyzer.analyze_screenshot(
                screenshot_path=sample_image_path,
                context="baseline view",
                viewport="1280x800",
                page_url="https://example.com"
            )
        
        assert bugs == []
        assert "Gemini API returned empty response" in error


class TestConvenienceFunction:
    """Test suite for the convenience analyze_screenshot function"""
    
    @pytest.fixture
    def sample_image_path(self):
        """Create a temporary image file for testing"""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            png_data = base64.b64decode(
                'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=='
            )
            tmp_file.write(png_data)
            tmp_file.flush()
            yield tmp_file.name
        os.unlink(tmp_file.name)
    
    @pytest.mark.asyncio
    async def test_convenience_function_success(self, sample_image_path):
        """Test the convenience function with successful analysis"""
        with patch('inspector.utils.gemini_analyzer.GeminiAnalyzer') as mock_analyzer_class:
            mock_analyzer = Mock()
            mock_analyzer.analyze_screenshot = AsyncMock(return_value=([], None))
            mock_analyzer_class.return_value = mock_analyzer
            
            bugs, error = await analyze_screenshot(
                screenshot_path=sample_image_path,
                context="baseline view",
                viewport="1280x800",
                page_url="https://example.com"
            )
            
            assert bugs == []
            assert error is None
            mock_analyzer.analyze_screenshot.assert_called_once_with(
                sample_image_path, "baseline view", "1280x800", "https://example.com"
            )
    
    @pytest.mark.asyncio
    async def test_convenience_function_initialization_error(self, sample_image_path):
        """Test the convenience function with analyzer initialization error"""
        with patch('inspector.utils.gemini_analyzer.GeminiAnalyzer', side_effect=ValueError("No API key")):
            bugs, error = await analyze_screenshot(
                screenshot_path=sample_image_path,
                context="baseline view",
                viewport="1280x800", 
                page_url="https://example.com"
            )
            
            assert bugs == []
            assert "Failed to initialize Gemini analyzer" in error
            assert "No API key" in error


class TestGeminiAnalyzerIntegration:
    """Integration tests that test multiple components together"""
    
    @pytest.fixture
    def sample_image_path(self):
        """Create a temporary image file for testing"""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            png_data = base64.b64decode(
                'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=='
            )
            tmp_file.write(png_data)
            tmp_file.flush()
            yield tmp_file.name
        os.unlink(tmp_file.name)
    
    @pytest.mark.asyncio
    async def test_full_workflow_with_mock_api(self, sample_image_path):
        """Test the complete workflow from image to Bug objects"""
        mock_response_data = [
            {
                "summary": "Integration test bug",
                "severity": "critical",
                "suggested_fix": "Fix the integration issue"
            }
        ]
        
        with patch('inspector.utils.gemini_analyzer.genai') as mock_genai:
            # Setup mock
            mock_model = Mock()
            mock_genai.GenerativeModel.return_value = mock_model
            
            mock_response = Mock()
            mock_response.text = json.dumps(mock_response_data)
            
            with patch('asyncio.to_thread', return_value=mock_response):
                analyzer = GeminiAnalyzer(api_key="test_key")
                bugs, error = await analyzer.analyze_screenshot(
                    screenshot_path=sample_image_path,
                    context="after form submission",
                    viewport="375x667",
                    page_url="https://test-site.com/form"
                )
            
            assert error is None
            assert len(bugs) == 1
            
            bug = bugs[0]
            assert bug.summary == "Integration test bug"
            assert bug.severity == "critical"
            assert bug.suggested_fix == "Fix the integration issue"
            assert bug.type == "UI"
            assert bug.page_url == "https://test-site.com/form"
            assert bug.evidence.screenshot_path == sample_image_path
            assert bug.evidence.viewport == "375x667"
            assert bug.id is not None  # UUID should be generated
    
    def test_prompt_generation_with_real_data(self):
        """Test prompt generation with realistic data"""
        with patch('inspector.utils.gemini_analyzer.genai') as mock_genai:
            mock_genai.GenerativeModel.return_value = Mock()
            
            analyzer = GeminiAnalyzer(api_key="test_key")
            prompt = analyzer._create_analysis_prompt(
                context="after clicking 'Show More' button on mobile device",
                viewport="375x667",
                page_url="https://ecommerce-site.com/products"
            )
            
            # Verify key components are in the prompt
            assert "after clicking 'Show More' button on mobile device" in prompt
            assert "375x667" in prompt
            assert "https://ecommerce-site.com/products" in prompt
            
            # Verify it contains bug detection instructions
            assert "Text overflow or cutoff" in prompt
            assert "Elements overlapping inappropriately" in prompt
            assert "Broken responsive design" in prompt
            
            # Verify it has the expected response format
            assert "JSON array" in prompt
            assert '"summary"' in prompt
            assert '"severity"' in prompt
            assert '"suggested_fix"' in prompt


class TestErrorHandling:
    """Test various error conditions and edge cases"""
    
    def test_malformed_json_responses(self):
        """Test handling of various malformed JSON responses"""
        with patch('inspector.utils.gemini_analyzer.genai') as mock_genai:
            mock_genai.GenerativeModel.return_value = Mock()
            analyzer = GeminiAnalyzer(api_key="test_key")
            
            test_cases = [
                "Not JSON at all",
                '{"incomplete": json',
                '["missing", "closing bracket"',
                "null",
                "undefined",
                '{"not": "a list"}',
                "",
                "   ",
            ]
            
            for malformed_json in test_cases:
                bugs = analyzer._parse_gemini_response(
                    response_text=malformed_json,
                    page_url="https://example.com",
                    screenshot_path="/test.png",
                    viewport="1280x800"
                )
                assert bugs == [], f"Expected empty list for: {malformed_json}"
    
    def test_missing_required_fields_in_response(self):
        """Test handling of responses missing required fields"""
        with patch('inspector.utils.gemini_analyzer.genai') as mock_genai:
            mock_genai.GenerativeModel.return_value = Mock()
            analyzer = GeminiAnalyzer(api_key="test_key")
            
            # Response with missing summary
            response_data = json.dumps([
                {"severity": "high", "suggested_fix": "Fix it"}
            ])
            
            bugs = analyzer._parse_gemini_response(
                response_text=response_data,
                page_url="https://example.com",
                screenshot_path="/test.png",
                viewport="1280x800"
            )
            
            assert len(bugs) == 1
            assert bugs[0].summary == "Visual layout issue detected"  # Default value
            assert bugs[0].severity == "high"
    
    def test_invalid_severity_values(self):
        """Test handling of invalid severity values"""
        with patch('inspector.utils.gemini_analyzer.genai') as mock_genai:
            mock_genai.GenerativeModel.return_value = Mock()
            analyzer = GeminiAnalyzer(api_key="test_key")
            
            response_data = json.dumps([
                {"summary": "Test bug", "severity": "invalid_severity"}
            ])
            
            bugs = analyzer._parse_gemini_response(
                response_text=response_data,
                page_url="https://example.com",
                screenshot_path="/test.png",
                viewport="1280x800"
            )
            
            assert len(bugs) == 1
            assert bugs[0].severity == "invalid_severity"  # Preserved as-is for Bug validation


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
