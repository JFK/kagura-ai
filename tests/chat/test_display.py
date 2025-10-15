"""
Tests for EnhancedDisplay
"""

from io import StringIO

import pytest
from rich.console import Console

from kagura.chat.display import EnhancedDisplay


class TestEnhancedDisplay:
    """Test suite for EnhancedDisplay"""

    @pytest.fixture
    def console(self) -> Console:
        """Create a test console"""
        return Console(file=StringIO(), force_terminal=True, width=80)

    @pytest.fixture
    def display(self, console: Console) -> EnhancedDisplay:
        """Create a test display"""
        return EnhancedDisplay(console)

    def test_display_simple_text(self, display: EnhancedDisplay) -> None:
        """Test displaying simple text"""
        # Should not raise
        display.display_response("Hello, world!")

    def test_display_markdown(self, display: EnhancedDisplay) -> None:
        """Test displaying markdown text"""
        markdown_text = """
# Title

This is a **bold** text with *italic*.

- Item 1
- Item 2
"""
        # Should not raise
        display.display_response(markdown_text)

    def test_display_code_block_python(self, display: EnhancedDisplay) -> None:
        """Test displaying Python code block"""
        response = """
Here's a Python example:

```python
def hello():
    print("Hello, world!")
```

That's it!
"""
        # Should not raise
        display.display_response(response)

    def test_display_code_block_javascript(self, display: EnhancedDisplay) -> None:
        """Test displaying JavaScript code block"""
        response = """
Here's a JavaScript example:

```javascript
function hello() {
    console.log("Hello, world!");
}
```
"""
        # Should not raise
        display.display_response(response)

    def test_display_multiple_code_blocks(self, display: EnhancedDisplay) -> None:
        """Test displaying multiple code blocks"""
        response = """
First block:

```python
def func1():
    pass
```

Second block:

```javascript
function func2() {}
```
"""
        # Should not raise
        display.display_response(response)

    def test_display_panel(self, display: EnhancedDisplay) -> None:
        """Test displaying panel"""
        # Should not raise
        display.display_panel("Panel content", title="Test", border_style="green")

    def test_display_panel_markdown(self, display: EnhancedDisplay) -> None:
        """Test displaying panel with markdown"""
        # Should not raise
        display.display_panel(
            "**Bold** text", title="Test", markdown=True, border_style="blue"
        )

    def test_display_error(self, display: EnhancedDisplay) -> None:
        """Test displaying error message"""
        # Should not raise
        display.display_error("Error message")

    def test_display_success(self, display: EnhancedDisplay) -> None:
        """Test displaying success message"""
        # Should not raise
        display.display_success("Success message")

    def test_display_info(self, display: EnhancedDisplay) -> None:
        """Test displaying info message"""
        # Should not raise
        display.display_info("Info message")

    def test_display_warning(self, display: EnhancedDisplay) -> None:
        """Test displaying warning message"""
        # Should not raise
        display.display_warning("Warning message")

    def test_code_block_without_language(self, display: EnhancedDisplay) -> None:
        """Test code block without language specification"""
        response = """
Code without language:

```
some code here
```
"""
        # Should default to python
        display.display_response(response)

    def test_empty_code_block(self, display: EnhancedDisplay) -> None:
        """Test empty code block"""
        response = """
Empty block:

```python
```
"""
        # Should not raise
        display.display_response(response)

    def test_nested_markdown_in_text(self, display: EnhancedDisplay) -> None:
        """Test markdown formatting outside code blocks"""
        response = """
Text with **bold** and *italic*.

```python
# Code here
def func():
    pass
```

More **markdown** text.
"""
        # Should not raise
        display.display_response(response)
