# Output Format Instructions

## Response Format Specification

You MUST respond with valid JSON containing exactly these fields:

**REQUIRED FIELDS:**
- **summary**: String (2-4 sentences) - Brief review summary explaining:
  1. What was reviewed (file count, change type)
  2. What was validated
  3. Outcome/reasoning
  - **IMPORTANT**: Do NOT mention issue count in summary (will be added automatically)
  - Example: "Reviewed 19 files refactoring schedule-zone components to shared location. Validated type safety, export consistency, and test coverage. All changes follow established patterns."
- **severity_counts**: Object with four integer counts: critical, major, minor, info
- **changes**: Array of issue objects (each with: file_path, start_line, end_line, severity, category, title, description, suggestion, code_snippet, suggested_code, rationale)

**VALID SEVERITY VALUES:** "critical", "major", "minor", "info"
**VALID CATEGORY VALUES:** "security", "performance", "maintainability", "architecture", "style"

**EXAMPLE STRUCTURE:**
```json
{
  "summary": "Reviewed 8 files implementing user authentication flow with token refresh. Validated error handling, type safety, and async patterns. Implementation matches existing authentication patterns with proper edge case handling.",
  "severity_counts": {
    "critical": 0,
    "major": 1,
    "minor": 2,
    "info": 0
  },
  "changes": [
    {
      "file_path": "path/to/file.py",
      "start_line": 42,
      "end_line": 42,
      "severity": "major",
      "category": "security",
      "title": "Missing input validation",
      "description": "User input is not validated before use",
      "suggestion": "Add input validation before processing",
      "code_snippet": "value = request.data['key']",
      "suggested_code": "value = validate_input(request.data.get('key', ''))",
      "rationale": "Prevents injection attacks and handles missing keys"
    }
  ]
}
```

## Important Notes
- Respond with **raw JSON only** - no markdown, no explanations
- Use the exact field names and types specified in the schema
- **summary is REQUIRED** - always provide a concise 2-4 sentence summary
- changes array can be empty if no issues found (summary still required)
- All severity counts should be integers (0 or higher)
- Focus only on REAL ISSUES that need fixing, not descriptions of what was done

