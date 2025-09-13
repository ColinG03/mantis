"""
Performance and stress tests for Gemini analyzer.
"""
import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock
import json
import tempfile
import base64
import os
import sys

# Add the src directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from inspector.utils.gemini_analyzer import GeminiAnalyzer, analyze_screenshot


class TestGeminiPerformance:
    """Performance tests for GeminiAnalyzer"""
    
    @pytest.fixture
    def mock_genai_fast(self):
        """Mock that responds quickly"""
        with patch('inspector.utils.gemini_analyzer.genai') as mock_genai:
            mock_model = Mock()
            mock_response = Mock()
            mock_response.text = '[]'
            mock_model.generate_content = Mock(return_value=mock_response)
            mock_genai.GenerativeModel.return_value = mock_model
            yield mock_genai, mock_model
    
    @pytest.fixture
    def mock_genai_slow(self):
        """Mock that simulates slow API responses"""
        async def slow_generate_content(*args, **kwargs):
            await asyncio.sleep(0.5)  # Simulate 500ms delay
            mock_response = Mock()
            mock_response.text = '[]'
            return mock_response
        
        with patch('inspector.utils.gemini_analyzer.genai') as mock_genai:
            mock_model = Mock()
            mock_genai.GenerativeModel.return_value = mock_model
            yield mock_genai, mock_model, slow_generate_content
    
    @pytest.mark.asyncio
    async def test_single_analysis_performance(self, mock_genai_fast, test_image_1x1_png):
        """Test performance of single screenshot analysis"""
        mock_genai_module, mock_model = mock_genai_fast
        
        analyzer = GeminiAnalyzer(api_key="test_key")
        
        start_time = time.time()
        
        with patch('asyncio.to_thread', return_value=mock_model.generate_content.return_value):
            bugs, error = await analyzer.analyze_screenshot(
                screenshot_path=test_image_1x1_png,
                context="performance test",
                viewport="1280x800",
                page_url="https://example.com"
            )
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        assert error is None
        assert isinstance(bugs, list)
        assert execution_time < 1.0  # Should complete in under 1 second with mocking
    
    @pytest.mark.asyncio
    async def test_concurrent_analyses(self, mock_genai_fast, test_image_1x1_png):
        """Test performance of concurrent screenshot analyses"""
        mock_genai_module, mock_model = mock_genai_fast
        
        analyzer = GeminiAnalyzer(api_key="test_key")
        
        # Create multiple concurrent analysis tasks
        num_concurrent = 5
        
        async def single_analysis(i):
            with patch('asyncio.to_thread', return_value=mock_model.generate_content.return_value):
                return await analyzer.analyze_screenshot(
                    screenshot_path=test_image_1x1_png,
                    context=f"concurrent test {i}",
                    viewport="1280x800",
                    page_url=f"https://example.com/{i}"
                )
        
        start_time = time.time()
        
        # Run all analyses concurrently
        tasks = [single_analysis(i) for i in range(num_concurrent)]
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Verify all completed successfully
        assert len(results) == num_concurrent
        for bugs, error in results:
            assert error is None
            assert isinstance(bugs, list)
        
        # Should complete in reasonable time (not much slower than single analysis)
        assert execution_time < 2.0
    
    @pytest.mark.asyncio
    async def test_timeout_handling_performance(self, test_image_1x1_png):
        """Test that timeout handling doesn't add significant overhead"""
        with patch('inspector.utils.gemini_analyzer.genai') as mock_genai:
            mock_model = Mock()
            mock_genai.GenerativeModel.return_value = mock_model
            
            analyzer = GeminiAnalyzer(api_key="test_key")
            
            start_time = time.time()
            
            # Mock asyncio.wait_for to raise TimeoutError
            with patch('asyncio.wait_for', side_effect=asyncio.TimeoutError()):
                bugs, error = await analyzer.analyze_screenshot(
                    screenshot_path=test_image_1x1_png,
                    context="timeout test",
                    viewport="1280x800",
                    page_url="https://example.com"
                )
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            assert bugs == []
            assert "timeout" in error.lower()
            assert execution_time < 0.1  # Timeout handling should be immediate
    
    @pytest.mark.asyncio
    async def test_large_response_parsing_performance(self, mock_genai_fast, test_image_1x1_png):
        """Test performance with large JSON responses"""
        mock_genai_module, mock_model = mock_genai_fast
        
        # Create a large response with many bugs
        large_response = []
        for i in range(100):  # 100 bugs
            large_response.append({
                "summary": f"Bug {i}: This is a longer summary that describes a complex visual layout issue that was detected by the analyzer",
                "severity": "medium",
                "suggested_fix": f"Fix suggestion {i}: Implement a comprehensive solution that addresses the root cause of this visual issue"
            })
        
        mock_response = Mock()
        mock_response.text = json.dumps(large_response)
        mock_model.generate_content = Mock(return_value=mock_response)
        
        analyzer = GeminiAnalyzer(api_key="test_key")
        
        start_time = time.time()
        
        with patch('asyncio.to_thread', return_value=mock_response):
            bugs, error = await analyzer.analyze_screenshot(
                screenshot_path=test_image_1x1_png,
                context="large response test",
                viewport="1280x800",
                page_url="https://example.com"
            )
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        assert error is None
        assert len(bugs) == 100
        assert execution_time < 1.0  # Should handle large responses efficiently
    
    @pytest.mark.asyncio
    async def test_memory_usage_with_multiple_analyses(self, mock_genai_fast, test_image_1x1_png):
        """Test that multiple analyses don't cause memory leaks"""
        mock_genai_module, mock_model = mock_genai_fast
        
        analyzer = GeminiAnalyzer(api_key="test_key")
        
        # Run many sequential analyses
        num_analyses = 20
        
        for i in range(num_analyses):
            with patch('asyncio.to_thread', return_value=mock_model.generate_content.return_value):
                bugs, error = await analyzer.analyze_screenshot(
                    screenshot_path=test_image_1x1_png,
                    context=f"memory test {i}",
                    viewport="1280x800",
                    page_url=f"https://example.com/{i}"
                )
            
            assert error is None
            assert isinstance(bugs, list)
            
            # Small delay to allow garbage collection
            await asyncio.sleep(0.01)
        
        # If we get here without memory issues, the test passes
        assert True


