# Kagura AI Prompt Templates

This directory contains Jinja2 prompt templates for various AI-powered coding analysis features.

## 📁 Directory Structure

```
prompts/
├── coding/                           # Coding session analysis prompts
│   ├── session_summary_system.j2     # System prompt for session summarization
│   ├── session_summary_user.j2       # User prompt for session summarization
│   ├── error_pattern_system.j2       # System prompt for error pattern analysis
│   ├── error_pattern_user.j2         # User prompt for error pattern analysis
│   ├── solution_suggestion_system.j2 # System prompt for solution suggestions
│   ├── solution_suggestion_user.j2   # User prompt for solution suggestions
│   ├── preference_extraction_system.j2 # System prompt for preference extraction
│   ├── preference_extraction_user.j2   # User prompt for preference extraction
│   ├── context_compression_system.j2   # System prompt for context compression
│   └── context_compression_user.j2     # User prompt for context compression
└── README.md                         # This file
```

## 🎯 Template Categories

### 1. Session Summary Templates

**Purpose:** Generate comprehensive summaries of coding sessions including decisions, errors, patterns, and recommendations.

**System:** `coding/session_summary_system.j2`
**User:** `coding/session_summary_user.j2`

**Variables:**
- `duration_minutes` (float): Session duration in minutes
- `duration_human` (str): Human-readable duration (e.g., "2.5 hours")
- `project_id` (str): Project identifier
- `description` (str): Session description
- `file_count` (int): Number of files modified
- `files_list` (str): Formatted list of modified files
- `error_count` (int): Total errors encountered
- `fixed_count` (int): Number of errors resolved
- `errors_list` (str): Formatted list of errors
- `decision_count` (int): Number of design decisions
- `decisions_list` (str): Formatted list of decisions
- `session_id` (str): Unique session identifier

**Usage:**
```python
from kagura.llm.prompts import build_session_summary_prompt

session_data = {
    "duration_minutes": 135.5,
    "project_id": "kagura-ai",
    "description": "Implement JWT authentication",
    "files_touched": ["auth.py", "middleware.py"],
    "errors": [...],
    "decisions": [...]
}
prompts = build_session_summary_prompt(session_data)
# Returns: {"system": "...", "user": "..."}
```

### 2. Error Pattern Analysis Templates

**Purpose:** Identify recurring error patterns and suggest prevention strategies.

**System:** `coding/error_pattern_system.j2`
**User:** `coding/error_pattern_user.j2`

**Variables:**
- `error_history` (str): Formatted list of historical errors

**Usage:**
```python
from kagura.llm.prompts import build_error_pattern_prompt

errors = [
    {"error_type": "TypeError", "message": "...", ...},
    {"error_type": "AttributeError", "message": "...", ...}
]
prompts = build_error_pattern_prompt(errors)
```

### 3. Solution Suggestion Templates

**Purpose:** Suggest solutions for current errors based on past successful resolutions.

**System:** `coding/solution_suggestion_system.j2`
**User:** `coding/solution_suggestion_user.j2`

**Variables:**
- `error_type` (str): Error type (e.g., "TypeError")
- `error_message` (str): Error message
- `file_path` (str): File where error occurred
- `line_number` (int): Line number where error occurred
- `stack_trace` (str): Full stack trace
- `screenshot_section` (str): Optional screenshot information
- `similar_errors` (str): Formatted list of similar past errors with solutions

**Usage:**
```python
from kagura.llm.prompts import build_solution_prompt

current_error = {
    "error_type": "TypeError",
    "message": "can't compare offset-naive and offset-aware datetimes",
    "file_path": "auth.py",
    "line_number": 42,
    "stack_trace": "..."
}
similar_errors = [...]
prompts = build_solution_prompt(current_error, similar_errors)
```

### 4. Preference Extraction Templates

**Purpose:** Extract developer coding preferences from file changes and decisions.

**System:** `coding/preference_extraction_system.j2`
**User:** `coding/preference_extraction_user.j2`

**Variables:**
- `change_count` (int): Number of file changes analyzed
- `file_changes` (str): Formatted list of file changes
- `decision_count` (int): Number of design decisions analyzed
- `design_decisions` (str): Formatted list of design decisions

**Usage:**
```python
from kagura.llm.prompts import build_preference_extraction_prompt

file_changes = [
    {"file_path": "api.py", "action": "edit", "reason": "...", "diff": "..."},
    ...
]
decisions = [
    {"decision": "Use FastAPI", "rationale": "...", "alternatives": [...]},
    ...
]
prompts = build_preference_extraction_prompt(file_changes, decisions)
```

### 5. Context Compression Templates

**Purpose:** Compress coding context while preserving critical information (RFC-024).

**System:** `coding/context_compression_system.j2`
**User:** `coding/context_compression_user.j2`

**Variables:**
- `target_tokens` (int): Target token count after compression
- `original_tokens` (int): Original token count
- `full_context` (str): Full context to compress
- `preserve_topics` (str): Formatted list of topics to preserve

**Usage:**
```python
from kagura.llm.prompts import build_context_compression_prompt

prompts = build_context_compression_prompt(
    full_context="...",
    target_tokens=500,
    original_tokens=2000,
    preserve_topics=["security decisions", "critical errors"]
)
```

