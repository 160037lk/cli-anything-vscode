"""Search operations for VS Code CLI.

Handles searching files, content, and symbols.
"""

import os
import subprocess
import fnmatch
from typing import Dict, Any, List, Optional


def search_files(
    query: str,
    glob: Optional[str] = None,
    case_sensitive: bool = False,
) -> List[Dict[str, Any]]:
    """Search for files by name.

    Args:
        query: File name pattern to search for
        glob: File pattern filter (e.g., '*.py')
        case_sensitive: Case sensitive search

    Returns:
        List of matching file dictionaries
    """
    results = []

    # Walk the directory tree
    for root, dirs, files in os.walk("."):
        # Skip common directories to ignore
        dirs[:] = [d for d in dirs if d not in [
            ".git", ".svn", ".hg", "node_modules", "__pycache__",
            ".vscode", ".idea", "dist", "build", ".next", ".nuxt"
        ]]

        for filename in files:
            # Check glob pattern
            if glob and not fnmatch.fnmatch(filename, glob):
                continue

            # Check name match
            match_name = filename if case_sensitive else filename.lower()
            match_query = query if case_sensitive else query.lower()

            if match_query in match_name:
                full_path = os.path.join(root, filename)
                results.append({
                    "name": filename,
                    "path": full_path,
                    "relative_path": os.path.relpath(full_path),
                    "size": os.path.getsize(full_path),
                })

    return results


def search_content(
    query: str,
    glob: Optional[str] = None,
    case_sensitive: bool = False,
    regex: bool = False,
) -> List[Dict[str, Any]]:
    """Search for content within files.

    Args:
        query: Content pattern to search for
        glob: File pattern filter
        case_sensitive: Case sensitive search
        regex: Use regex pattern

    Returns:
        List of match dictionaries with file and line info
    """
    import re

    results = []

    # Compile regex if needed
    if regex:
        flags = 0 if case_sensitive else re.IGNORECASE
        try:
            pattern = re.compile(query, flags)
        except re.error as e:
            return [{"error": f"Invalid regex: {e}"}]
    else:
        query_lower = query.lower()

    # Walk the directory tree
    for root, dirs, files in os.walk("."):
        # Skip common directories
        dirs[:] = [d for d in dirs if d not in [
            ".git", ".svn", ".hg", "node_modules", "__pycache__",
            ".vscode", ".idea", "dist", "build", ".next", ".nuxt"
        ]]

        for filename in files:
            # Check glob pattern
            if glob and not fnmatch.fnmatch(filename, glob):
                continue

            # Skip binary files
            if _is_binary_file(filename):
                continue

            full_path = os.path.join(root, filename)

            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line_num, line in enumerate(f, 1):
                        if regex:
                            matches = pattern.finditer(line)
                            for match in matches:
                                results.append({
                                    "file": full_path,
                                    "relative_path": os.path.relpath(full_path),
                                    "line": line_num,
                                    "column": match.start() + 1,
                                    "match": match.group(),
                                    "context": line.strip(),
                                })
                        else:
                            line_check = line if case_sensitive else line.lower()
                            if query_lower in line_check:
                                results.append({
                                    "file": full_path,
                                    "relative_path": os.path.relpath(full_path),
                                    "line": line_num,
                                    "column": line_check.find(query_lower) + 1,
                                    "match": query,
                                    "context": line.strip(),
                                })
            except Exception:
                continue

    return results


def search_symbols(query: str, file: Optional[str] = None) -> List[Dict[str, Any]]:
    """Search for symbols (functions, classes, etc.).

    This is a basic implementation using regex patterns.
    For more accurate results, consider using language servers.

    Args:
        query: Symbol name pattern
        file: Limit to specific file

    Returns:
        List of symbol dictionaries
    """
    import re

    results = []

    # Define symbol patterns for common languages
    symbol_patterns = {
        ".py": [
            (r'^\s*(?:async\s+)?def\s+([a-zA-Z_][a-zA-Z0-9_]*)', 'function'),
            (r'^\s*class\s+([a-zA-Z_][a-zA-Z0-9_]*)', 'class'),
        ],
        ".js": [
            (r'(?:function\s+([a-zA-Z_][a-zA-Z0-9_]*)|(?:const|let|var)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(?:async\s+)?function|([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)\s*\{)', 'function'),
            (r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)', 'class'),
        ],
        ".ts": [
            (r'(?:function\s+([a-zA-Z_][a-zA-Z0-9_]*)|(?:const|let|var)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(?:async\s+)?function|([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)\s*(:\s*\w+)?\s*\{)', 'function'),
            (r'(?:export\s+)?(?:abstract\s+)?class\s+([a-zA-Z_][a-zA-Z0-9_]*)', 'class'),
            (r'interface\s+([a-zA-Z_][a-zA-Z0-9_]*)', 'interface'),
        ],
        ".java": [
            (r'(?:public|private|protected|static|\s)+[\w<>\[\]]+\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)', 'method'),
            (r'(?:public\s+)?(?:abstract\s+)?class\s+([a-zA-Z_][a-zA-Z0-9_]*)', 'class'),
            (r'interface\s+([a-zA-Z_][a-zA-Z0-9_]*)', 'interface'),
        ],
        ".c": [
            (r'^\s*(?:static\s+)?(?:\w+\s+)+([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)\s*\{', 'function'),
        ],
        ".cpp": [
            (r'^\s*(?:static\s+)?(?:\w+::)?(?:\w+\s+)+([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)', 'function'),
            (r'(?:class|struct)\s+([a-zA-Z_][a-zA-Z0-9_]*)', 'class'),
        ],
        ".go": [
            (r'^\s*func\s+(?:\([^)]*\)\s+)?([a-zA-Z_][a-zA-Z0-9_]*)', 'function'),
            (r'^\s*type\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+(?:struct|interface)', 'type'),
        ],
        ".rs": [
            (r'^\s*(?:pub\s+)?fn\s+([a-zA-Z_][a-zA-Z0-9_]*)', 'function'),
            (r'^\s*(?:pub\s+)?struct\s+([a-zA-Z_][a-zA-Z0-9_]*)', 'struct'),
            (r'^\s*(?:pub\s+)?trait\s+([a-zA-Z_][a-zA-Z0-9_]*)', 'trait'),
        ],
    }

    files_to_search = []

    if file:
        if os.path.exists(file):
            files_to_search.append(file)
    else:
        # Search all source files
        for root, dirs, files in os.walk("."):
            dirs[:] = [d for d in dirs if d not in [
                ".git", "node_modules", "__pycache__", ".vscode", ".idea",
                "dist", "build", ".next", ".nuxt", "target", "bin", "obj"
            ]]

            for filename in files:
                ext = os.path.splitext(filename)[1]
                if ext in symbol_patterns:
                    files_to_search.append(os.path.join(root, filename))

    for filepath in files_to_search:
