"""Tests for prompt template engine"""
import pytest
from jinja2 import TemplateSyntaxError, UndefinedError
from kagura.core.prompt import (
    extract_template,
    render_prompt,
    validate_template,
    filter_truncate,
    filter_format_code,
    filter_list_items,
)


def test_extract_template():
    """Test template extraction from docstring"""
    def sample_func():
        '''This is a template with {{ variable }}'''
        pass

    template = extract_template(sample_func)
    assert template == "This is a template with {{ variable }}"


def test_extract_template_no_docstring():
    """Test error when function has no docstring"""
    def no_doc():
        pass

    with pytest.raises(ValueError, match="has no docstring"):
        extract_template(no_doc)


def test_render_basic():
    """Test basic template rendering"""
    template = "Hello, {{ name }}!"
    result = render_prompt(template, name="World")
    assert result == "Hello, World!"


def test_render_with_loop():
    """Test template with for loop"""
    template = """
    {% for item in items %}
    - {{ item }}
    {% endfor %}
    """
    result = render_prompt(template, items=["apple", "banana", "cherry"])
    assert "- apple" in result
    assert "- banana" in result
    assert "- cherry" in result


def test_render_with_conditional():
    """Test template with if/else"""
    template = """
    {% if is_urgent %}
    URGENT: {{ message }}
    {% else %}
    Normal: {{ message }}
    {% endif %}
    """

    result_urgent = render_prompt(template, is_urgent=True, message="Alert")
    assert "URGENT: Alert" in result_urgent
    assert "Normal:" not in result_urgent

    result_normal = render_prompt(template, is_urgent=False, message="Info")
    assert "Normal: Info" in result_normal
    assert "URGENT:" not in result_normal


def test_render_with_dict_iteration():
    """Test template with dictionary iteration"""
    template = """
    {% for key, value in data.items() %}
    {{ key }}: {{ value }}
    {% endfor %}
    """
    result = render_prompt(template, data={"name": "Alice", "age": 30})
    assert "name: Alice" in result
    assert "age: 30" in result


def test_filter_truncate():
    """Test truncate filter"""
    # Short text
    assert filter_truncate("Hello", 10) == "Hello"

    # Long text with default suffix
    assert filter_truncate("This is a very long text", 10) == "This is a ..."

    # Custom suffix
    assert filter_truncate("Long text", 5, "[more]") == "Long [more]"

    # Numeric input (should convert to string)
    assert filter_truncate(12345, 3) == "123..."


def test_filter_format_code():
    """Test format_code filter"""
    code = "def hello():\n    print('Hello')"
    result = filter_format_code(code)
    assert result == "```python\ndef hello():\n    print('Hello')\n```"

    # Custom language
    result_js = filter_format_code("console.log('Hi')", "javascript")
    assert result_js == "```javascript\nconsole.log('Hi')\n```"


def test_filter_list_items():
    """Test list_items filter"""
    items = ["apple", "banana", "cherry"]
    assert filter_list_items(items) == "apple, banana, cherry"

    # Custom separator
    assert filter_list_items(items, " | ") == "apple | banana | cherry"

    # Numbers
    assert filter_list_items([1, 2, 3]) == "1, 2, 3"


def test_render_with_truncate_filter():
    """Test template using truncate filter"""
    template = "{{ text | truncate(20) }}"
    result = render_prompt(template, text="This is a very long piece of text")
    assert result == "This is a very long ..."


def test_render_with_format_code_filter():
    """Test template using format_code filter"""
    template = "{{ code | format_code }}"
    result = render_prompt(template, code="print('Hello')")
    assert "```python" in result
    assert "print('Hello')" in result


def test_render_with_list_items_filter():
    """Test template using list_items filter"""
    template = "Items: {{ items | list_items }}"
    result = render_prompt(template, items=["a", "b", "c"])
    assert result == "Items: a, b, c"


def test_validate_template_valid():
    """Test template validation with valid template"""
    template = "Hello, {{ name }}!"
    error = validate_template(template, name="Test")
    assert error is None


def test_validate_template_syntax_error():
    """Test template validation with syntax error"""
    template = "Hello, {{ name"  # Missing closing braces
    error = validate_template(template)
    assert error is not None
    assert "syntax error" in error.lower()


def test_validate_template_undefined_variable():
    """Test template validation with undefined variable"""
    template = "Hello, {{ name }}!"
    error = validate_template(template, other="value")  # 'name' not provided
    assert error is not None
    assert "undefined" in error.lower()


def test_validate_template_no_sample_vars():
    """Test template validation without sample variables"""
    template = "Hello, {{ name }}!"
    error = validate_template(template)
    # Should pass syntax check even without variables
    assert error is None


def test_render_undefined_variable_raises():
    """Test that rendering with undefined variable raises error"""
    template = "Hello, {{ name }}!"
    with pytest.raises(UndefinedError):
        render_prompt(template, other="value")


def test_render_complex_template():
    """Test complex template with multiple features"""
    template = """
    Analysis of {{ dataset }}:
    {% for key, value in data.items() %}
    - {{ key }}: {{ value | truncate(50) }}
    {% endfor %}

    {% if has_code %}
    Code sample:
    {{ code | format_code('python') }}
    {% endif %}
    """

    result = render_prompt(
        template,
        dataset="User Data",
        data={
            "description": "This is a very long description that should be truncated",
            "count": 100,
        },
        has_code=True,
        code="print('test')"
    )

    assert "Analysis of User Data:" in result
    assert "description:" in result
    assert "..." in result  # Truncated text
    assert "count: 100" in result
    assert "```python" in result
    assert "print('test')" in result


def test_trim_blocks():
    """Test that trim_blocks and lstrip_blocks work"""
    template = """
    {% for item in items %}
    {{ item }}
    {% endfor %}
    """
    result = render_prompt(template, items=["a", "b"])
    # Should not have excessive blank lines
    lines = [line for line in result.split('\n') if line.strip()]
    assert len(lines) == 2
    assert "a" in lines[0]
    assert "b" in lines[1]
