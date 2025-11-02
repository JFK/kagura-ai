"""Carefully crafted prompts for coding context analysis.

This module contains high-quality prompt templates following best practices:
- Few-shot learning with examples
- Chain-of-thought reasoning
- Structured output formats (JSON/YAML)
- Clear role definitions
- Explicit constraints

All prompts are designed for maximum reliability and consistency.
"""

from typing import Any

# =============================================================================
# SESSION SUMMARIZATION PROMPTS
# =============================================================================

SESSION_SUMMARY_SYSTEM = """You are an expert software engineering assistant
specializing in analyzing coding sessions.

<role>
Your role is to:
- Analyze coding activities comprehensively
- Extract key technical decisions and their rationale
- Identify patterns in developer behavior
- Provide actionable insights and recommendations
</role>

<output_requirements>
- Use clear, structured markdown format
- Be concise but comprehensive
- Focus on "why" not just "what"
- Highlight both successes and areas for improvement
- Include specific examples when relevant
</output_requirements>

<reasoning_approach>
Before providing your summary, think through:
1. What was the main objective of this session?
2. What technical challenges were encountered?
3. What patterns (good or bad) are evident?
4. What recommendations would most help the developer?
</reasoning_approach>"""

SESSION_SUMMARY_USER_TEMPLATE = """Analyze the following coding session and
generate a comprehensive summary.

<session_information>
<duration>{duration_minutes:.1f} minutes ({duration_human})</duration>
<project>{project_id}</project>
<description>{description}</description>
</session_information>

<files_modified count="{file_count}">
{files_list}
</files_modified>

<errors_encountered total="{error_count}" fixed="{fixed_count}">
{errors_list}
</errors_encountered>

<design_decisions count="{decision_count}">
{decisions_list}
</design_decisions>

<task>
First, in <thinking> tags, analyze:
1. What was the main goal? Was it achieved?
2. What were the key technical challenges?
3. What patterns do you observe in the approach taken?
4. What could be improved next time?

Then, generate a structured summary covering:

### 1. Session Overview
Brief statement of what was accomplished

### 2. Key Technical Decisions
List each decision with:
- **Decision:** What was decided
- **Rationale:** Why this approach was chosen
- **Impact:** Expected effect on the project

### 3. Challenges & Solutions
For each significant error/challenge:
- **Challenge:** What went wrong
- **Root Cause:** Why it happened
- **Solution:** How it was resolved
- **Prevention:** How to avoid in future

### 4. Patterns Observed
Identify:
- **Good Practices:** What went well
- **Anti-Patterns:** What should be improved
- **Coding Style:** Observed preferences

### 5. Recommendations
3-5 actionable recommendations for:
- Future sessions on this project
- Code quality improvements
- Development workflow enhancements
</task>

<output_format>
Structure your response as:

1. <thinking>Your analysis here</thinking>
2. Structured markdown summary (as specified above)

Use markdown with clear sections. Be specific and actionable.
</output_format>

## Example Output Structure
```markdown
# Session Summary: {session_id}

## Overview
Implemented authentication middleware for FastAPI, including JWT token
validation and role-based access control.

## Key Technical Decisions

### 1. JWT vs Session-based Auth
- **Decision:** Use JWT tokens with RS256 signing
- **Rationale:** Stateless auth enables horizontal scaling, RS256 provides
better security than HS256
- **Impact:** No session storage needed, but requires key rotation strategy

### 2. Access Control Pattern
- **Decision:** Decorator-based permission checks
- **Rationale:** Clean separation of concerns, reusable across endpoints
- **Impact:** Reduces boilerplate, easier to audit permissions

## Challenges & Solutions

### TypeError in token validation
- **Challenge:** Token expiry comparison failing with TypeError
- **Root Cause:** datetime comparison between aware/naive datetime objects
- **Solution:** Ensure all timestamps use UTC timezone
- **Prevention:** Add type hints and use datetime.utcnow() consistently

## Patterns Observed

**Good Practices:**
- Comprehensive type hints throughout
- Extensive unit tests for edge cases
- Clear docstrings with examples

**Areas for Improvement:**
- Some functions exceed 50 lines (consider refactoring)
- Magic strings for role names (use Enum instead)

**Coding Style:**
- Prefers functional approach over OOP
- Follows Pydantic validation patterns
- Uses async/await consistently

## Recommendations

1. **Extract role definitions to Enum** - Replace string literals with
`UserRole` enum for type safety
2. **Add integration tests** - Current tests are unit-only, add E2E auth flow tests
3. **Implement token refresh** - Current JWT has no refresh mechanism
4. **Document security assumptions** - Add security.md explaining threat model
5. **Set up pre-commit hooks** - Ensure type checking runs before commits
```

Now generate the summary:"""

