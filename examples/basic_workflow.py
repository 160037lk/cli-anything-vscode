"""Example: Basic VS Code CLI Workflow

This script demonstrates a typical workflow using the VS Code CLI.
"""

import subprocess
import sys
import os

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cli_anything.vscode.core.workspace import open_in_vscode
from cli_anything.vscode.core.extension import install_extension, list_extensions
from cli_anything.vscode.core.git import get_status, add, commit


def main():
    """Run a basic workflow."""
    print("=" * 50)
    print("VS Code CLI - Basic Workflow Example")
    print("=" * 50)
    print()

    # 1. Open a workspace
    print("Step 1: Opening workspace...")
    try:
        result = open_in_vscode(".", new_window=True)
        print(f"✓ Opened: {result['path']}")
    except Exception as e:
        print(f"✗ Error: {e}")
        return

    print()

    # 2. Install an extension
    print("Step 2: Installing Python extension...")
    try:
        result = install_extension("ms-python.python")
        if result.get("success"):
            print(f"✓ Installed: {result['extension_id']}")
        else:
            print(f"✗ Failed: {result.get('stderr', 'Unknown error')}")
    except Exception as e:
        print(f"✗ Error: {e}")

    print()

    # 3. List installed extensions
    print("Step 3: Listing installed extensions...")
    try:
        extensions = list_extensions()
        print(f"✓ Found {len(extensions)} extensions")
        for ext in extensions[:5]:  # Show first 5
            print(f"  - {ext['id']}")
    except Exception as e:
        print(f"✗ Error: {e}")

    print()

    # 4. Check Git status
    print("Step 4: Checking Git status...")
    try:
        status = get_status()
        print(f"✓ Current branch: {status.get('branch', 'unknown')}")
        print(f"  Changes: {len(status.get('changes', {}).get('staged', []))} staged, "
              f"{len(status.get('changes', {}).get('unstaged', []))} unstaged")
    except Exception as e:
        print(f"✗ Error: {e}")

    print()
    print("=" * 50)
    print("Workflow complete!")
    print("=" * 50)


if __name__ == "__main__":
    main()
