"""Workspace management for VS Code CLI.

Handles opening folders/workspaces and retrieving workspace information.
"""

import os
import json
import subprocess
from typing import Dict, Any, List, Optional
from ..utils.vscode_backend import find_vscode, run_vscode_command


def open_in_vscode(
    path: str,
    wait: bool = False,
    reuse_window: bool = False,
    new_window: bool = False,
) -> Dict[str, Any]:
    """Open a folder or workspace in VS Code.

    Args:
        path: Path to folder or workspace file
        wait: Wait for VS Code to close
        reuse_window: Reuse existing window
        new_window: Open in new window

    Returns:
        Result dictionary with operation details
    """
    vscode = find_vscode()

    cmd = [vscode]

    if wait:
        cmd.append("--wait")
    if reuse_window:
        cmd.append("--reuse-window")
    if new_window:
        cmd.append("--new-window")

    cmd.append(os.path.abspath(path))

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
    )

    return {
        "path": path,
        "command": " ".join(cmd),
        "returncode": result.returncode,
        "stdout": result.stdout if result.stdout else None,
        "stderr": result.stderr if result.stderr else None,
    }


def close_workspace() -> Dict[str, Any]:
    """Close the current workspace.

    Note: VS Code doesn't have a direct CLI command to close workspaces.
    This sends a command to close the current window.

    Returns:
        Result dictionary
    """
    # VS Code doesn't have a direct "close workspace" CLI command
    # We can only close the window via keyboard shortcut or window manager
    return {
        "status": "info",
        "message": "Use 'code --status' to check VS Code status. To close, use window manager or Ctrl+Q/Cmd+Q.",
    }


def get_workspace_info(workspace: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Get information about the current workspace.

    Args:
        workspace: Current workspace dictionary

    Returns:
        Workspace information dictionary
    """
    if workspace is None:
        return {
            "status": "no_workspace",
            "message": "No workspace is currently open",
        }

    path = workspace.get("path", "")

    info = {
        "path": path,
        "name": os.path.basename(path) if path else "",
        "type": "workspace" if path.endswith(".code-workspace") else "folder",
        "exists": os.path.exists(path) if path else False,
    }

    # Try to get VS Code status
    try:
        vscode = find_vscode()
        result = subprocess.run(
            [vscode, "--status"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            info["vscode_status"] = result.stdout.strip()
    except Exception:
        pass

    return info


def list_recent_workspaces() -> List[Dict[str, Any]]:
    """List recent VS Code workspaces.

    Reads VS Code's state database to get recent folders and workspaces.

    Returns:
        List of recent workspace dictionaries
    """
    workspaces = []

    # Try to read VS Code's state.vscdb
    state_paths = [
        # macOS
        os.path.expanduser("~/Library/Application Support/Code/User/globalStorage/state.vscdb"),
        # Linux
        os.path.expanduser("~/.config/Code/User/globalStorage/state.vscdb"),
        # Windows
        os.path.expanduser("~/AppData/Roaming/Code/User/globalStorage/state.vscdb"),
    ]

    for state_path in state_paths:
        if os.path.exists(state_path):
            try:
                # state.vscdb is a SQLite database
                import sqlite3
                conn = sqlite3.connect(state_path)
                cursor = conn.cursor()

                # Query for recent folders
                cursor.execute("SELECT key, value FROM ItemTable WHERE key LIKE 'history.recent%' OR key LIKE 'history.workspace%'")
                rows = cursor.fetchall()

                for key, value in rows:
                    try:
                        data = json.loads(value)
                        if isinstance(data, list):
                            for item in data:
                                if isinstance(item, dict):
                                    workspaces.append({
                                        "path": item.get("path", ""),
                                        "name": os.path.basename(item.get("path", "")),
                                        "type": "workspace" if item.get("path", "").endswith(".code-workspace") else "folder",
                                    })
                    except json.JSONDecodeError:
                        continue

                conn.close()
            except Exception:
                pass

    # Remove duplicates while preserving order
    seen = set()
    unique_workspaces = []
    for ws in workspaces:
        path = ws.get("path", "")
        if path and path not in seen:
            seen.add(path)
            unique_workspaces.append(ws)

    return unique_workspaces[:20]  # Limit to 20 most recent


def open_workspace(path: str) -> Dict[str, Any]:
    """Open a workspace file and return its configuration.

    Args:
        path: Path to .code-workspace file

    Returns:
        Workspace configuration dictionary
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Workspace file not found: {path}")

    if path.endswith(".code-workspace"):
        with open(path, "r") as f:
            config = json.load(f)
        return {
            "path": path,
            "config": config,
            "folders": config.get("folders", []),
            "settings": config.get("settings", {}),
        }
    else:
        # It's a folder, not a workspace file
        return {
            "path": path,
            "config": {},
            "folders": [{"path": path}],
            "settings": {},
        }
