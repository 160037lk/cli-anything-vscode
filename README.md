# VS Code CLI - Agent-Usable Command Line Interface

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A **stateful**, **agent-usable** command-line interface for Visual Studio Code, built with the [CLI-Anything](https://github.com/HKUDS/CLI-Anything) methodology.

## 🎯 Purpose

This CLI enables AI agents and automation tools to control VS Code programmatically without needing a display or mouse. It wraps VS Code's native CLI and provides a structured interface for common development workflows.

## ✨ Features

- **🗂️ Workspace Management** - Open, close, and manage VS Code workspaces
- **📦 Extension Management** - Install, uninstall, search, and list extensions
- **⚡ Task Runner** - Execute VS Code tasks defined in `tasks.json`
- **🔍 Smart Search** - Search files, content, and code symbols across projects
- **🌿 Git Integration** - Full Git workflow (status, diff, commit, push, pull, branches)
- **📝 Editor Control** - Open files, navigate to specific lines, manage editors
- **↩️ Session Management** - Undo/redo support with persistent state
- **💻 REPL Mode** - Interactive shell for complex workflows
- **📤 JSON Output** - Machine-readable output for agent consumption

## 📋 Prerequisites

- **Python** 3.10 or higher
- **Visual Studio Code** installed with `code` command in PATH

### Check VS Code CLI

```bash
code --version
# Should output something like:
# 1.85.0
# af28b32d7e553898b2a91af498b1fb666fdebe0c
# x64
```

If `code` is not found, see [VS Code CLI documentation](https://code.visualstudio.com/docs/editor/command-line).

## 🚀 Installation

### From Source

```bash
# Clone or download this repository
git clone https://github.com/YOUR_USERNAME/cli-anything-vscode.git
cd cli-anything-vscode

# Install in editable mode
pip install -e .

# Or install normally
pip install .
```

### Verify Installation

```bash
cli-anything-vscode --help
```

## 📖 Usage

### Quick Start

```bash
# Open a project
cli-anything-vscode workspace open ./my-project

# Install Python extension
cli-anything-vscode extension install ms-python.python

# Check Git status
cli-anything-vscode git status

# Open a file at line 10
cli-anything-vscode editor open main.py --line 10
```

### Interactive REPL Mode

```bash
# Start REPL
cli-anything-vscode

# Or explicitly
cli-anything-vscode repl
```

In REPL mode:
```
──────────────────────────────────────────────────
  VS Code CLI v1.0.0
──────────────────────────────────────────────────
  Type 'help' for commands, 'quit' to exit

vscode my-project > workspace open ./my-project
vscode my-project > extension list
vscode my-project > git status
vscode my-project > quit
```

### JSON Output for Agents

Add `--json` flag to any command for machine-readable output:

```bash
cli-anything-vscode --json git status
cli-anything-vscode --json extension list
cli-anything-vscode --json search files "*.py"
```

## 📚 Command Reference

### Workspace Commands

| Command | Description | Example |
|---------|-------------|---------|
| `workspace open <path>` | Open a folder or workspace | `workspace open ./my-project` |
| `workspace close` | Close current workspace | `workspace close` |
| `workspace info` | Show workspace information | `workspace info` |
| `workspace list` | List recent workspaces | `workspace list` |
| `workspace save [path]` | Save workspace configuration | `workspace save my-project.json` |

**Options:**
- `--wait` - Wait for VS Code to close
- `--reuse-window` - Reuse existing window
- `--new-window` - Open in new window

### Extension Commands

| Command | Description | Example |
|---------|-------------|---------|
| `extension install <id>` | Install an extension | `extension install ms-python.python` |
| `extension uninstall <id>` | Uninstall an extension | `extension uninstall ms-python.python` |
| `extension list` | List installed extensions | `extension list` |
| `extension search <query>` | Search marketplace | `extension search python` |
| `extension info <id>` | Show extension details | `extension info ms-python.python` |

**Options:**
- `--version` - Install specific version
- `--pre-release` - Install pre-release version

### Task Commands

| Command | Description | Example |
|---------|-------------|---------|
| `task run <name>` | Run a VS Code task | `task run build` |
| `task list` | List available tasks | `task list` |

### Search Commands

| Command | Description | Example |
|---------|-------------|---------|
| `search files <query>` | Search for files | `search files "*.py"` |
| `search content <query>` | Search file content | `search content "TODO"` |
| `search symbols <query>` | Search code symbols | `search symbols "MyClass"` |

**Options:**
- `--glob` - File pattern filter (e.g., `*.py`)
- `--case-sensitive` - Case sensitive search
- `--regex` - Use regex pattern (for content search)

### Git Commands

| Command | Description | Example |
|---------|-------------|---------|
| `git status` | Show Git status | `git status` |
| `git diff` | Show diff | `git diff` |
| `git add [files...]` | Stage files | `git add main.py` or `git add --all` |
| `git commit -m <msg>` | Create commit | `git commit -m "Update"` |
| `git push` | Push to remote | `git push` |
| `git pull` | Pull from remote | `git pull` |
| `git log` | Show commit log | `git log --limit 20` |
| `git branch` | Manage branches | `git branch feature-x --create` |

### Editor Commands

| Command | Description | Example |
|---------|-------------|---------|
| `editor open <file>` | Open a file | `editor open main.py` |
| `editor goto <file> <line>` | Navigate to line | `editor goto main.py 10` |
| `editor close [file]` | Close editor | `editor close main.py` |
| `editor list` | List open editors | `editor list` |

**Options:**
- `--line` - Go to line number
- `--column` - Go to column number
- `--wait` - Wait for file to close

### Session Commands

| Command | Description | Example |
|---------|-------------|---------|
| `session status` | Show session status | `session status` |
| `session undo` | Undo last operation | `session undo` |
| `session redo` | Redo last undone | `session redo` |
| `session history` | Show undo history | `session history` |

## 🏗️ Architecture

This CLI follows the [CLI-Anything](https://github.com/HKUDS/CLI-Anything) methodology:

```
┌─────────────────────────────────────────────────────────┐
│                    VS Code CLI                          │
├─────────────────────────────────────────────────────────┤
│  REPL Mode │ Subcommand Mode │ JSON Output              │
├─────────────────────────────────────────────────────────┤
│  Session Management (undo/redo, state persistence)      │
├─────────────────────────────────────────────────────────┤
│  Core Modules                                           │
│  ├── workspace.py  - Workspace operations               │
│  ├── extension.py  - Extension management               │
│  ├── task.py       - Task runner                        │
│  ├── search.py     - Search operations                  │
│  ├── git.py        - Git integration                    │
│  └── editor.py     - Editor control                     │
├─────────────────────────────────────────────────────────┤
│  Backend                                                │
│  └── vscode_backend.py - VS Code CLI wrapper            │
└─────────────────────────────────────────────────────────┘
```

## 🧪 Testing

```bash
# Run all tests
python -m pytest cli_anything/vscode/tests/ -v

# Run unit tests only
python -m pytest cli_anything/vscode/tests/test_core.py -v

# Run E2E tests
python -m pytest cli_anything/vscode/tests/test_full_e2e.py -v
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built with the [CLI-Anything](https://github.com/HKUDS/CLI-Anything) methodology
- Uses [Click](https://click.palletsprojects.com/) for CLI framework
- Uses [prompt-toolkit](https://python-prompt-toolkit.readthedocs.io/) for REPL

## 📞 Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/YOUR_USERNAME/cli-anything-vscode/issues) page
2. Create a new issue with details about your problem
3. Include your OS, Python version, and VS Code version

---

**Made with ❤️ for AI agents and developers alike**