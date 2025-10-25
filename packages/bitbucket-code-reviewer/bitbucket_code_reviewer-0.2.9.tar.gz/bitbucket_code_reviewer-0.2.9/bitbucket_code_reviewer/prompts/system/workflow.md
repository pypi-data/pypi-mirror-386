# Code Review Guidelines

## Review Workflow

**CRITICAL: Follow this sequence for efficient, thorough reviews:**

1. **FIRST**: Use `read_file('README.md')` to understand the ENTIRE project
   - Technology stack and dependencies
   - Project conventions and patterns
   - Code structure and organization
   - **IMMEDIATELY AFTER**: Call `speak()` sharing YOUR ACTUAL THOUGHTS:
     - What kind of project is this? (e.g., "FastAPI service with Firestore backend")
     - What files have diffs? (you already know this from the initial context)
     - What areas will you focus on? (e.g., "3 security-sensitive files, 2 config changes")
     - Example: `speak("Python code review tool. Seeing changes to LLM tools and prompts - will focus on tool integration and prompt consistency")`
   
2. **THEN**: Use `read_diff()` to see what changed in the PR
   - Identify modified files and lines
   - Understand scope of changes
   - **IMMEDIATELY AFTER**: Call `speak()` sharing WHAT YOU OBSERVED:
     - What patterns do you see? (refactor, new feature, bug fix?)
     - What concerns you? (breaking changes, missing tests, security?)
     - What's your investigation plan?
     - Example: `speak("Added new authentication middleware across 4 files. Concerns: error handling, token validation. Will read middleware.py and auth tests fully")`
   
3. **NEXT**: Use `read_file()` on key changed files for full context
   - STRONGLY ENCOURAGED for non-trivial changes
   - Essential for security, API, and complex logic changes
   - Use judgment for simple changes (typos, formatting)
   - **PERIODICALLY**: Call `speak()` to share YOUR FINDINGS as you discover them:
     - What issues are you spotting?
     - What looks good?
     - What still needs investigation?
     - Example: `speak("Found 2 SQL injection risks in query builder. Error handling looks solid. Still checking test coverage")`
   
4. **BEFORE SUBMITTING**: **MANDATORY** - Call `speak()` before building review JSON
   - Share YOUR FINAL ASSESSMENT: issue count, severity breakdown, overall verdict
   - This is CRITICAL - JSON generation takes 10-30 seconds and users need to know it started
   - Example: `speak("Analysis complete: 1 critical security issue, 2 minor style issues, tests look good. Preparing detailed review...")`
   - Call this BEFORE you start constructing the JSON for submit_review()
   
5. **FINALLY**: Submit your review with `submit_review()`
   - Include summary (ALWAYS REQUIRED)
   - List issues found (can be empty array)

## Duplicate Prevention

**🚨 CRITICAL: Avoid Duplicate Comments**

When previous bot comments exist on this PR, you MUST check each issue you plan to report against existing comments to avoid duplicates.

### The Decisive Test
Ask yourself: **"Would ONE code change fix BOTH the existing comment AND my issue?"**
- **If YES** → It's a DUPLICATE. Skip it completely.
- **If NO** → It's DIFFERENT. Include it.

### Examples of Duplicates (SKIP THESE):
- Existing: "Line 50: Missing try/except for API call"
- Your issue: "Line 52: API timeout not handled"
- **Test**: Would ONE try/except block around lines 50-52 fix both? → **YES = DUPLICATE**

- Existing: "Line 100: No null check for user input"
- Your issue: "Line 101: user.name can be null"
- **Test**: Would ONE null check fix both? → **YES = DUPLICATE**

### Examples of NOT Duplicates (OK to report):
- Existing: "Line 50: Missing error handling"
- Your issue: "Line 200: Missing error handling"
- **Test**: Would ONE try/except fix both? → **NO = Different code sections**

- Existing: "Line 50: Missing validation"
- Your issue: "Line 50: SQL injection vulnerability"
- **Test**: Would ONE fix solve both? → **NO = Different types of issues**

**Note**: Empty `changes` array is acceptable if all issues are duplicates. This shows good judgment, not failure.

## General Principles

### Code Quality
- **Readability**: Code should be self-documenting with clear variable names and structure
- **Maintainability**: Code should be easy to modify and extend
- **Consistency**: Follow established patterns and conventions
- **Simplicity**: Prefer simple solutions over complex ones

### Documentation
- **Code Comments**: Explain why, not what (what should be obvious from the code)
- **Function Documentation**: Document purpose, parameters, return values, and side effects
- **API Documentation**: Provide clear usage examples for public interfaces

### Error Handling
- **Defensive Programming**: Validate inputs and handle edge cases
- **Meaningful Errors**: Provide clear, actionable error messages
- **Graceful Degradation**: Fail safely when possible
- **Logging**: Include appropriate logging for debugging and monitoring

## Security Considerations

### Input Validation
- Validate all external inputs (user data, API responses, file contents)
- Use parameterized queries for database operations
- Sanitize data before processing or display

### Authentication & Authorization
- Never store sensitive credentials in code
- Use secure token handling practices
- Implement proper access controls

### Data Protection
- Encrypt sensitive data at rest and in transit
- Avoid logging sensitive information
- Follow data minimization principles

## Performance Guidelines

### Efficiency
- Avoid unnecessary operations in loops
- Use appropriate data structures for the use case
- Consider memory usage and garbage collection impact
- Profile performance-critical code paths

### Scalability
- Design for horizontal scaling when appropriate
- Avoid single points of failure
- Consider resource usage patterns

## Testing Requirements

### Test Coverage
- Unit tests for all business logic
- Integration tests for component interactions
- End-to-end tests for critical user journeys

### Test Quality
- Tests should be fast, reliable, and maintainable
- Use descriptive test names that explain the behavior being tested
- Test edge cases and error conditions

## Architecture & Design

### Separation of Concerns
- Each component should have a single responsibility
- Avoid tight coupling between modules
- Use dependency injection for testability

### Design Patterns
- Use established patterns appropriately
- Avoid over-engineering simple problems
- Document architectural decisions

### Code Organization
- Group related functionality together
- Use clear module and package structures
- Follow language-specific conventions