# =============================================================================
# ERROR PATTERN ANALYSIS PROMPTS
# =============================================================================

ERROR_PATTERN_SYSTEM = """You are an expert at identifying patterns in software errors.

<role>
Your role is to:
- Analyze error histories to find recurring issues
- Identify root causes beyond surface symptoms
- Suggest prevention strategies
- Provide actionable quick fixes
</role>

<key_principles>
- Focus on patterns, not individual errors
- Identify systemic issues (e.g., missing validation, unclear APIs)
- Prioritize by frequency and severity
- Balance short-term fixes with long-term improvements
</key_principles>

<reasoning_approach>
Use chain-of-thought reasoning:
1. Group similar errors together
2. Identify the common root cause
3. Consider why this keeps happening
4. Propose both immediate fixes and long-term prevention
</reasoning_approach>"""

ERROR_PATTERN_USER_TEMPLATE = """Analyze the following error history to
identify recurring patterns.

## Error History
{error_history}

## Task
For each pattern you identify, provide:

### Pattern Structure
```yaml
name: Brief descriptive name (e.g., "Off-by-one in loop indices")
frequency: Number of occurrences
confidence: 0.0-1.0 (how confident you are this is a real pattern)
severity: low | medium | high

root_cause: |
  Deep explanation of why this keeps happening.
  Focus on systemic issues, not surface symptoms.

prevention_strategy: |
  How to avoid this in the future.
  Include code patterns, tools, or practices.

quick_fix: |
  Standard steps to resolve when it occurs.
  Step-by-step, copy-pastable when possible.

examples:
  - "file.py:42 - IndexError accessing list[i+1]"
  - "utils.py:17 - Similar off-by-one in range()"
```

## Guidelines
- Only report patterns that occur 2+ times
- Confidence < 0.7 for weak patterns, > 0.8 for strong patterns
- Be specific: "Missing null checks on API responses" not "TypeError"
- Include code examples in prevention strategies
- Keep quick_fix actionable (not just "fix the bug")

## Example Output
```yaml
patterns:
  - name: "Async/await inconsistency in database calls"
    frequency: 5
    confidence: 0.9
    severity: medium

    root_cause: |
      Mixing sync and async database calls due to unclear API.
      The ORM provides both `query()` (sync) and `aquery()` (async),
      but the async requirement isn't enforced by type system.

    prevention_strategy: |
      1. Use async-only database client (e.g., asyncpg instead of psycopg2)
      2. Add type hints: `async def func() -> Awaitable[Result]`
      3. Enable pyright strict mode to catch missing awaits
      4. Code review checklist: "All DB calls use await?"

      Example pattern to follow:
      ```python
      async def get_user(user_id: int) -> User:
          result = await db.aquery("SELECT * FROM users WHERE id = $1", user_id)
          return User.parse_obj(result)
      ```

    quick_fix: |
      1. Identify the sync call (usually missing `await`)
      2. Add `await` keyword: `result = await db.query(...)`
      3. Ensure function is marked `async def`
      4. Check all callers also use `await` on this function

    examples:
      - "api/users.py:45 - RuntimeError: no running event loop"
      - "api/posts.py:33 - coroutine was never awaited"
      - "services/auth.py:78 - Task was destroyed but it is pending"

  - name: "Type mismatches in JSON API responses"
    frequency: 4
    confidence: 0.85
    severity: medium

    root_cause: |
      External API returns numeric IDs as strings ("123" vs 123),
      but our Pydantic models expect integers. The API is inconsistent
      (sometimes string, sometimes int) depending on the endpoint.

    prevention_strategy: |
      1. Use Pydantic validators to coerce types:
      ```python
      class User(BaseModel):
          id: int

          @validator('id', pre=True)
          def coerce_id(cls, v):
              return int(v) if isinstance(v, str) else v
      ```
      2. Add integration tests that use real API responses (recorded)
      3. Document API inconsistencies in api_docs.md
      4. Consider using `str | int` union type if coercion is risky

    quick_fix: |
      1. Locate the Pydantic model causing ValidationError
      2. Add pre-validator to coerce the field type
      3. Test with both string and int inputs
      4. Update API documentation to note inconsistency

    examples:
      - "models/user.py:15 - ValidationError: id value is not a valid integer"
      - "models/post.py:23 - ValidationError: author_id must be integer"
```

Now analyze the errors:"""

