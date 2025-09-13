# Gemini Analyzer Tests

This directory contains comprehensive tests for the Gemini analyzer functionality.

## Test Structure

### Core Test Files

- **`test_gemini_analyzer.py`** - Main unit and integration tests
- **`test_gemini_performance.py`** - Performance and stress tests  
- **`conftest.py`** - Shared fixtures and test configuration

### Test Categories

#### Unit Tests (`test_gemini_analyzer.py`)

1. **Initialization Tests**
   - API key validation
   - Environment variable handling
   - Module dependency checks

2. **Image Processing Tests**
   - Image encoding/decoding
   - File validation
   - Error handling for missing files

3. **Response Parsing Tests**
   - Valid JSON parsing
   - Malformed JSON handling
   - Edge cases and error conditions

4. **Prompt Generation Tests**
   - Context integration
   - Viewport formatting
   - URL handling

5. **Integration Tests**
   - End-to-end workflow simulation
   - API call mocking
   - Error propagation

#### Performance Tests (`test_gemini_performance.py`)

1. **Single Analysis Performance**
   - Response time validation
   - Memory usage monitoring

2. **Concurrent Analysis Tests**
   - Multiple simultaneous requests
   - Resource contention handling

3. **Stress Tests**
   - Rapid-fire requests
   - Malformed response handling
   - Network error simulation

4. **Timeout Handling**
   - API timeout behavior
   - Graceful degradation

## Running Tests

### Basic Test Run
```bash
# Run all Gemini analyzer tests
python run_gemini_tests.py

# Run with verbose output
python run_gemini_tests.py -v

# Run specific test pattern
python run_gemini_tests.py -k "test_init"
```

### Advanced Options
```bash
# Run with coverage reporting
python run_gemini_tests.py --coverage

# Include performance tests (slower)
python run_gemini_tests.py --performance

# Quick run (unit tests only)
python run_gemini_tests.py --quick
```

### Direct Pytest Usage
```bash
# Run specific test file
pytest src/tests/test_gemini_analyzer.py -v

# Run with coverage
pytest src/tests/test_gemini_analyzer.py --cov=src/inspector/utils/gemini_analyzer

# Run specific test class
pytest src/tests/test_gemini_analyzer.py::TestGeminiAnalyzer -v

# Run specific test method
pytest src/tests/test_gemini_analyzer.py::TestGeminiAnalyzer::test_init_with_api_key -v
```

## Test Fixtures

### Image Fixtures
- `test_image_1x1_png` - Session-scoped minimal PNG for testing
- `temp_image_file` - Function-scoped temporary image file

### Mock Data Fixtures
- `sample_gemini_responses` - Various API response scenarios
- `sample_test_contexts` - Different analysis contexts
- `sample_viewports` - Common viewport configurations
- `sample_page_urls` - Test URLs for different scenarios

### Environment Fixtures
- `mock_environment_variables` - Environment variable management
- `mock_genai` - Mocked Google AI API

## Test Coverage

The test suite covers:

### ✅ Functionality Coverage
- API key validation and configuration
- Image encoding and validation
- JSON response parsing and validation
- Error handling and edge cases
- Convenience function wrapper
- Bug object creation and validation

### ✅ Error Scenarios
- Missing API keys
- Invalid image files
- Malformed JSON responses
- Network timeouts and errors
- Missing dependencies
- Invalid parameters

### ✅ Performance Scenarios
- Single analysis timing
- Concurrent request handling
- Large response processing
- Memory usage patterns
- Timeout behavior

## Mock Strategy

### API Mocking
The tests use comprehensive mocking to avoid actual API calls:

- **`google.generativeai`** module is mocked
- **API responses** are simulated with various scenarios
- **Network errors** are simulated for error handling tests
- **Timeouts** are simulated for performance tests

### File System Mocking
- Temporary files are created for valid scenarios
- Non-existent files are used for error scenarios
- File permissions and access are tested

## Test Data

### Sample Responses
The tests include realistic sample responses that Gemini might return:

```json
[
  {
    "summary": "Header text overflows container on mobile",
    "severity": "high", 
    "suggested_fix": "Add responsive text wrapping"
  }
]
```

### Error Scenarios
Various malformed responses are tested:
- Invalid JSON syntax
- Missing required fields
- Non-array responses
- Empty responses
- Network errors

## Continuous Integration

The tests are designed to run reliably in CI environments:

- No external API dependencies (fully mocked)
- Deterministic test data
- Fast execution (under 30 seconds for full suite)
- Clear error reporting
- Cross-platform compatibility

## Adding New Tests

### For New Functionality
1. Add test methods to appropriate test class
2. Create fixtures for new test data if needed
3. Update this documentation

### For Bug Fixes
1. Add regression test that reproduces the bug
2. Verify the test fails before the fix
3. Verify the test passes after the fix

### Test Naming Convention
- Test classes: `TestClassBeingTested`
- Test methods: `test_specific_functionality`
- Fixtures: `descriptive_fixture_name`

## Dependencies

The tests require these packages (automatically installed with requirements.txt):

- `pytest` - Test framework
- `pytest-asyncio` - Async test support
- `pytest-cov` - Coverage reporting
- `pytest-mock` - Enhanced mocking capabilities

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure you're running from project root
   - Check that `src/` is in Python path

2. **Missing Dependencies**
   - Run: `pip install -r requirements.txt`

3. **Mock Failures**
   - Verify mock patches match actual module structure
   - Check that mocks are properly scoped

4. **Performance Test Failures**
   - Performance tests may be sensitive to system load
   - Consider running with `--quick` for faster feedback

### Debug Mode
```bash
# Run with maximum verbosity and debugging
pytest src/tests/test_gemini_analyzer.py -vvs --tb=long

# Run single test with debugging
pytest src/tests/test_gemini_analyzer.py::TestGeminiAnalyzer::test_init_with_api_key -vvs --pdb
```
