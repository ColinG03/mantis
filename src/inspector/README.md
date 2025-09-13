# Mantis UI Inspector

The Inspector module provides a **simple, singleton interface** for the orchestrator to perform comprehensive UI testing and accessibility analysis on web pages using Playwright.

## Key Features

- **Simple Interface**: Just call `inspector.inspect_page(url)` 
- **Singleton Pattern**: One inspector instance handles all pages
- **Multi-viewport Testing**: Automatically tests desktop, tablet, and mobile viewports
- **Comprehensive Checks**: Accessibility, visual layout, and more
- **Evidence Collection**: Screenshots, logs, and detailed bug reports

## Architecture

### Main Components

- **`Inspector`** - Singleton orchestrator that coordinates all checks
- **`BaseCheck`** - Abstract base class for all check implementations  
- **`PageSetup`** - Handles safe navigation and page initialization
- **`EvidenceCollector`** - Captures screenshots, logs, and other evidence
- **`LinkDetector`** - Extracts outlinks without navigation

### Check Types

- **`StaticCheck`** - No user interaction required (accessibility, visual analysis)
- **`InteractiveCheck`** - Requires user interactions (forms, navigation)
- **`ViewportSpecificCheck`** - Runs differently per viewport size

### Current Implementations

1. **`AccessibilityCheck`** - WCAG compliance and accessibility issues
   - Missing alt text on images
   - Form inputs without labels  
   - Heading structure problems
   - Color contrast issues
   - Keyboard accessibility

2. **`VisualLayoutCheck`** - Visual and layout defects
   - Overlapping elements
   - Broken images
   - Invisible text
   - Elements outside viewport
   - Empty elements with visible dimensions

## Simple Usage

```python
from src.inspector import get_inspector

# Get the singleton inspector
inspector = await get_inspector()

# Just pass a URL - that's it!
result = await inspector.inspect_page("https://example.com")

# Use the results
print(f"Found {len(result.findings)} issues")
for bug in result.findings:
    print(f"[{bug.severity}] {bug.summary}")

# Clean up when done
await inspector.close()
```

### Multiple Pages

```python
inspector = await get_inspector()

urls = ["https://example.com", "https://example.com/about"]
for url in urls:
    result = await inspector.inspect_page(url)
    print(f"{url}: {len(result.findings)} issues")

await inspector.close()
```

## Output

The inspector returns a `PageResult` containing:

- **`findings`** - List of `Bug` objects with evidence
- **`outlinks`** - URLs found on the page for crawling
- **`timings`** - Performance metrics
- **`viewport_artifacts`** - Screenshots per viewport
- **`status`** - HTTP response status

## Evidence Collection

Each bug can include:

- **Screenshots** - Full page or element-specific
- **Console logs** - JavaScript errors and warnings  
- **DOM snapshots** - HTML state when bug was found
- **WCAG references** - Specific accessibility guidelines violated

## Adding New Checks

To add a new check type:

1. Create a class inheriting from `BaseCheck`, `StaticCheck`, or `InteractiveCheck`
2. Implement the `run()` method to return a list of `Bug` objects
3. Register the check with the inspector using `inspector.register_check()`

Example:

```python
class MyCustomCheck(StaticCheck):
    def __init__(self):
        super().__init__("My Check", "Description of what it does")
    
    async def run(self, page: Page, opts: InspectorOptions, viewport: str) -> List[Bug]:
        bugs = []
        # Your check logic here
        return bugs
```

## Safety Features

- **Timeout handling** - All operations have configurable timeouts
- **Error isolation** - Failed checks don't stop other checks
- **No navigation** - Links are detected but never clicked
- **Budget limits** - Interactive actions are limited to prevent infinite loops
- **Graceful degradation** - Continues working even if some features fail

## Performance

- **Multi-viewport testing** - Efficiently tests responsive breakpoints
- **Parallel execution** - Checks run concurrently where possible
- **Evidence on demand** - Screenshots only captured when needed
- **Resource cleanup** - Browser contexts properly closed