# =============================================================================
# SOLUTION SUGGESTION PROMPTS
# =============================================================================

SOLUTION_SUGGESTION_SYSTEM = """You are an expert debugging assistant with
deep knowledge of software patterns.

<role>
Your role is to:
- Suggest solutions based on past successful resolutions
- Apply analogical reasoning from similar past errors
- Provide step-by-step implementation guidance
- Assess confidence in your suggestions
</role>

<key_principles>
- Prioritize solutions that worked before
- Explain *why* a solution works, not just *what* to do
- Offer alternatives when confidence is low
- Include code examples when helpful
</key_principles>

<reasoning_approach>
Use chain-of-thought reasoning:
1. Analyze the current error in detail
2. Compare with similar past errors
3. Identify which past solution is most applicable
4. Explain why that solution should work here
5. Consider edge cases and alternatives
</reasoning_approach>"""

SOLUTION_SUGGESTION_USER_TEMPLATE = """Suggest a solution for the current
error based on past similar errors.

## Current Error
**Type:** {error_type}
**Message:** {error_message}
**File:** {file_path}:{line_number}
**Stack Trace:**
```
{stack_trace}
```

{screenshot_section}

## Similar Past Errors (with solutions)
{similar_errors}

## Task
Provide a solution recommendation with:

### Solution Structure
```yaml
confidence: low | medium | high
primary_solution:
  steps: |
    Step-by-step instructions.
    Include code changes with before/after examples.
  reasoning: |
    Why this solution addresses the root cause.
    Reference similar past errors if applicable.
  code_example: |
    ```python
    # Complete, copy-pastable code example
    ```

alternative_solutions:
  - approach: "Alternative approach name"
    when_to_use: "When this is better than primary"
    steps: "Brief steps"

similar_pattern: |
  If this matches a known pattern from past errors,
  explain the connection and how past solutions apply.

debugging_tips: |
  Additional tips for investigating if solution doesn't work.
```

## Guidelines
- **High confidence:** Direct match with past solution (95%+ similarity)
- **Medium confidence:** Similar pattern, solution likely transfers (70-95%)
- **Low confidence:** Novel error, educated guess (<70%)
- Always provide reasoning, not just instructions
- Include code examples for complex solutions
- Mention potential side effects or edge cases

## Example Output
```yaml
confidence: high

primary_solution:
  steps: |
    1. The error occurs because you're comparing a timezone-aware datetime
       with a naive datetime object. This is a common issue with JWT expiry checks.

    2. Ensure all datetime objects use UTC timezone:
       ```python
       # BEFORE (causes TypeError)
       if token.exp < datetime.now():
           raise TokenExpired()

       # AFTER (correct)
       if token.exp < datetime.now(timezone.utc):
           raise TokenExpired()
       ```

    3. Update the token generation to also use UTC:
       ```python
       exp = datetime.now(timezone.utc) + timedelta(hours=24)
       ```

    4. Add type hint to enforce timezone-aware datetimes:
       ```python
       from datetime import datetime, timezone

       def validate_token(token: str) -> dict[str, Any]:
           exp: datetime = decode_jwt(token)["exp"]
           # Ensure exp is timezone-aware
           if exp.tzinfo is None:
               exp = exp.replace(tzinfo=timezone.utc)
           if exp < datetime.now(timezone.utc):
               raise TokenExpired()
       ```

  reasoning: |
    This error matches the pattern from errors #42 and #87 (both datetime
    comparison issues). The root cause is mixing naive and aware datetimes,
    which Python 3.11+ explicitly forbids.

    The solution works because:
    1. All times are in UTC (no daylight saving issues)
    2. Comparisons are between same types (both aware)
    3. Type hints catch future mistakes at development time

    Past resolution in error #87 used the same approach and successfully
    prevented recurrence for 3 months.

  code_example: |
    ```python
    from datetime import datetime, timedelta, timezone
    from typing import Any

    def create_token(user_id: int, expires_in: timedelta) -> str:
        '''Create JWT with timezone-aware expiry.'''
        exp = datetime.now(timezone.utc) + expires_in
        payload = {"sub": user_id, "exp": exp}
        return encode_jwt(payload)

    def validate_token(token: str) -> dict[str, Any]:
        '''Validate JWT expiry with timezone-aware comparison.'''
        try:
            payload = decode_jwt(token)
            exp_timestamp = payload["exp"]

            # JWT exp is Unix timestamp - convert to aware datetime
            exp = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)

            if exp < datetime.now(timezone.utc):
                raise TokenExpired("Token has expired")

            return payload
        except (KeyError, ValueError) as e:
            raise InvalidToken(f"Invalid token format: {e}")
    ```

alternative_solutions:
  - approach: "Store expiry as Unix timestamp"
    when_to_use: "If you want to avoid datetime complexity entirely"
    steps: |
      1. Store/compare expiry as integer Unix timestamps
      2. Use `time.time()` instead of datetime objects
      3. Example: `if token.exp < time.time(): raise TokenExpired()`

      Pros: No timezone issues, simpler
      Cons: Less readable, no datetime features

  - approach: "Use arrow or pendulum library"
    when_to_use: "If working extensively with timezones"
    steps: |
      1. `pip install arrow`
      2. Use `arrow.utcnow()` instead of datetime
      3. All arrow objects are timezone-aware by default

      Pros: Cleaner API, better timezone handling
      Cons: Additional dependency

similar_pattern: |
  This is the "naive-aware datetime comparison" pattern seen in:
  - Error #42: Token validation (3 months ago) - Resolved with UTC enforcement
  - Error #87: Database timestamp comparison (1 month ago) - Same solution

  Pattern: Mixing datetime.now() (naive) with datetime from external source (aware)
  Prevention: Always use datetime.now(timezone.utc) in new code

debugging_tips: |
  If the error persists after applying the solution:
  1. Check if datetime is coming from a database that stores naive times
     - Solution: Add `tzinfo=timezone.utc` when reading from DB
  2. Verify JWT library's decode behavior - some return naive datetimes
     - Solution: Convert explicitly: `dt.replace(tzinfo=timezone.utc)`
  3. Enable pyright strict mode to catch naive/aware mismatches at dev time
  4. Add assertion: `assert exp.tzinfo is not None, "Expected aware datetime"`
```

Now suggest a solution:"""

