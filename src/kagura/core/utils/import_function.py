import importlib
import os
import sys
from pathlib import Path
from typing import Callable


def import_function(tool_path: str, agent_name: str = None) -> Callable:
    module_name, tool_name = tool_path.rsplit(".", 1)
    user_tools_dir = Path(os.path.expanduser("~")) / ".config" / "kagura" / "tools"
    default_tools_dir = Path(__file__).parent.parent / "tools"  # kagura/tools
    user_agent_tools_dir = (
        (
            Path(os.path.expanduser("~"))
            / ".config"
            / "kagura"
            / "agents"
            / agent_name
            / "tools"
        )
        if agent_name
        else None
    )
    agent_tools_dir = (
        (Path(__file__).parent.parent / "agents" / agent_name / "tools")
        if agent_name
        else None
    )  # kagura / agents / agent_name / tools
    module_search_paths = [
        str(user_tools_dir),
        str(default_tools_dir),
        str(agent_tools_dir),
        str(user_agent_tools_dir),
    ]

    for path in module_search_paths:
        if path not in sys.path and Path(path).exists():
            sys.path.insert(0, path)
    try:
        module = importlib.import_module(module_name)
        return getattr(module, tool_name)
    except ImportError as e:
        raise ImportError(
            f"Failed to import function '{tool_name}' from module '{module_name}'. {str(e)}"
        )
