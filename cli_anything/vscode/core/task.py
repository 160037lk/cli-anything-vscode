"""Task runner for VS Code CLI.

Handles running VS Code tasks defined in tasks.json.
"""

import os
import json
import subprocess
from typing import Dict, Any, List, Optional
from ..utils.vscode_backend import find_vscode


def run_task(task_name: str, group: Optional[str] = None) -> Dict[str, Any]:
    """Run a VS Code task.

    Note: VS Code CLI doesn't have a direct task run command.
    This uses the VS Code CLI to trigger tasks via the extension API.

    Args:
        task_name: Name of the task to run
        group: Task group (build, test, etc.)

    Returns:
        Result dictionary with operation details
    """
    vscode = find_vscode()

    # VS Code doesn't have a direct CLI command to run tasks
    # We need to use the extension API or open VS Code with a specific configuration
    # For now, we'll provide instructions

    return {
        "task_name": task_name,
        "group": group,
        "status": "info",
        "message": f"To run task '{task_name}', use VS Code's command palette (Ctrl+Shift+P) and type 'Run Task'",
        "alternative": f"Or use: {vscode} --goto <workspace> and then run tasks from the Terminal menu",
    }


def list_tasks(group: Optional[str] = None) -> List[Dict[str, Any]]:
    """List available VS Code tasks.

    Reads tasks.json from the workspace to find available tasks.

    Args:
        group: Filter by task group

    Returns:
        List of task dictionaries
    """
    tasks = []

    # Look for tasks.json in common locations
    task_file_paths = [
        ".vscode/tasks.json",
        ".vscode/tasks.jsonc",
    ]

    for task_file in task_file_paths:
        if os.path.exists(task_file):
            try:
                with open(task_file, "r") as f:
                    content = f.read()

                # Remove comments for JSON parsing (tasks.json supports comments)
                import re
                content = re.sub(r'//.*$', '', content, flags=re.MULTILINE)
                content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)

                config = json.loads(content)

                for task in config.get("tasks", []):
                    task_info = {
                        "label": task.get("label", ""),
                        "type": task.get("type", ""),
                        "command": task.get("command", ""),
                        "group": task.get("group", ""),
                        "detail": task.get("detail", ""),
                    }

                    if group and task_info["group"] != group:
                        continue

                    tasks.append(task_info)

            except (json.JSONDecodeError, Exception) as e:
                return [{"error": str(e), "message": f"Failed to parse {task_file}"}]

    # Also check for npm scripts if package.json exists
    if os.path.exists("package.json"):
        try:
            with open("package.json", "r") as f:
                package = json.load(f)

            scripts = package.get("scripts", {})
            for name, command in scripts.items():
                tasks.append({
                    "label": f"npm: {name}",
                    "type": "npm",
                    "command": command,
                    "group": "build" if name in ["build", "compile"] else "test" if name in ["test"] else "",
                })
        except Exception:
            pass

    return tasks