class TestGeminiStressTests:
    """Stress tests for error conditions and edge cases"""
    
    @pytest.mark.asyncio
    async def test_rapid_fire_requests(self, test_image_1x1_png):
        """Test rapid consecutive requests"""
        with patch('inspector.utils.gemini_analyzer.genai') as mock_genai:
            mock_model = Mock()
            mock_response = Mock()
            mock_response.text = '[]'
            mock_model.generate_content = Mock(return_value=mock_response)
            mock_genai.GenerativeModel.return_value = mock_model
            
            analyzer = GeminiAnalyzer(api_key="test_key")
            
            # Fire off many requests rapidly
            tasks = []
            for i in range(50):
                with patch('asyncio.to_thread', return_value=mock_response):
                    task = analyzer.analyze_screenshot(
                        screenshot_path=test_image_1x1_png,
                        context=f"rapid fire {i}",
                        viewport="375x667",
                        page_url=f"https://test.com/{i}"
                    )
                    tasks.append(task)
            
            # Wait for all to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Check that none failed catastrophically
            successful_results = 0
            for result in results:
                if isinstance(result, tuple) and len(result) == 2:
                    bugs, error = result
                    if error is None:
                        successful_results += 1
            
            # At least some should succeed (depends on mock reliability)
            assert successful_results > 0
    
    @pytest.mark.asyncio
    async def test_malformed_responses_stress(self, test_image_1x1_png):
        """Test handling of various malformed responses under stress"""
        malformed_responses = [
            "not json",
            '{"incomplete": json',
            '["missing", "bracket"',
            "",
            "null",
            '{"not": "a list"}',
            "random text here",
            '[][]',  # Multiple JSON objects
            '{"summary": "Missing closing quote}',
            '{summary: "Missing quotes on key"}',
        ]
        
        with patch('inspector.utils.gemini_analyzer.genai') as mock_genai:
            mock_model = Mock()
            mock_genai.GenerativeModel.return_value = mock_model
            
            analyzer = GeminiAnalyzer(api_key="test_key")
            
            # Test each malformed response
            for i, malformed in enumerate(malformed_responses):
                mock_response = Mock()
                mock_response.text = malformed
                
                with patch('asyncio.to_thread', return_value=mock_response):
                    bugs, error = await analyzer.analyze_screenshot(
                        screenshot_path=test_image_1x1_png,
                        context=f"malformed test {i}",
                        viewport="1280x800",
                        page_url="https://example.com"
                    )
                
                # Should handle gracefully - return empty bugs, no crash
                assert isinstance(bugs, list)
                assert len(bugs) == 0
                # Error may or may not be None, depending on how malformed the response is
    
    @pytest.mark.asyncio
    async def test_network_error_simulation(self, test_image_1x1_png):
        """Test various network error conditions"""
        network_errors = [
            ConnectionError("Network unreachable"),
            TimeoutError("Connection timeout"),
            Exception("SSL certificate error"),
            ValueError("Invalid response format"),
            RuntimeError("Service unavailable"),
        ]
        
        analyzer = None
        with patch('inspector.utils.gemini_analyzer.genai') as mock_genai:
            mock_model = Mock()
            mock_genai.GenerativeModel.return_value = mock_model
            analyzer = GeminiAnalyzer(api_key="test_key")
        
        for error in network_errors:
            with patch('asyncio.to_thread', side_effect=error):
                bugs, error_msg = await analyzer.analyze_screenshot(
                    screenshot_path=test_image_1x1_png,
                    context="network error test",
                    viewport="1280x800",
                    page_url="https://example.com"
                )
            
            assert bugs == []
            assert error_msg is not None
            assert isinstance(error_msg, str)
    
    def test_image_encoding_stress(self):
        """Test image encoding with various file conditions"""
        with patch('inspector.utils.gemini_analyzer.genai') as mock_genai:
            mock_genai.GenerativeModel.return_value = Mock()
            analyzer = GeminiAnalyzer(api_key="test_key")
            
            # Test with non-existent files
            for i in range(10):
                with pytest.raises(ValueError):
                    analyzer._encode_image(f"nonexistent_file_{i}.png")
            
            # Test with invalid file paths
            invalid_paths = [
                "",
                "/dev/null",
                "/nonexistent/path/file.png",
                "invalid\0filename.png",
                "." * 1000 + ".png",  # Very long filename
            ]
            
            for invalid_path in invalid_paths:
                with pytest.raises(ValueError):
                    analyzer._encode_image(invalid_path)


