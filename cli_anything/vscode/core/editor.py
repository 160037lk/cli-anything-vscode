"""Editor control for VS Code CLI.

Handles opening files, navigating to lines, and managing editor state.
"""

import os
import subprocess
from typing import Dict, Any, List, Optional
from ..utils.vscode_backend import find_vscode


def open_file(
    file_path: str,
    line: Optional[int] = None,
    column: Optional[int] = None,
    wait: bool = False,
) -> Dict[str, Any]:
    """Open a file in VS Code.

    Args:
        file_path: Path to the file
        line: Line number to navigate to
        column: Column number to navigate to
        wait: Wait for the file to be closed

    Returns:
        Result dictionary with operation details
    """
    vscode = find_vscode()

    cmd = [vscode]

    if wait:
        cmd.append("--wait")

    # Build the goto argument if line/column specified
    if line is not None:
        goto = f"{line}"
        if column is not None:
            goto = f"{line}:{column}"
        cmd.extend(["--goto", f"{os.path.abspath(file_path)}:{goto}"])
    else:
        cmd.append(os.path.abspath(file_path))

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
    )

    return {
        "file": file_path,
        "line": line,
        "column": column,
        "command": " ".join(cmd),
        "returncode": result.returncode,
        "stdout": result.stdout if result.stdout else None,
        "stderr": result.stderr if result.stderr else None,
    }


def goto_line(file_path: str, line: int, column: int = 1) -> Dict[str, Any]:
    """Navigate to a specific line in a file.

    Args:
        file_path: Path to the file
        line: Line number
        column: Column number

    Returns:
        Result dictionary
    """
    return open_file(file_path, line=line, column=column)


def close_editor(file_path: Optional[str] = None) -> Dict[str, Any]:
    """Close an editor.

    Note: VS Code CLI doesn't have a direct command to close editors.
    This is handled through the VS Code extension API.

    Args:
        file_path: Path to the file to close (None for active editor)

    Returns:
        Result dictionary
    """
    # VS Code CLI doesn't have a direct "close editor" command
    return {
        "status": "info",
        "message": "Use VS Code's keyboard shortcuts (Ctrl+W / Cmd+W) to close editors",
        "file": file_path,
    }


def close_all_editors() -> Dict[str, Any]:
    """Close all editors.

    Returns:
        Result dictionary
    """
    return {
        "status": "info",
        "message": "Use VS Code's keyboard shortcuts (Ctrl+K W / Cmd+K W) to close all editors",
    }


def list_open_editors() -> List[Dict[str, Any]]:
    """List open editors.

    Note: VS Code CLI doesn't expose open editors directly.
    This would require the VS Code extension API.

    Returns:
        List of editor dictionaries
    """
    # VS Code CLI doesn't expose open editors
    return [{
        "status": "info",
        "message": "Open editors can be viewed in VS Code's Explorer sidebar (Ctrl+Shift+E)",
    }]
