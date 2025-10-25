# Design Document

## Overview

The tool name detection enhancement will replace the current hardcoded "unknown" default with intelligent path analysis. The system will search directory paths for AI coding tool names and return appropriate results based on the number of matches found.

## Architecture

The enhancement will be implemented as a new function `detect_tool_from_path()` in the `search.py` module that will be called from the existing `_add_location()` function before defaulting to "unknown".

### Current Flow
```
_add_location(path_to_zip) -> locations.append({"tool": "unknown", ...})
```

### Enhanced Flow
```
_add_location(path_to_zip) -> detect_tool_from_path(path_to_zip) -> locations.append({"tool": detected_tool, ...})
```

## Components and Interfaces

### New Function: `detect_tool_from_path(path: Path) -> str`

**Purpose**: Analyzes a directory path to detect AI coding tool names

**Input**: 
- `path: Path` - The directory path to analyze

**Output**: 
- `str` - The detected tool name or formatted unknown string

**Logic**:
1. Convert path to lowercase string for case-insensitive matching
2. Search for each tool name in the predefined list within the path
3. Return result based on number of matches found

### Tool Name List

The function will search for these AI coding tool names (case-insensitive):
- "cursor"
- "kiro" 
- "github copilot"
- "cline"
- "roo"
- "kilo"
- "zencoder"
- "augment"

### Integration Point

The function will be called from `_add_location()` in `search.py`, replacing the current hardcoded "unknown" assignment:

```python
# Current code:
locations.append({"dir": str(dir_of_all_logs), "tool": "unknown", "verified": True})

# Enhanced code:
detected_tool = detect_tool_from_path(dir_of_all_logs)
locations.append({"dir": str(dir_of_all_logs), "tool": detected_tool, "verified": True})
```

## Data Models

No new data models are required. The existing location entry structure remains unchanged:

```python
{
    "dir": str,      # Directory path
    "tool": str,     # Tool name (now intelligently detected)
    "verified": bool # Verification status
}
```

## Error Handling

The function will be designed to never fail:
- Invalid paths will be converted to strings safely
- Empty paths will result in "unknown" with empty directory info
- All exceptions will be caught and result in fallback behavior

## Testing Strategy

### Unit Tests
- Test single tool name detection
- Test multiple tool name detection  
- Test no tool name detection
- Test case-insensitive matching
- Test edge cases (empty paths, special characters)

### Integration Tests
- Test integration with `_add_location()` function
- Verify locations.json is updated with detected tool names
- Test with real directory structures from different AI coding tools