# =============================================================================
# CODING PREFERENCE EXTRACTION PROMPTS
# =============================================================================

PREFERENCE_EXTRACTION_SYSTEM = """You are an expert at analyzing developer
coding patterns and preferences.

<role>
Your role is to:
- Identify consistent patterns in code changes and decisions
- Distinguish between project requirements and personal preferences
- Extract actionable insights for AI assistants
- Avoid over-generalizing from limited data
</role>

<key_principles>
- Confidence based on consistency (3+ examples = medium, 5+ = high)
- Distinguish "always does X" from "did X once"
- Focus on preferences that affect code generation
- Note exceptions to patterns
</key_principles>

<reasoning_approach>
Use chain-of-thought analysis:
1. Group similar code changes by pattern
2. Count occurrences to assess consistency
3. Distinguish personal style from project constraints
4. Extract preferences that AI can apply to new code
</reasoning_approach>"""

PREFERENCE_EXTRACTION_USER_TEMPLATE = """Analyze coding patterns to extract
developer preferences.

## File Changes (n={change_count})
{file_changes}

## Design Decisions (n={decision_count})
{design_decisions}

## Task
Extract coding preferences in the following categories:

### Preference Structure
```yaml
language_preferences:
  python_version: "3.11+"  # If evident from type hints, syntax
  type_annotations: always | usually | rarely
  docstring_style: google | numpy | sphinx | minimal
  async_usage: heavy | moderate | minimal

library_preferences:
  web_framework: fastapi | flask | django | ...
  testing: pytest | unittest | ...
  validation: pydantic | marshmallow | ...
  # Other libraries with 3+ uses

naming_conventions:
  functions: snake_case | camelCase
  classes: PascalCase | ...
  constants: SCREAMING_SNAKE_CASE | ...
  private_prefix: _underscore | __double | none

code_organization:
  file_length_preference: short (<200) | medium (200-500) | long (500+)
  function_length_preference: short (<20) | medium (20-50) | long (50+)
  class_vs_function: prefers_classes | prefers_functions | mixed
  import_style: absolute | relative | mixed

patterns:
  error_handling: exceptions | result_types | both
  null_handling: optional_types | none_checks | assertions
  validation: early (at input) | late (at use) | mixed

testing_practices:
  test_coverage_importance: high | medium | low
  test_style: unit_focused | integration_focused | e2e_focused
  mock_usage: heavy | moderate | minimal

confidence_levels:
  # For each preference, include confidence
  # based on: high (5+ consistent examples), medium (3-4), low (1-2)
```

## Guidelines
- Only include preferences with 2+ supporting examples
- Note confidence level for each preference
- Include counter-examples if pattern isn't 100% consistent
- Distinguish project constraints from personal preferences
- Focus on preferences that affect code generation

## Example Output
```yaml
language_preferences:
  python_version: "3.11+"
  type_annotations: always
    confidence: high
    evidence: "All 47 functions have complete type hints including return types"

  docstring_style: google
    confidence: high
    evidence: "Consistent Google-style docstrings in 38/40 functions"
    exceptions: "2 utility functions lack docstrings"

  async_usage: heavy
    confidence: high
    evidence: "All database and API calls use async/await (23 functions)"

library_preferences:
  web_framework: fastapi
    confidence: high
    evidence: "5 endpoints defined, all use FastAPI patterns"

  testing: pytest
    confidence: high
    evidence: "All 31 test files use pytest fixtures and conventions"

  validation: pydantic
    confidence: high
    evidence: "19 data models, all use Pydantic BaseModel"

  database: asyncpg
    confidence: medium
    evidence: "3 database files all use asyncpg, but only 3 examples"

naming_conventions:
  functions: snake_case
    confidence: high
    evidence: "All 47 functions use snake_case, zero exceptions"

  classes: PascalCase
    confidence: high
    evidence: "All 19 classes use PascalCase"

  constants: SCREAMING_SNAKE_CASE
    confidence: medium
    evidence: "4/5 constants use SCREAMING, 1 uses lowercase"

  private_prefix: single_underscore
    confidence: high
    evidence: "Private methods use _prefix (8 examples), never __double"

code_organization:
  file_length_preference: medium
    confidence: medium
    evidence: "Average file length 234 lines, range 120-450"

  function_length_preference: short
    confidence: high
    evidence: "89% of functions under 20 lines, longest is 35 lines"
    note: "Strong preference for breaking down complex functions"

  class_vs_function: prefers_functions
    confidence: high
    evidence: "47 functions vs 19 classes, classes used mainly for data models"

  import_style: absolute
    confidence: high
    evidence: "All imports use absolute paths from project root"

patterns:
  error_handling: exceptions
    confidence: high
    evidence: "Consistent use of try/except, custom exception classes"
    note: "No use of Result types or error codes"

  null_handling: optional_types
    confidence: high
    evidence: "Uses Optional[T] and | None extensively (28 occurrences)"
    note: "Prefers type system over runtime null checks"

  validation: early
    confidence: high
    evidence: "Pydantic validation at API boundary, assertions rare"

testing_practices:
  test_coverage_importance: high
    confidence: high
    evidence: "91% coverage, even edge cases tested"

  test_style: unit_focused
    confidence: medium
    evidence: "27 unit tests vs 4 integration tests"

  mock_usage: moderate
    confidence: medium
    evidence: "Mocks for external APIs, real objects for internal code"

architectural_preferences:
  - pattern: "Dependency injection via function parameters"
    confidence: high
    evidence: "Database connections passed as params (12 functions)"

  - pattern: "Thin controllers, fat services"
    confidence: medium
    evidence: "API routes delegate to service layer (5 examples)"

  - pattern: "Explicit is better than implicit"
    confidence: high
    evidence: "No global state, no magic imports, explicit dependencies"

anti_patterns_avoided:
  - "Global mutable state" (confidence: high, 0 occurrences in 47 files)
  - "God objects" (confidence: high, largest class is 8 methods)
  - "Deep nesting" (confidence: high, max indent level is 3)

recommendations_for_ai_assistants:
  - "Always include type hints with return types"
  - "Use Pydantic for any data validation needs"
  - "Keep functions under 20 lines - extract helpers if needed"
  - "Add Google-style docstrings to all public functions"
  - "Prefer async/await for I/O operations"
  - "Use absolute imports from project root"
  - "Write comprehensive unit tests with edge cases"
  - "Inject dependencies via parameters, not globals"
```

Now extract preferences:"""

