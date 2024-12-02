from pathlib import Path
from typing import Optional

import yaml
from rich.console import Console


class IndentDumper(yaml.SafeDumper):
    def increase_indent(self, flow=False, indentless=False):
        # 'indentless' を常に False に設定
        return super(IndentDumper, self).increase_indent(flow, False)


class KaguraAgentTemplateCreator:
    TEMPLATE_DIR = Path(__file__).parent.parent / "agents"

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()

    def create_template(self, agent_name: str, description: str):
        root = Path(f"kagura-{agent_name}")
        self._create_structure(root, agent_name)
        self._create_agent_files(root, agent_name, description)
        self._create_test_files(root, agent_name)
        self._create_example_files(root, agent_name)
        self._create_project_files(root, agent_name, description)

    def _create_structure(self, root: Path, agent_name: str):
        dirs = [
            root / "agents" / agent_name,
            root / "tests" / agent_name,
            root / "examples" / agent_name,
        ]
        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)

    def _create_agent_files(self, root: Path, agent_name: str, description: str):
        agent_dir = root / "agents" / agent_name

        # agent.yml
        agent_config = {
            "description": [
                {"language": "en", "text": description},
                {"language": "ja", "text": description},
            ],
            "instructions": [
                {"language": "en", "description": "Instructions for the agent"},
                {"language": "ja", "description": "エージェントの指示"},
            ],
            "prompt": [
                {"language": "en", "template": "{input}"},
                {"language": "ja", "template": "{input}"},
            ],
            "response_fields": ["output"],
        }
        with open(agent_dir / "agent.yml", "w") as f:
            yaml.dump(
                agent_config,
                stream=f,
                allow_unicode=True,
                sort_keys=False,
                indent=2,
                default_flow_style=False,
                Dumper=IndentDumper,
            )

        # state_model.yml
        state_model = {
            "custom_models": [
                {
                    "name": "Output",
                    "fields": [
                        {
                            "name": "text",
                            "type": "str",
                            "description": [
                                {"language": "en", "text": "Output text"},
                                {"language": "ja", "text": "出力テキスト"},
                            ],
                        }
                    ],
                }
            ],
            "state_fields": [
                {
                    "name": "input",
                    "type": "str",
                    "description": [
                        {"language": "en", "text": "Input text"},
                        {"language": "ja", "text": "入力テキスト"},
                    ],
                },
                {
                    "name": "output",
                    "type": "Output",
                    "description": [
                        {"language": "en", "text": "Output result"},
                        {"language": "ja", "text": "出力結果"},
                    ],
                },
            ],
        }
        with open(agent_dir / "state_model.yml", "w") as f:
            yaml.dump(
                state_model,
                stream=f,
                allow_unicode=True,
                sort_keys=False,
                indent=2,
                default_flow_style=False,
                Dumper=IndentDumper,
            )

        # Create tools directory and files
        tools_dir = agent_dir / "tools"
        tools_dir.mkdir(exist_ok=True)

        # tools/custom_tool.py
        tool_content = '''from typing import Any, Dict
from kagura.core.models import StateModel

async def process(state: StateModel) -> StateModel:
    """
    Process the input state and return updated state
    """
    try:
        # Implement your custom processing logic here
        state.output.text = state.input
        return state
    except Exception as e:
        raise Exception(f"Processing error: {{str(e)}}")
'''
        with open(tools_dir / f"{agent_name}_tool.py", "w") as f:
            f.write(tool_content)

    def _create_test_files(self, root: Path, agent_name: str):
        test_content = f"""import pytest
from kagura.core.agent import Agent

@pytest.mark.asyncio
async def test_{agent_name}():
    agent = Agent.assigner("{agent_name}")
    result = await agent.execute({{"input": "test input"}})
    assert result.SUCCESS
    assert hasattr(result, "output")
    assert hasattr(result.output, "text")
"""
        with open(root / "tests" / agent_name / f"test_{agent_name}.py", "w") as f:
            f.write(test_content)

    def _create_example_files(self, root: Path, agent_name: str):
        example_content = f"""from kagura.core.agent import Agent

async def run_example():
    agent = Agent.assigner("{agent_name}")
    result = await agent.execute({{"input": "example input"}})
    print(result.output.text)

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_example())
"""
        with open(
            root / "examples" / agent_name / f"{agent_name}_example.py", "w"
        ) as f:
            f.write(example_content)

    def _create_project_files(self, root: Path, agent_name: str, description: str):
        # pyproject.toml
        pyproject_content = f"""[tool.poetry]
name = "kagura-{agent_name}"
version = "0.1.0"
description = "{description}"
authors = ["Your Name <your.email@example.com>"]

[tool.poetry.dependencies]
python = "^3.11"
kagura-ai = {{git = "https://github.com/JFK/kagura-ai.git"}}

[tool.poetry.group.dev.dependencies]
pytest = "^8.0.0"
pytest-asyncio = "^0.23.0"
"""
        with open(root / "pyproject.toml", "w") as f:
            f.write(pyproject_content)

        # README.md
        readme_content = f"""# Kagura {agent_name.title()} Agent

{description}

## Installation

```bash
poetry install
```

## Usage

```python
from kagura.core.agent import Agent

async def example():
    agent = Agent.assigner("{agent_name}")
    result = await agent.execute({{"input": "example"}})
    print(result.output.text)
```

## Development

```bash
poetry run pytest
```
"""
        with open(root / "README.md", "w") as f:
            f.write(readme_content)