## 🔧 Customization

### Override Templates Locally

Users can override templates by placing custom versions in `~/.kagura/prompts/`:

```bash
# Create user prompt directory
mkdir -p ~/.kagura/prompts/coding/

# Copy template to customize
cp src/kagura/templates/prompts/coding/session_summary_user.j2 \
   ~/.kagura/prompts/coding/session_summary_user.j2

# Edit as needed
vim ~/.kagura/prompts/coding/session_summary_user.j2
```

**Template Loading Order:**
1. `~/.kagura/prompts/coding/{template}.j2` (user override)
2. `src/kagura/templates/prompts/coding/{template}.j2` (default)

### Create Custom Templates

For new prompt types:

1. Create template file: `~/.kagura/prompts/custom/my_prompt.j2`
2. Load with Jinja2:

```python
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

# Set up Jinja2 environment
template_dirs = [
    Path.home() / ".kagura/prompts",  # User templates first
    Path(__file__).parent / "templates/prompts"  # Default templates
]
env = Environment(loader=FileSystemLoader([str(d) for d in template_dirs]))

# Render template
template = env.get_template("custom/my_prompt.j2")
rendered = template.render(variable1="value1", variable2="value2")
```

## 📝 Jinja2 Syntax Reference

### Variables
```jinja2
{{ variable_name }}
{{ dict.key }}
{{ list[0] }}
```

### Conditionals
```jinja2
{% if condition %}
  Content when true
{% elif other_condition %}
  Content for other condition
{% else %}
  Content when false
{% endif %}
```

### Loops
```jinja2
{% for item in items %}
  - {{ item.name }}
{% endfor %}
```

### Filters
```jinja2
{{ name|upper }}
{{ value|default("default value") }}
{{ number|round(2) }}
{{ text|truncate(100) }}
```

### Comments
```jinja2
{# This is a comment #}
```

## 🎨 Best Practices

### 1. Keep Templates Readable
- Use proper indentation
- Add comments for complex logic
- Break long lines for readability

### 2. Preserve XML/Markdown Structure
- Don't add Jinja2 syntax inside XML tags
- Keep markdown formatting intact
- Test rendered output format

### 3. Variable Naming
- Use descriptive names: `error_count` not `ec`
- Follow Python naming: `snake_case`
- Document all variables in README

### 4. Error Handling
- Provide defaults: `{{ variable|default("N/A") }}`
- Handle missing data gracefully
- Validate inputs in Python before rendering

### 5. Version Control
- Default templates in git
- User templates in `~/.kagura/` (not tracked)
- Document template version compatibility

## 🧪 Testing Templates

### Manual Testing
```python
from jinja2 import Template

template_str = """
Session: {{ project_id }}
Duration: {{ duration_minutes }} minutes
"""

template = Template(template_str)
result = template.render(
    project_id="kagura-ai",
    duration_minutes=135.5
)
print(result)
```

### Unit Testing
```python
import pytest
from kagura.llm.prompts import build_session_summary_prompt

def test_session_summary_prompt():
    session_data = {
        "duration_minutes": 60,
        "project_id": "test-project",
        "description": "Test session",
        "files_touched": ["test.py"],
        "errors": [],
        "decisions": []
    }

    prompts = build_session_summary_prompt(session_data)

    assert "test-project" in prompts["user"]
    assert "60" in prompts["user"]
    assert "<session_information>" in prompts["user"]
```

## 📚 Resources

- **Jinja2 Documentation:** https://jinja.palletsprojects.com/
- **Template Design Guide:** https://jinja.palletsprojects.com/en/stable/templates/
- **Kagura Prompts Source:** `src/kagura/llm/prompts.py`

## 🔄 Migration from String Templates

### Before (Python string formatting)
```python
PROMPT = """Hello {name}, you have {count} items"""
formatted = PROMPT.format(name="Alice", count=5)
```

### After (Jinja2 templates)
```python
from jinja2 import Template

template = Template("Hello {{ name }}, you have {{ count }} items")
rendered = template.render(name="Alice", count=5)
```

### Conversion Notes
- `{variable}` → `{{ variable }}`
- `{dict[key]}` → `{{ dict.key }}` or `{{ dict['key'] }}`
- `{value:.1f}` → `{{ value|round(1) }}`
- Escape literal braces: `{{` → `{{ '{{' }}`

## 🐛 Troubleshooting

### Template Not Found
```python
jinja2.exceptions.TemplateNotFound: coding/my_template.j2
```
**Solution:** Ensure template exists in template directories and path is correct.

### Undefined Variable
```python
jinja2.exceptions.UndefinedError: 'variable_name' is undefined
```
**Solution:** Provide the variable in `render()` or use default filter: `{{ variable|default("") }}`

### Template Syntax Error
```python
jinja2.exceptions.TemplateSyntaxError: unexpected '}'
```
**Solution:** Check for unmatched braces, missing `{% endif %}`, etc.

### Whitespace Issues
Use `-` to control whitespace:
```jinja2
{%- if condition -%}  {# Strip whitespace before and after #}
  content
{%- endif -%}
```

## 📖 Examples

See `tests/test_llm_prompts.py` for comprehensive template usage examples.