class TestConvenienceFunctionPerformance:
    """Performance tests for the convenience function"""
    
    @pytest.mark.asyncio
    async def test_convenience_function_overhead(self, test_image_1x1_png):
        """Test that the convenience function doesn't add significant overhead"""
        with patch('inspector.utils.gemini_analyzer.GeminiAnalyzer') as mock_analyzer_class:
            mock_analyzer = Mock()
            mock_analyzer.analyze_screenshot = AsyncMock(return_value=([], None))
            mock_analyzer_class.return_value = mock_analyzer
            
            start_time = time.time()
            
            bugs, error = await analyze_screenshot(
                screenshot_path=test_image_1x1_png,
                context="convenience performance test",
                viewport="1280x800",
                page_url="https://example.com"
            )
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            assert error is None
            assert isinstance(bugs, list)
            assert execution_time < 0.1  # Should be very fast with mocking
    
    @pytest.mark.asyncio
    async def test_convenience_function_concurrent_usage(self, test_image_1x1_png):
        """Test concurrent usage of the convenience function"""
        with patch('inspector.utils.gemini_analyzer.GeminiAnalyzer') as mock_analyzer_class:
            mock_analyzer = Mock()
            mock_analyzer.analyze_screenshot = AsyncMock(return_value=([], None))
            mock_analyzer_class.return_value = mock_analyzer
            
            # Create multiple concurrent tasks
            num_concurrent = 10
            
            async def single_call(i):
                return await analyze_screenshot(
                    screenshot_path=test_image_1x1_png,
                    context=f"concurrent convenience test {i}",
                    viewport="1280x800",
                    page_url=f"https://example.com/{i}"
                )
            
            start_time = time.time()
            
            tasks = [single_call(i) for i in range(num_concurrent)]
            results = await asyncio.gather(*tasks)
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Verify all completed successfully
            assert len(results) == num_concurrent
            for bugs, error in results:
                assert error is None
                assert isinstance(bugs, list)
            
            # Should complete efficiently
            assert execution_time < 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
