# Requirements Document

## Introduction

This feature enhances the vise-logger's tool name detection by checking directory paths for AI coding tool names instead of defaulting to "unknown". The system will search for specific tool names within the log directory path and use the first match found.

## Glossary

- **Tool_Name_Detector**: The system component that searches directory paths for AI coding tool names
- **Tool_Name_List**: The predefined list of AI coding tool names to search for in paths
- **Path_Search**: The process of checking if any tool names appear in a directory path

## Requirements

### Requirement 1

**User Story:** As a developer using the vise-logger, I want the system to automatically detect tool names from directory paths, so that I don't see "unknown" tool names in my session uploads.

#### Acceptance Criteria

1. WHEN a new log location is discovered, THE Tool_Name_Detector SHALL search the directory path for AI coding tool names
2. THE Tool_Name_Detector SHALL check for the following tool names: "Cursor", "Kiro", "GitHub Copilot", "Cline", "Roo", "Kilo", "Zencoder", "Augment"
3. WHERE exactly one tool name is found in the path, THE Tool_Name_Detector SHALL use that name as the tool name
4. IF no tool names are found in the path, THEN THE Tool_Name_Detector SHALL return "unknown" followed by the last two directories in the log path in parentheses
5. IF multiple tool names are found in the path, THEN THE Tool_Name_Detector SHALL return "unknown" followed by all found tool names separated by " & " in parentheses

### Requirement 2

**User Story:** As a developer, I want the tool detection to be case-insensitive, so that it works regardless of how the tool name appears in the directory path.

#### Acceptance Criteria

1. THE Tool_Name_Detector SHALL perform case-insensitive matching when searching for tool names in paths
2. WHEN a tool name is found, THE Tool_Name_Detector SHALL return the tool name in lowercase