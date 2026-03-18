#!/usr/bin/env python3
"""VS Code CLI -- A stateful command-line interface for Visual Studio Code.

This CLI provides comprehensive control over VS Code via its native CLI and
Extension API, enabling agents to:
- Open files, folders, and workspaces
- Install and manage extensions
- Run tasks and debug configurations
- Search files and symbols
- Execute Git operations
- Control the editor (open, edit, navigate)

Usage:
    # One-shot commands
    python3 -m cli_anything.vscode.vscode_cli workspace open ./my-project
    python3 -m cli_anything.vscode.vscode_cli extension install ms-python.python
    python3 -m cli_anything.vscode.vscode_cli task run build

    # Interactive REPL
    python3 -m cli_anything.vscode.vscode_cli repl
"""

import sys
import os
import json
import click
from typing import Optional, List, Dict, Any

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cli_anything.vscode.core.session import Session
from cli_anything.vscode.core import workspace as workspace_mod
from cli_anything.vscode.core import extension as extension_mod
from cli_anything.vscode.core import task as task_mod
from cli_anything.vscode.core import search as search_mod
from cli_anything.vscode.core import git as git_mod
from cli_anything.vscode.core import editor as editor_mod

# Global session state
_session: Optional[Session] = None
_json_output = False
_repl_mode = False


def get_session() -> Session:
    global _session
    if _session is None:
        _session = Session()
    return _session


def output(data: Any, message: str = ""):
    """Output data in human or JSON format."""
    if _json_output:
        click.echo(json.dumps(data, indent=2, default=str))
    else:
        if message:
            click.echo(message)
        if isinstance(data, dict):
            _print_dict(data)
        elif isinstance(data, list):
            _print_list(data)
        elif data is not None:
            click.echo(str(data))


def _print_dict(d: Dict, indent: int = 0):
    prefix = "  " * indent
    for k, v in d.items():
        if isinstance(v, dict):
            click.echo(f"{prefix}{k}:")
            _print_dict(v, indent + 1)
        elif isinstance(v, list):
            click.echo(f"{prefix}{k}:")
            _print_list(v, indent + 1)
        else:
            click.echo(f"{prefix}{k}: {v}")


def _print_list(items: List, indent: int = 0):
    prefix = "  " * indent
    for i, item in enumerate(items):
        if isinstance(item, dict):
            click.echo(f"{prefix}[{i}]")
            _print_dict(item, indent + 1)
        else:
            click.echo(f"{prefix}- {item}")