# =============================================================================
# CONTEXT COMPRESSION PROMPTS (RFC-024)
# =============================================================================

CONTEXT_COMPRESSION_SYSTEM = """You are an expert at compressing technical
context while preserving critical information.

<role>
Your role is to:
- Reduce token count while maintaining semantic meaning
- Preserve key decisions, errors, and patterns
- Create hierarchical summaries (brief → detailed → full)
- Ensure compressed context remains actionable
</role>

<key_principles>
- Never lose critical information (errors, decisions, security issues)
- Compress verbose explanations, not conclusions
- Maintain traceability (reference original items by ID)
- Target 70-90% token reduction
</key_principles>

<reasoning_approach>
Use systematic compression:
1. Identify critical vs. non-critical information
2. Replace verbose explanations with concise summaries
3. Use references (e.g., "Error #42") instead of full text
4. Preserve all numerical data and specifics
</reasoning_approach>"""

CONTEXT_COMPRESSION_USER_TEMPLATE = """Compress the following coding context
to approximately {target_tokens} tokens.

## Full Context ({original_tokens} tokens)
{full_context}

## Preservation Priority (MUST keep)
{preserve_topics}

## Compression Task
Create a hierarchical summary with three levels:

### Level 1: Brief Summary (target: 10% of original tokens)
- 2-3 sentence overview
- Critical alerts only (security, breaking changes, blockers)

### Level 2: Detailed Summary (target: 30% of original tokens)
- Key decisions with brief rationale
- Major errors and solutions
- Important patterns
- Reference original IDs for traceability

### Level 3: Comprehensive (target: 70% of original tokens)
- All significant information
- Condensed explanations (remove redundancy)
- Preserved examples for critical patterns

## Guidelines
- Use references: "Error #42 (TypeError in auth.py)" not full stack trace
- Compress "We decided to use FastAPI because it's modern, async-first, has
great docs, and Pydantic integration" → "Chose FastAPI for async + Pydantic"
- Keep numbers: "91% test coverage" not "high coverage"
- Preserve specifics: "bug in line 45" not "bug somewhere"
- Remove filler: "it's important to note that", "basically", etc.

## Example Compression

**Original (437 tokens):**
```
In this session, we worked on implementing the authentication system for our API.
We spent considerable time deciding between different approaches. Initially, we
considered using session-based authentication, which is a traditional approach
that stores user state on the server. However, after discussing the pros and cons,
we ultimately decided to implement JWT (JSON Web Token) based authentication instead.

The main reasons for this decision were:
1. Stateless authentication enables better horizontal scaling because we don't need
   to store sessions in a database or cache
2. JWTs can be validated without database lookups, improving performance
3. The token-based approach works better for our planned mobile app integration
4. We can easily implement role-based access control by including claims in the token

During implementation, we encountered several errors. The first error was a TypeError
when comparing datetime objects. This happened because we were comparing a
timezone-aware
datetime from the JWT with a naive datetime from datetime.now(). The solution was to
use datetime.now(timezone.utc) consistently throughout the codebase. This same error
had occurred before in a different module, which suggests we should add a linting rule
to catch this pattern.

We also decided to use RS256 signing instead of HS256 because RS256 provides better
security through asymmetric keys, even though it's slightly more complex to set up.
```

**Level 1 (43 tokens - 10%):**
```
Implemented JWT auth system with RS256 signing. Resolved datetime comparison TypeError
by enforcing UTC timestamps. Pattern suggests adding linter rule for timezone handling.
```

**Level 2 (131 tokens - 30%):**
```
## Session: Auth System Implementation

**Key Decisions:**
- JWT over sessions: stateless scaling, no DB lookups, mobile-ready (#decision-1)
- RS256 over HS256: asymmetric keys for better security (#decision-2)

**Errors Resolved:**
- #error-15: TypeError in datetime comparison (auth.py:42)
  - Cause: Mixed naive/aware datetimes
  - Fix: Use datetime.now(timezone.utc) consistently
  - Note: 2nd occurrence of this pattern → add linter rule

**Impact:** Auth system functional, blocks mobile app development work
```

**Level 3 (298 tokens - 68%):**
```
## Session: Authentication System Implementation

### Decisions

**#decision-1: JWT vs Session-based Auth**
- Chose: JWT tokens
- Rationale:
  - Stateless → horizontal scaling without session store
  - No DB lookup on validation → better performance
  - Better mobile app integration
  - Easy RBAC via token claims
- Alternative: Session-based (rejected for scaling concerns)

**#decision-2: RS256 vs HS256 Signing**
- Chose: RS256 (asymmetric keys)
- Rationale: Better security through public/private key separation
- Trade-off: More setup complexity, acceptable for security gain

### Errors

**#error-15: TypeError - Datetime Comparison**
- Location: auth.py:42, token validation
- Message: "can't compare offset-naive and offset-aware datetimes"
- Cause: JWT exp (aware) compared with datetime.now() (naive)
- Solution: Use datetime.now(timezone.utc) consistently across codebase
- Pattern: 2nd occurrence (also #error-8 in db_utils.py)
- Action Item: Add pyright rule or linter to catch naive datetime usage

### Implementation

Files: auth.py, middleware.py, models/user.py
Tests: 15 new tests, 92% coverage on auth module
Duration: 2.3 hours

### Impact

- ✅ Enables: Mobile app development (was blocked)
- ⚠️ Requires: Key rotation strategy (not yet implemented)
- 📋 Follow-up: Token refresh mechanism, revocation list
```

Now compress the context:"""

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================


def format_duration(minutes: float) -> str:
    """Format duration in human-readable form.

    Args:
        minutes: Duration in minutes

    Returns:
        Human-readable duration string

    Examples:
        >>> format_duration(45.5)
        '45 minutes'
        >>> format_duration(90)
        '1.5 hours'
        >>> format_duration(150)
        '2.5 hours'
    """
    if minutes < 60:
        return f"{minutes:.0f} minutes"
    hours = minutes / 60
    return f"{hours:.1f} hours"


def build_session_summary_prompt(session_data: dict[str, Any]) -> dict[str, str]:
    """Build session summary prompt from session data.

    Args:
        session_data: Dictionary containing session information

    Returns:
        Dictionary with 'system' and 'user' prompt keys
    """
    duration_minutes = session_data.get("duration_minutes", 0)
    duration_human = format_duration(duration_minutes)

    files_list = "\n".join(f"- {f}" for f in session_data.get("files_touched", []))
    errors_list = "\n\n".join(
        f"**Error {i + 1}:** {e.get('message', 'Unknown')}\n"
        f"File: {e.get('file_path', 'Unknown')}\n"
        f"Solution: {e.get('solution', 'Not yet resolved')}"
        for i, e in enumerate(session_data.get("errors", []))
    )
    decisions_list = "\n\n".join(
        f"**Decision {i + 1}:** {d.get('decision', 'Unknown')}\n"
        f"Rationale: {d.get('rationale', 'Not specified')}"
        for i, d in enumerate(session_data.get("decisions", []))
    )

    user_prompt = SESSION_SUMMARY_USER_TEMPLATE.format(
        duration_minutes=duration_minutes,
        duration_human=duration_human,
        project_id=session_data.get("project_id", "Unknown"),
        description=session_data.get("description", "No description"),
        file_count=len(session_data.get("files_touched", [])),
        files_list=files_list or "No files modified",
        error_count=len(session_data.get("errors", [])),
        fixed_count=sum(1 for e in session_data.get("errors", []) if e.get("resolved")),
        errors_list=errors_list or "No errors encountered",
        decision_count=len(session_data.get("decisions", [])),
        decisions_list=decisions_list or "No decisions recorded",
        session_id=session_data.get("session_id", "unknown"),
    )

    return {"system": SESSION_SUMMARY_SYSTEM, "user": user_prompt}


def build_error_pattern_prompt(errors: list[dict[str, Any]]) -> dict[str, str]:
    """Build error pattern analysis prompt.

    Args:
        errors: List of error records

    Returns:
        Dictionary with 'system' and 'user' prompt keys
    """
    error_history = "\n\n".join(
        f"### Error #{i + 1}\n"
        f"**Type:** {e.get('error_type', 'Unknown')}\n"
        f"**Message:** {e.get('message', 'N/A')}\n"
        f"**Location:** {e.get('file_path', 'unknown')}:{e.get('line_number', 0)}\n"
        f"**Timestamp:** {e.get('timestamp', 'Unknown')}\n"
        f"**Resolved:** {'Yes' if e.get('resolved') else 'No'}\n"
        f"**Solution:** {e.get('solution', 'Not yet resolved')}"
        for i, e in enumerate(errors)
    )

    user_prompt = ERROR_PATTERN_USER_TEMPLATE.format(error_history=error_history)

    return {"system": ERROR_PATTERN_SYSTEM, "user": user_prompt}


def build_solution_prompt(
    current_error: dict[str, Any], similar_errors: list[dict[str, Any]]
) -> dict[str, str]:
    """Build solution suggestion prompt.

    Args:
        current_error: The current error needing resolution
        similar_errors: Past similar errors with solutions

    Returns:
        Dictionary with 'system' and 'user' prompt keys
    """
    screenshot_section = ""
    if current_error.get("screenshot_path") or current_error.get("screenshot_base64"):
        screenshot_section = (
            "**Screenshot:** Available (analyze for additional context)\n"
        )

    similar_errors_text = (
        "\n\n".join(
            f"### Past Error #{i + 1} (Similarity: {e.get('similarity', 0):.1%})\n"
            f"**Type:** {e.get('error_type', 'Unknown')}\n"
            f"**Message:** {e.get('message', 'N/A')}\n"
            f"**Solution Applied:** {e.get('solution', 'No solution recorded')}\n"
            f"**Outcome:** {'Successful' if e.get('resolved') else 'Unresolved'}"
            for i, e in enumerate(similar_errors)
        )
        or "No similar past errors found"
    )

    user_prompt = SOLUTION_SUGGESTION_USER_TEMPLATE.format(
        error_type=current_error.get("error_type", "Unknown"),
        error_message=current_error.get("message", "No message"),
        file_path=current_error.get("file_path", "unknown"),
        line_number=current_error.get("line_number", 0),
        stack_trace=current_error.get("stack_trace", "No stack trace available"),
        screenshot_section=screenshot_section,
        similar_errors=similar_errors_text,
    )

    return {"system": SOLUTION_SUGGESTION_SYSTEM, "user": user_prompt}


