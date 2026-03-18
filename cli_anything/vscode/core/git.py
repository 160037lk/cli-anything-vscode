"""Git integration for VS Code CLI.

Provides Git operations that integrate with VS Code's Git features.
"""

import subprocess
from typing import Dict, Any, List, Optional


def _run_git_command(args: List[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a git command and return the result."""
    return subprocess.run(
        ["git"] + args,
        capture_output=True,
        text=True,
        check=check,
    )


def get_status() -> Dict[str, Any]:
    """Get Git repository status.

    Returns:
        Status dictionary with branch, changes, and other info
    """
    try:
        # Get current branch
        branch_result = _run_git_command(["branch", "--show-current"], check=False)
        branch = branch_result.stdout.strip() if branch_result.returncode == 0 else "unknown"

        # Get status in porcelain format
        status_result = _run_git_command(["status", "--porcelain"], check=False)

        changes = {
            "staged": [],
            "unstaged": [],
            "untracked": [],
        }

        if status_result.returncode == 0:
            for line in status_result.stdout.strip().split("\n"):
                if not line:
                    continue

                status_code = line[:2]
                file_path = line[3:]

                if status_code[0] != " ":
                    # Staged changes
                    changes["staged"].append({
                        "file": file_path,
                        "status": _parse_status_code(status_code[0]),
                    })

                if status_code[1] != " ":
                    if status_code[1] == "?":
                        changes["untracked"].append({"file": file_path})
                    else:
                        changes["unstaged"].append({
                            "file": file_path,
                            "status": _parse_status_code(status_code[1]),
                        })

        # Get ahead/behind info
        ahead_behind_result = _run_git_command(
            ["rev-list", "--left-right", "--count", f"HEAD...{branch}@{u}"],
            check=False,
        )
        ahead = 0
        behind = 0
        if ahead_behind_result.returncode == 0:
            counts = ahead_behind_result.stdout.strip().split("\t")
            if len(counts) == 2:
                ahead = int(counts[0])
                behind = int(counts[1])

        return {
            "branch": branch,
            "changes": changes,
            "ahead": ahead,
            "behind": behind,
            "is_clean": len(changes["staged"]) == 0 and len(changes["unstaged"]) == 0 and len(changes["untracked"]) == 0,
        }

    except Exception as e:
        return {"error": str(e), "message": "Failed to get Git status"}


def _parse_status_code(code: str) -> str:
    """Parse Git status code to human-readable string."""
    status_map = {
        "M": "modified",
        "A": "added",
        "D": "deleted",
        "R": "renamed",
        "C": "copied",
        "U": "updated but unmerged",
        "?": "untracked",
        "!": "ignored",
    }
    return status_map.get(code, "unknown")


def get_diff(staged: bool = False, file: Optional[str] = None) -> Dict[str, Any]:
    """Get Git diff.

    Args:
        staged: Show staged changes
        file: Show diff for specific file

    Returns:
        Diff dictionary with changes
    """
    try:
        args = ["diff"]
        if staged:
            args.append("--staged")
        if file:
            args.append(file)

        result = _run_git_command(args, check=False)

        return {
            "staged": staged,
            "file": file,
            "diff": result.stdout if result.returncode == 0 else result.stderr,
            "has_changes": len(result.stdout.strip()) > 0,
        }

    except Exception as e:
        return {"error": str(e), "message": "Failed to get diff"}


def add(files: List[str], all_files: bool = False) -> Dict[str, Any]:
    """Stage files for commit.

    Args:
        files: List of files to stage
        all_files: Stage all changes

    Returns:
        Result dictionary
    """
    try:
        if all_files:
            result = _run_git_command(["add", "."])
            return {
                "action": "add_all",
                "success": result.returncode == 0,
                "output": result.stdout if result.stdout else None,
            }
        elif files:
            result = _run_git_command(["add"] + files)
            return {
                "action": "add",
                "files": files,
                "success": result.returncode == 0,
                "output": result.stdout if result.stdout else None,
            }
        else:
            return {"error": "No files specified and --all not set"}

    except Exception as e:
        return {"error": str(e), "message": "Failed to stage files"}


def commit(message: str, amend: bool = False) -> Dict[str, Any]:
    """Create a Git commit.

    Args:
        message: Commit message
        amend: Amend previous commit

    Returns:
        Result dictionary
    """
    try:
        args = ["commit", "-m", message]
        if amend:
            args.append("--amend")

        result = _run_git_command(args, check=False)

        return {
            "message": message,
            "amend": amend,
            "success": result.returncode == 0,
            "output": result.stdout if result.stdout else None,
            "error": result.stderr if result.stderr else None,
        }

    except Exception as e:
        return {"error": str(e), "message": "Failed to commit"}


def push(remote: str = "origin", branch: Optional[str] = None) -> Dict[str, Any]:
    """Push commits to remote.

    Args:
        remote: Remote name
        branch: Branch name (defaults to current)

    Returns:
        Result dictionary
    """
    try:
        args = ["push", remote]
        if branch:
            args.append(branch)

        result = _run_git_command(args, check=False)

        return {
            "remote": remote,
            "branch": branch,
            "success": result.returncode == 0,
            "output": result.stdout if result.stdout else None,
            "error": result.stderr if result.stderr else None,
        }

    except Exception as e:
        return {"error": str(e), "message": "Failed to push"}


def pull(remote: str = "origin", branch: Optional[str] = None, rebase: bool = False) -> Dict[str, Any]:
    """Pull changes from remote.

    Args:
        remote: Remote name
        branch: Branch name
        rebase: Rebase instead of merge

    Returns:
        Result dictionary
    """
    try:
        args = ["pull", remote]
        if rebase:
            args.append("--rebase")
        if branch:
            args.append(branch)

        result = _run_git_command(args, check=False)

        return {
            "remote": remote,
            "branch": branch,
            "rebase": rebase,
            "success": result.returncode == 0,
            "output": result.stdout if result.stdout else None,
            "error": result.stderr if result.stderr else None,
        }

    except Exception as e:
        return {"error": str(e), "message": "Failed to pull"}


def get_log(limit: int = 10, oneline: bool = False) -> List[Dict[str, Any]]:
    """Get Git commit log.

    Args:
        limit: Number of commits to show
        oneline: Show one line per commit

    Returns:
        List of commit dictionaries
    """
    try:
        args = ["log", f"-{limit}", "--pretty=format:%H|%an|%ae|%ad|%s"]
        if oneline:
            args = ["log", f"-{limit}", "--oneline"]

        result = _run_git_command(args, check=False)

        commits = []
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            for line in lines:
                if not line:
                    continue

                if oneline:
                    # Parse oneline format: "hash message"
                    parts = line.split(" ", 1)
                    commits.append({
                        "hash": parts[0] if parts else "",
                        "message": parts[1] if len(parts) > 1 else "",
                    })
                else:
                    # Parse detailed format
                    parts = line.split("|", 4)
                    if len(parts) >= 5:
                        commits.append({
                            "hash": parts[0],
                            "author": parts[1],
                            "email": parts[2],
                            "date": parts[3],
                            "message": parts[4],
                        })

        return commits

    except Exception as e:
        return [{"error": str(e), "message": "Failed to get log"}]


def list_branches() -> List[Dict[str, Any]]:
    """List Git branches.

    Returns:
        List of branch dictionaries
    """
    try:
        result = _run_git_command(["branch", "-vv"], check=False)

        branches = []
        if result.returncode == 0:
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue

                current = line.startswith("*")
                line = line[2:] if current else line[2:]

                parts = line.split()
                name = parts[0] if parts else ""
                commit = parts[1] if len(parts) > 1 else ""
                message = " ".join(parts[2:]) if len(parts) > 2 else ""

                branches.append({
                    "name": name,
                    "current": current,
                    "commit": commit,
                    "message": message,
                })

        return branches

    except Exception as e:
        return [{"error": str(e), "message": "Failed to list branches"}]


def create_branch(branch_name: str) -> Dict[str, Any]:
    """Create a new Git branch.

    Args:
        branch_name: Name of the new branch

    Returns:
        Result dictionary
    """
    try:
        result = _run_git_command(["checkout", "-b", branch_name], check=False)

        return {
            "branch": branch_name,
            "success": result.returncode == 0,
            "output": result.stdout if result.stdout else None,
            "error": result.stderr if result.stderr else None,
        }

    except Exception as e:
        return {"error": str(e), "message": "Failed to create branch"}


def delete_branch(branch_name: str) -> Dict[str, Any]:
    """Delete a Git branch.

    Args:
        branch_name: Name of the branch to delete

    Returns:
        Result dictionary
    """
    try:
        result = _run_git_command(["branch", "-d", branch_name], check=False)

        return {
            "branch": branch_name,
            "success": result.returncode == 0,
            "output": result.stdout if result.stdout else None,
            "error": result.stderr if result.stderr else None,
        }

    except Exception as e:
        return {"error": str(e), "message": "Failed to delete branch"}


def switch_branch(branch_name: str) -> Dict[str, Any]:
    """Switch to a Git branch.

    Args:
        branch_name: Name of the branch to switch to

    Returns:
        Result dictionary
    """
    try:
        result = _run_git_command(["checkout", branch_name], check=False)

        return {
            "branch": branch_name,
            "success": result.returncode == 0,
            "output": result.stdout if result.stdout else None,
            "error": result.stderr if result.stderr else None,
        }

    except Exception as e:
        return {"error": str(e), "message": "Failed to switch branch"}
