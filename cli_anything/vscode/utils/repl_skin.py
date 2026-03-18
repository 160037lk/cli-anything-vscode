"""Unified REPL skin for VS Code CLI.

Provides a consistent, branded REPL interface.
"""

import os
from typing import Optional, Dict, Any


class ReplSkin:
    """Unified REPL skin for CLI-Anything tools."""

    def __init__(self, name: str, version: str = "1.0.0"):
        self.name = name
        self.version = version
        self._setup_colors()

    def _setup_colors(self):
        """Setup ANSI color codes."""
        # Check if terminal supports colors
        if os.environ.get("NO_COLOR") or not os.environ.get("TERM"):
            self.colors = {
                "reset": "",
                "bold": "",
                "dim": "",
                "red": "",
                "green": "",
                "yellow": "",
                "blue": "",
                "magenta": "",
                "cyan": "",
                "white": "",
            }
        else:
            self.colors = {
                "reset": "\033[0m",
                "bold": "\033[1m",
                "dim": "\033[2m",
                "red": "\033[31m",
                "green": "\033[32m",
                "yellow": "\033[33m",
                "blue": "\033[34m",
                "magenta": "\033[35m",
                "cyan": "\033[36m",
                "white": "\033[37m",
            }

    def print_banner(self):
        """Print the REPL banner."""
        c = self.colors
        print()
        print(f"{c['cyan']}{'─' * 50}{c['reset']}")
        print(f"{c['bold']}{c['blue']}  VS Code CLI{c['reset']} {c['dim']}v{self.version}{c['reset']}")
        print(f"{c['cyan']}{'─' * 50}{c['reset']}")
        print(f"{c['dim']}  Type 'help' for commands, 'quit' to exit{c['reset']}")
        print()

    def print_goodbye(self):
        """Print the goodbye message."""
        c = self.colors
        print()
        print(f"{c['dim']}Goodbye!{c['reset']}")
        print()

    def create_prompt_session(self):
        """Create a prompt_toolkit session."""
        try:
            from prompt_toolkit import PromptSession
            from prompt_toolkit.history import FileHistory
            from prompt_toolkit.styles import Style

            history_file = os.path.expanduser(f"~/.cli-anything-{self.name}-history")

            style = Style.from_dict({
                "prompt": "#00a4e4 bold",
                "": "#ffffff",
            })

            return PromptSession(
                history=FileHistory(history_file),
                style=style,
            )
        except ImportError:
            return None

    def get_input(self, pt_session, project_name: str = "", modified: bool = False) -> str:
        """Get input from the user."""
        c = self.colors

        # Build prompt
        prompt_parts = [f"{c['blue']}vscode{c['reset']}"]

        if project_name:
            display_name = os.path.basename(project_name) if os.path.sep in project_name else project_name
            prompt_parts.append(f"{c['cyan']}{display_name}{c['reset']}")

        if modified:
            prompt_parts.append(f"{c['yellow']}*{c['reset']}")

        prompt = " ".join(prompt_parts) + f" {c['dim']}>{c['reset']} "

        if pt_session:
            try:
                return pt_session.prompt(prompt)
            except Exception:
                pass

        # Fallback to built-in input
        return input(f"vscode> ")

    def help(self, commands: Dict[str, str]):
        """Print help text."""
        c = self.colors
        print()
        print(f"{c['bold']}Available Commands:{c['reset']}")
        print()

        for cmd, desc in commands.items():
            print(f"  {c['cyan']}{cmd:50s}{c['reset']} {desc}")

        print()

    def success(self, message: str):
        """Print a success message."""
        c = self.colors
        print(f"{c['green']}✓{c['reset']} {message}")

    def error(self, message: str):
        """Print an error message."""
        c = self.colors
        print(f"{c['red']}✗{c['reset']} {message}")

    def warning(self, message: str):
        """Print a warning message."""
        c = self.colors
        print(f"{c['yellow']}⚠{c['reset']} {message}")

    def info(self, message: str):
        """Print an info message."""
        c = self.colors
        print(f"{c['blue']}●{c['reset']} {message}")

    def status(self, key: str, value: str):
        """Print a key-value status line."""
        c = self.colors
        print(f"  {c['dim']}{key}:{c['reset']} {value}")

    def table(self, headers: list, rows: list):
        """Print a formatted table."""
        if not rows:
            return

        # Calculate column widths
        widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                widths[i] = max(widths[i], len(str(cell)))

        # Print headers
        header_line = "  ".join(
            h.ljust(w) for h, w in zip(headers, widths)
        )
        print(header_line)
        print("-" * len(header_line))

        # Print rows
        for row in rows:
            print("  ".join(
                str(cell).ljust(w) for cell, w in zip(row, widths)
            ))

    def progress(self, current: int, total: int, message: str = ""):
        """Print a progress bar."""
        c = self.colors
        width = 30
        filled = int(width * current / total) if total > 0 else 0
        bar = f"{'█' * filled}{'░' * (width - filled)}"
        pct = int(100 * current / total) if total > 0 else 0
        print(f"\r{c['blue']}{bar}{c['reset']} {pct}% {message}", end="", flush=True)
        if current >= total:
            print()
