"""Session management for VS Code CLI.

Provides stateful session management with undo/redo support.
"""

import json
import os
from typing import Optional, Dict, Any, List
from copy import deepcopy


class Session:
    """Manages the CLI session state including workspace and undo history."""

    def __init__(self):
        self._workspace: Optional[Dict[str, Any]] = None
        self._workspace_path: Optional[str] = None
        self._history: List[Dict[str, Any]] = []
        self._history_index: int = -1
        self._max_history: int = 50

    def has_workspace(self) -> bool:
        """Check if a workspace is currently open."""
        return self._workspace is not None

    def get_workspace(self) -> Dict[str, Any]:
        """Get the current workspace."""
        if self._workspace is None:
            raise RuntimeError("No workspace is currently open")
        return self._workspace

    def set_workspace(self, workspace: Dict[str, Any], path: Optional[str] = None):
        """Set the current workspace."""
        self._workspace = workspace
        self._workspace_path = path
        self._history = []
        self._history_index = -1

    def clear_workspace(self):
        """Clear the current workspace."""
        self._workspace = None
        self._workspace_path = None
        self._history = []
        self._history_index = -1

    def snapshot(self, description: str):
        """Create a snapshot for undo support."""
        if self._workspace is None:
            return

        # Remove any redo history
        self._history = self._history[:self._history_index + 1]

        # Add new snapshot
        snapshot = {
            "description": description,
            "workspace": deepcopy(self._workspace),
        }
        self._history.append(snapshot)

        # Trim history if too long
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

        self._history_index = len(self._history) - 1

    def undo(self) -> str:
        """Undo the last operation."""
        if self._history_index <= 0:
            raise RuntimeError("Nothing to undo")

        self._history_index -= 1
        snapshot = self._history[self._history_index]
        self._workspace = deepcopy(snapshot["workspace"])
        return snapshot["description"]

    def redo(self) -> str:
        """Redo the last undone operation."""
        if self._history_index >= len(self._history) - 1:
            raise RuntimeError("Nothing to redo")

        self._history_index += 1
        snapshot = self._history[self._history_index]
        self._workspace = deepcopy(snapshot["workspace"])
        return snapshot["description"]

    def list_history(self) -> List[Dict[str, Any]]:
        """List the undo history."""
        result = []
        for i, snapshot in enumerate(self._history):
            result.append({
                "index": i,
                "description": snapshot["description"],
                "current": i == self._history_index,
            })
        return result

    def is_modified(self) -> bool:
        """Check if the workspace has been modified."""
        return len(self._history) > 0

    def status(self) -> Dict[str, Any]:
        """Get session status."""
        return {
            "has_workspace": self.has_workspace(),
            "workspace_path": self._workspace_path,
            "history_count": len(self._history),
            "can_undo": self._history_index > 0,
            "can_redo": self._history_index < len(self._history) - 1,
            "modified": self.is_modified(),
        }

    def save_session(self, path: Optional[str] = None) -> str:
        """Save the current session to a file."""
        if path is None:
            path = self._workspace_path

        if path is None:
            raise RuntimeError("No path specified and no workspace path set")

        # Ensure .vscode-cli.json extension
        if not path.endswith(".vscode-cli.json"):
            path = path + ".vscode-cli.json"

        data = {
            "version": "1.0.0",
            "workspace": self._workspace,
            "workspace_path": self._workspace_path,
        }

        with open(path, "w") as f:
            json.dump(data, f, indent=2)

        return path

    def load_session(self, path: str) -> Dict[str, Any]:
        """Load a session from a file."""
        with open(path, "r") as f:
            data = json.load(f)

        self._workspace = data.get("workspace")
        self._workspace_path = data.get("workspace_path")
        self._history = []
        self._history_index = -1

        return self._workspace