def handle_error(func):
    """Decorator for consistent error handling."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FileNotFoundError as e:
            if _json_output:
                click.echo(json.dumps({"error": str(e), "type": "file_not_found"}))
            else:
                click.echo(f"Error: {e}", err=True)
            if not _repl_mode:
                sys.exit(1)
        except (ValueError, IndexError, RuntimeError) as e:
            if _json_output:
                click.echo(json.dumps({"error": str(e), "type": type(e).__name__}))
            else:
                click.echo(f"Error: {e}", err=True)
            if not _repl_mode:
                sys.exit(1)
        except FileExistsError as e:
            if _json_output:
                click.echo(json.dumps({"error": str(e), "type": "file_exists"}))
            else:
                click.echo(f"Error: {e}", err=True)
            if not _repl_mode:
                sys.exit(1)
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper


# ── Main CLI Group ──────────────────────────────────────────────
@click.group(invoke_without_command=True)
@click.option("--json", "use_json", is_flag=True, help="Output as JSON")
@click.option("--project", "project_path", type=str, default=None,
              help="Path to .vscode-cli.json project file")
@click.pass_context
def cli(ctx, use_json, project_path):
    """VS Code CLI -- Control Visual Studio Code from the command line.

    Run without a subcommand to enter interactive REPL mode.
    """
    global _json_output
    _json_output = use_json

    if project_path:
        sess = get_session()
        if not sess.has_workspace():
            workspace = workspace_mod.open_workspace(project_path)
            sess.set_workspace(workspace, project_path)

    if ctx.invoked_subcommand is None:
        ctx.invoke(repl, project_path=None)


# ── Workspace Commands ───────────────────────────────────────────
@cli.group()
def workspace():
    """Workspace management commands."""
    pass


@workspace.command("open")
@click.argument("path")
@click.option("--wait", is_flag=True, help="Wait for VS Code to close")
@click.option("--reuse-window", is_flag=True, help="Reuse existing window")
@click.option("--new-window", is_flag=True, help="Open in new window")
@handle_error
def workspace_open(path, wait, reuse_window, new_window):
    """Open a folder or workspace in VS Code."""
    result = workspace_mod.open_in_vscode(
        path,
        wait=wait,
        reuse_window=reuse_window,
        new_window=new_window,
    )
    sess = get_session()
    sess.set_workspace({"path": path}, path)
    output(result, f"Opened: {path}")


@workspace.command("close")
@handle_error
def workspace_close():
    """Close the current workspace."""
    result = workspace_mod.close_workspace()
    sess = get_session()
    sess.clear_workspace()
    output(result, "Workspace closed")


@workspace.command("info")
@handle_error
def workspace_info():
    """Show workspace information."""
    sess = get_session()
    info = workspace_mod.get_workspace_info(sess.get_workspace())
    output(info)


@workspace.command("list")
@handle_error
def workspace_list():
    """List recent workspaces."""
    workspaces = workspace_mod.list_recent_workspaces()
    output(workspaces, "Recent workspaces:")


@workspace.command("save")
@click.argument("path", required=False)
@handle_error
def workspace_save(path):
    """Save the current workspace configuration."""
    sess = get_session()
    saved = sess.save_session(path)
    output({"saved": saved}, f"Saved to: {saved}")


# ── Extension Commands ───────────────────────────────────────────
@cli.group()
def extension():
    """Extension management commands."""
    pass


@extension.command("install")
@click.argument("extension_id")
@click.option("--version", type=str, default=None, help="Specific version")
@click.option("--pre-release", is_flag=True, help="Install pre-release version")
@handle_error
def extension_install(extension_id, version, pre_release):
    """Install a VS Code extension."""
    result = extension_mod.install_extension(
        extension_id,
        version=version,
        pre_release=pre_release,
    )
    output(result, f"Installed: {extension_id}")


@extension.command("uninstall")
@click.argument("extension_id")
@handle_error
def extension_uninstall(extension_id):
    """Uninstall a VS Code extension."""
    result = extension_mod.uninstall_extension(extension_id)
    output(result, f"Uninstalled: {extension_id}")


@extension.command("list")
@click.option("--installed", is_flag=True, help="Show installed extensions")
@click.option("--enabled", is_flag=True, help="Show only enabled extensions")
@click.option("--disabled", is_flag=True, help="Show disabled extensions")
@handle_error
def extension_list(installed, enabled, disabled):
    """List extensions."""
    extensions = extension_mod.list_extensions(
        installed=installed,
        enabled=enabled,
        disabled=disabled,
    )
    output(extensions, "Extensions:")


@extension.command("search")
@click.argument("query")
@click.option("--category", type=str, default=None, help="Filter by category")
@click.option("--limit", type=int, default=20, help="Maximum results")
@handle_error
def extension_search(query, category, limit):
    """Search for extensions in the marketplace."""
    results = extension_mod.search_extensions(
        query,
        category=category,
        limit=limit,
    )
    output(results, f"Search results for '{query}':")


@extension.command("info")
@click.argument("extension_id")
@handle_error
def extension_info(extension_id):
    """Show extension details."""
    info = extension_mod.get_extension_info(extension_id)
    output(info)


# ── Task Commands ────────────────────────────────────────────────
@cli.group()
def task():
    """Task runner commands."""
    pass


@task.command("run")
@click.argument("task_name")
@click.option("--group", type=str, default=None, help="Task group")
@handle_error
def task_run(task_name, group):
    """Run a VS Code task."""
    result = task_mod.run_task(task_name, group=group)
    output(result, f"Running task: {task_name}")


@task.command("list")
@click.option("--group", type=str, default=None, help="Filter by group")
@handle_error
def task_list(group):
    """List available tasks."""
    tasks = task_mod.list_tasks(group=group)
    output(tasks, "Available tasks:")


# ── Search Commands ──────────────────────────────────────────────
@cli.group()
def search():
    """Search commands."""
    pass


@search.command("files")
@click.argument("query")
@click.option("--glob", type=str, default=None, help="File pattern filter")
@click.option("--case-sensitive", is_flag=True, help="Case sensitive search")
@handle_error
def search_files(query, glob, case_sensitive):
    """Search for files by name."""
    results = search_mod.search_files(
        query,
        glob=glob,
        case_sensitive=case_sensitive,
    )
    output(results, f"File search results for '{query}':")


@search.command("content")
@click.argument("query")
@click.option("--glob", type=str, default=None, help="File pattern filter")
@click.option("--case-sensitive", is_flag=True, help="Case sensitive search")
@click.option("--regex", is_flag=True, help="Use regex pattern")
@handle_error
def search_content(query, glob, case_sensitive, regex):
    """Search for content within files."""
    results = search_mod.search_content(
        query,
        glob=glob,
        case_sensitive=case_sensitive,
        regex=regex,
    )
    output(results, f"Content search results for '{query}':")


@search.command("symbols")
@click.argument("query")
@click.option("--file", type=str, default=None, help="Limit to specific file")
@handle_error
def search_symbols(query, file):
    """Search for symbols (functions, classes, etc.)."""
    results = search_mod.search_symbols(query, file=file)
    output(results, f"Symbol search results for '{query}':")


# ── Git Commands ─────────────────────────────────────────────────
@cli.group()
def git():
    """Git integration commands."""
    pass


@git.command("status")
@handle_error
def git_status():
    """Show Git status."""
    status = git_mod.get_status()
    output(status, "Git status:")


@git.command("diff")
@click.option("--staged", is_flag=True, help="Show staged changes")
@click.option("--file", type=str, default=None, help="Show diff for specific file")
@handle_error
def git_diff(staged, file):
    """Show Git diff."""
    diff = git_mod.get_diff(staged=staged, file=file)
    output(diff, "Git diff:")


@git.command("add")
@click.argument("files", nargs=-1)
@click.option("--all", "add_all", is_flag=True, help="Stage all changes")
@handle_error
def git_add(files, add_all):
    """Stage files for commit."""
    result = git_mod.add(files=list(files), all_files=add_all)
    output(result, "Files staged")


@git.command("commit")
@click.option("--message", "-m", required=True, help="Commit message")
@click.option("--amend", is_flag=True, help="Amend previous commit")
@handle_error
def git_commit(message, amend):
    """Create a Git commit."""
    result = git_mod.commit(message=message, amend=amend)
    output(result, f"Committed: {message}")


@git.command("push")
@click.option("--remote", type=str, default="origin", help="Remote name")
@click.option("--branch", type=str, default=None, help="Branch name")
@handle_error
def git_push(remote, branch):
    """Push commits to remote."""
    result = git_mod.push(remote=remote, branch=branch)
    output(result, f"Pushed to {remote}")


@git.command("pull")
@click.option("--remote", type=str, default="origin", help="Remote name")
@click.option("--branch", type=str, default=None, help="Branch name")
@click.option("--rebase", is_flag=True, help="Rebase instead of merge")
@handle_error
def git_pull(remote, branch, rebase):
    """Pull changes from remote."""
    result = git_mod.pull(remote=remote, branch=branch, rebase=rebase)
    output(result, f"Pulled from {remote}")


@git.command("log")
@click.option("--limit", type=int, default=10, help="Number of commits")
@click.option("--oneline", is_flag=True, help="One line per commit")
@handle_error
def git_log(limit, oneline):
    """Show Git commit log."""
    log = git_mod.get_log(limit=limit, oneline=oneline)
    output(log, "Git log:")


@git.command("branch")
@click.argument("branch_name", required=False)
@click.option("--create", is_flag=True, help="Create new branch")
@click.option("--delete", is_flag=True, help="Delete branch")
@click.option("--list", "list_branches", is_flag=True, help="List branches")
@handle_error
def git_branch(branch_name, create, delete, list_branches):
    """Manage Git branches."""
    if list_branches or not branch_name:
        branches = git_mod.list_branches()
        output(branches, "Branches:")
    elif create:
        result = git_mod.create_branch(branch_name)
        output(result, f"Created branch: {branch_name}")
    elif delete:
        result = git_mod.delete_branch(branch_name)
        output(result, f"Deleted branch: {branch_name}")
    else:
        result = git_mod.switch_branch(branch_name)
        output(result, f"Switched to branch: {branch_name}")


# ── Editor Commands ──────────────────────────────────────────────
@cli.group()
def editor():
    """Editor control commands."""
    pass


@editor.command("open")
@click.argument("file_path")
@click.option("--line", type=int, default=None, help="Go to line number")
@click.option("--column", type=int, default=None, help="Go to column number")
@click.option("--wait", is_flag=True, help="Wait for file to close")
@handle_error
def editor_open(file_path, line, column, wait):
    """Open a file in the editor."""
    result = editor_mod.open_file(
        file_path,
        line=line,
        column=column,
        wait=wait,
    )
    output(result, f"Opened: {file_path}")


@editor.command("goto")
@click.argument("file_path")
@click.argument("line", type=int)
@click.option("--column", type=int, default=1, help="Column number")
@handle_error
def editor_goto(file_path, line, column):
    """Navigate to a specific line in a file."""
    result = editor_mod.goto_line(file_path, line, column)
    output(result, f"Navigated to {file_path}:{line}:{column}")


@editor.command("close")
@click.argument("file_path", required=False)
@click.option("--all", "close_all", is_flag=True, help="Close all editors")
@handle_error
def editor_close(file_path, close_all):
    """Close editor(s)."""
    if close_all:
        result = editor_mod.close_all_editors()
        output(result, "Closed all editors")
    else:
        result = editor_mod.close_editor(file_path)
        output(result, f"Closed: {file_path}")


@editor.command("list")
@handle_error
def editor_list():
    """List open editors."""
    editors = editor_mod.list_open_editors()
    output(editors, "Open editors:")


# ── Session Commands ─────────────────────────────────────────────
@cli.group()
def session():
    """Session management commands."""
    pass


@session.command("status")
@handle_error
def session_status():
    """Show session status."""
    sess = get_session()
    output(sess.status())


@session.command("undo")
@handle_error
def session_undo():
    """Undo the last operation."""
    sess = get_session()
    desc = sess.undo()
    output({"undone": desc}, f"Undone: {desc}")


@session.command("redo")
@handle_error
def session_redo():
    """Redo the last undone operation."""
    sess = get_session()
    desc = sess.redo()
    output({"redone": desc}, f"Redone: {desc}")


@session.command("history")
@handle_error
def session_history():
    """Show undo history."""
    sess = get_session()
    history = sess.list_history()
    output(history, "Undo history:")


# ── REPL ─────────────────────────────────────────────────────────
@cli.command()
@click.option("--project", "project_path", type=str, default=None)
@handle_error
def repl(project_path):
    """Start interactive REPL session."""
    from cli_anything.vscode.utils.repl_skin import ReplSkin

    global _repl_mode
    _repl_mode = True

    skin = ReplSkin("vscode", version="1.0.0")

    if project_path:
        sess = get_session()
        workspace = workspace_mod.open_workspace(project_path)
        sess.set_workspace(workspace, project_path)

    skin.print_banner()

    pt_session = skin.create_prompt_session()

    def _get_workspace_name():
        try:
            s = get_session()
            ws = s.get_workspace()
            if ws and isinstance(ws, dict):
                return ws.get("path", "")
        except Exception:
            pass
        return ""

    def _is_modified():
        try:
            s = get_session()
            return s.is_modified() if hasattr(s, "is_modified") else False
        except Exception:
            return False

    while True:
        try:
            line = skin.get_input(
                pt_session,
                project_name=_get_workspace_name(),
                modified=_is_modified(),
            ).strip()
            if not line:
                continue
            if line.lower() in ("quit", "exit", "q"):
                skin.print_goodbye()
                break
            if line.lower() == "help":
                _repl_help(skin)
                continue

            args = line.split()
            try:
                cli.main(args, standalone_mode=False)
            except SystemExit:
                pass
            except click.exceptions.UsageError as e:
                skin.error(f"Usage error: {e}")
            except Exception as e:
                skin.error(str(e))

        except (EOFError, KeyboardInterrupt):
            skin.print_goodbye()
            break

    _repl_mode = False


def _repl_help(skin=None):
    commands = {
        "workspace open|close|info|list|save": "Workspace management",
        "extension install|uninstall|list|search|info": "Extension management",
        "task run|list": "Task runner",
        "search files|content|symbols": "Search operations",
        "git status|diff|add|commit|push|pull|log|branch": "Git integration",
        "editor open|goto|close|list": "Editor control",
        "session status|undo|redo|history": "Session management",
        "help": "Show this help",
        "quit": "Exit REPL",
    }
    if skin is not None:
        skin.help(commands)
    else:
        click.echo("\nCommands:")
        for cmd, desc in commands.items():
            click.echo(f"  {cmd:60s}  {desc}")
        click.echo()


# ── Entry Point ──────────────────────────────────────────────────
def main():
    cli()


if __name__ == "__main__":
    main()