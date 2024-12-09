# State Management in Kagura AI

## Introduction

Kagura AI's state management system has been enhanced with INPUT_QUERY and TEXT_OUTPUT fields to provide clearer separation between inputs and outputs while maintaining state consistency. This guide explains how to effectively use these features in your agents.

## Core Concepts

### INPUT_QUERY
- Stores structured input field data
- Preserves original input context
- Enables input tracking and validation

### TEXT_OUTPUT
- Stores converted response text
- Provides standardized output format
- Facilitates response processing

## Implementation Example

### Basic Agent Configuration

```yaml
# agent.yml
input_fields:
  - text_input
  - parameters

response_fields:
  - analysis_result
  - summary
```

```yaml
# state_model.yml
state_fields:
  - name: text_input
    type: str
    description:
      - language: en
        text: Input text for processing
  - name: parameters
    type: Dict[str, Any]
    description:
      - language: en
        text: Processing parameters
  - name: analysis_result
    type: str
    description:
      - language: en
        text: Analysis output
  - name: summary
    type: str
    description:
      - language: en
        text: Summarized results
```

### Using State Management

```python
from kagura.core.agent import Agent

async def process_text():
    # Initialize agent with input data
    input_data = {
        "text_input": "Sample text for analysis",
        "parameters": {"depth": "detailed"}
    }

    agent = Agent.assigner("text_analyzer", input_data)
    result = await agent.execute()

    # Access stored input
    print("Input Data:", result.INPUT_QUERY)

    # Access converted output
    print("Text Output:", result.TEXT_OUTPUT)

    # Access specific fields
    print("Analysis:", result.analysis_result)
    print("Summary:", result.summary)
```

## Best Practices

### 1. Input Field Storage
- Store all input fields in INPUT_QUERY
- Validate input data structure
- Maintain input field relationships

### 2. Text Output Conversion
- Convert complex responses to readable text
- Handle different data types appropriately
- Maintain output consistency

### 3. State Consistency
- Keep INPUT_QUERY and TEXT_OUTPUT synchronized
- Handle state transitions cleanly
- Validate state at each step

## Advanced Features

### Custom Text Conversion

You can customize how responses are converted to text by modifying the `_convert_response_to_text` method:

```python
async def _convert_response_to_text(self) -> str:
    """Custom text conversion logic"""
    text_parts = []

    for field in self.response_fields:
        value = getattr(self._state, field)
        if isinstance(value, str):
            text_parts.append(value)
        elif isinstance(value, (list, dict)):
            text_parts.append(
                json.dumps(value, indent=2, ensure_ascii=False)
            )
        elif isinstance(value, BaseModel):
            text_parts.append(
                value.model_dump_json(indent=2)
            )

    return "\n\n".join(text_parts)
```

### State Validation

Implement custom validation for your state:

```python
from pydantic import validator

class MyStateModel(BaseStateModel):
    @validator('INPUT_QUERY')
    def validate_input_query(cls, v):
        if not v.get('required_field'):
            raise ValueError("Missing required field")
        return v
```

## Testing

### Example Test Cases

```python
@pytest.mark.asyncio
async def test_state_management():
    agent = Agent.assigner("my_agent")
    input_data = {
        "text_input": "Test input",
        "parameters": {"key": "value"}
    }

    result = await agent.execute(input_data)

    # Verify INPUT_QUERY storage
    assert result.INPUT_QUERY["text_input"] == "Test input"
    assert result.INPUT_QUERY["parameters"]["key"] == "value"

    # Verify TEXT_OUTPUT conversion
    assert result.TEXT_OUTPUT is not None
    assert isinstance(result.TEXT_OUTPUT, str)
```

## Common Patterns

### 1. Input Processing
```python
def process_input(state: BaseStateModel) -> None:
    # Access stored input data
    input_data = state.INPUT_QUERY

    # Process specific fields
    text_input = input_data.get("text_input", "")
    parameters = input_data.get("parameters", {})

    # Perform validation or transformation
    if not text_input:
        raise ValueError("Text input is required")
```

### 2. Output Formatting
```python
def format_output(state: BaseStateModel) -> None:
    # Generate formatted output
    formatted_text = []

    # Add analysis results
    if state.analysis_result:
        formatted_text.append(f"Analysis: {state.analysis_result}")

    # Add summary
    if state.summary:
        formatted_text.append(f"Summary: {state.summary}")

    # Update TEXT_OUTPUT
    state.TEXT_OUTPUT = "\n".join(formatted_text)
```

## Troubleshooting

### Common Issues

1. Missing Input Data
   - Verify all required input fields are provided
   - Check INPUT_QUERY structure
   - Validate input data types

2. Text Conversion Errors
   - Check response field definitions
   - Verify data type handling
   - Review text conversion logic

3. State Consistency
   - Ensure state transitions are handled
   - Verify field updates
   - Check validation rules

## Best Practices Summary

1. Always validate input data before processing
2. Maintain clear separation between input and output states
3. Use type hints and validation for better reliability
4. Document state transitions and transformations
5. Implement comprehensive error handling
6. Write tests for state management logic
7. Keep input and output structures consistent
8. Use appropriate data types for state fields
9. Handle state cleanup properly
10. Monitor state changes for debugging

## Future Considerations

1. State History Tracking
2. Enhanced Validation Rules
3. Custom Serialization Formats
4. State Migration Support
5. Performance Optimization
