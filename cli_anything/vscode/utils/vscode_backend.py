"""VS Code backend wrapper.

Handles finding and invoking the VS Code CLI.
"""

import shutil
import platform
from typing import Optional


def find_vscode() -> str:
    """Find the VS Code executable.

    Returns:
        Path to the VS Code executable

    Raises:
        RuntimeError: If VS Code is not found
    """
    system = platform.system()

    # Platform-specific executable names
    if system == "Windows":
        candidates = ["code", "code.cmd", "code.exe"]
    elif system == "Darwin":  # macOS
        candidates = ["code", "/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code"]
    else:  # Linux
        candidates = ["code"]

    for candidate in candidates:
        path = shutil.which(candidate)
        if path:
            return path

    # If not found in PATH, try common locations
    common_paths = []

    if system == "Windows":
        common_paths = [
            r"C:\Program Files\Microsoft VS Code\bin\code.cmd",
            r"C:\Program Files\Microsoft VS Code\bin\code",
            r"%LOCALAPPDATA%\Programs\Microsoft VS Code\bin\code.cmd",
            r"%LOCALAPPDATA%\Programs\Microsoft VS Code\bin\code",
        ]
    elif system == "Darwin":
        common_paths = [
            "/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code",
            "/usr/local/bin/code",
        ]
    else:
        common_paths = [
            "/usr/bin/code",
            "/usr/local/bin/code",
            "/snap/bin/code",
        ]

    for path in common_paths:
        # Expand environment variables on Windows
        import os
        expanded_path = os.path.expandvars(path)
        if os.path.exists(expanded_path):
            return expanded_path

    raise RuntimeError(
        "VS Code is not installed or not in PATH.\n"
        "Install VS Code from: https://code.visualstudio.com/download\n"
        "Make sure 'code' command is available in your PATH."
    )


def run_vscode_command(args: list, capture_output: bool = True) -> dict:
    """Run a VS Code command.

    Args:
        args: Command arguments
        capture_output: Whether to capture output

    Returns:
        Result dictionary
    """
    import subprocess

    vscode = find_vscode()
    cmd = [vscode] + args

    result = subprocess.run(
        cmd,
        capture_output=capture_output,
        text=True,
    )

    return {
        "command": " ".join(cmd),
        "returncode": result.returncode,
        "stdout": result.stdout if result.stdout else None,
        "stderr": result.stderr if result.stderr else None,
    }