def build_preference_extraction_prompt(
    file_changes: list[dict[str, Any]], decisions: list[dict[str, Any]]
) -> dict[str, str]:
    """Build coding preference extraction prompt.

    Args:
        file_changes: List of file change records
        decisions: List of design decisions

    Returns:
        Dictionary with 'system' and 'user' prompt keys
    """
    changes_text = "\n\n".join(
        f"### Change #{i + 1}\n"
        f"**File:** {c.get('file_path', 'unknown')}\n"
        f"**Action:** {c.get('action', 'unknown')}\n"
        f"**Reason:** {c.get('reason', 'Not specified')}\n"
        f"**Diff Summary:** {c.get('diff', 'N/A')[:200]}..."
        for i, c in enumerate(file_changes[:30])  # Limit to 30 most recent
    )

    decisions_text = "\n\n".join(
        f"### Decision #{i + 1}\n"
        f"**Decision:** {d.get('decision', 'Unknown')}\n"
        f"**Rationale:** {d.get('rationale', 'Not specified')}\n"
        f"**Alternatives:** {', '.join(d.get('alternatives', ['None']))}"
        for i, d in enumerate(decisions[:20])  # Limit to 20 most recent
    )

    user_prompt = PREFERENCE_EXTRACTION_USER_TEMPLATE.format(
        change_count=len(file_changes),
        file_changes=changes_text,
        decision_count=len(decisions),
        design_decisions=decisions_text,
    )

    return {"system": PREFERENCE_EXTRACTION_SYSTEM, "user": user_prompt}


def build_context_compression_prompt(
    full_context: str,
    target_tokens: int,
    original_tokens: int,
    preserve_topics: list[str],
) -> dict[str, str]:
    """Build context compression prompt.

    Args:
        full_context: The full context to compress
        target_tokens: Target token count
        original_tokens: Original token count
        preserve_topics: Topics that must be preserved

    Returns:
        Dictionary with 'system' and 'user' prompt keys
    """
    preserve_text = "\n".join(f"- {topic}" for topic in preserve_topics)

    user_prompt = CONTEXT_COMPRESSION_USER_TEMPLATE.format(
        target_tokens=target_tokens,
        original_tokens=original_tokens,
        full_context=full_context,
        preserve_topics=preserve_text or "- All critical information",
    )

    return {"system": CONTEXT_COMPRESSION_SYSTEM, "user": user_prompt}
