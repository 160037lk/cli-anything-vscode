"""Extension management for VS Code CLI.

Handles installing, uninstalling, and listing VS Code extensions.
"""

import subprocess
import json
from typing import Dict, Any, List, Optional
from ..utils.vscode_backend import find_vscode


def install_extension(
    extension_id: str,
    version: Optional[str] = None,
    pre_release: bool = False,
) -> Dict[str, Any]:
    """Install a VS Code extension.

    Args:
        extension_id: Extension ID (e.g., 'ms-python.python')
        version: Specific version to install
        pre_release: Install pre-release version

    Returns:
        Result dictionary with operation details
    """
    vscode = find_vscode()

    cmd = [vscode, "--install-extension", extension_id]

    if version:
        cmd.extend(["--extension-version", version])
    if pre_release:
        cmd.append("--pre-release")

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
    )

    return {
        "extension_id": extension_id,
        "version": version,
        "pre_release": pre_release,
        "command": " ".join(cmd),
        "returncode": result.returncode,
        "stdout": result.stdout if result.stdout else None,
        "stderr": result.stderr if result.stderr else None,
        "success": result.returncode == 0 or "already installed" in result.stdout.lower(),
    }


def uninstall_extension(extension_id: str) -> Dict[str, Any]:
    """Uninstall a VS Code extension.

    Args:
        extension_id: Extension ID to uninstall

    Returns:
        Result dictionary with operation details
    """
    vscode = find_vscode()

    cmd = [vscode, "--uninstall-extension", extension_id]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
    )

    return {
        "extension_id": extension_id,
        "command": " ".join(cmd),
        "returncode": result.returncode,
        "stdout": result.stdout if result.stdout else None,
        "stderr": result.stderr if result.stderr else None,
        "success": result.returncode == 0,
    }


def list_extensions(
    installed: bool = True,
    enabled: bool = False,
    disabled: bool = False,
) -> List[Dict[str, Any]]:
    """List VS Code extensions.

    Args:
        installed: Show installed extensions
        enabled: Show only enabled extensions
        disabled: Show disabled extensions

    Returns:
        List of extension dictionaries
    """
    vscode = find_vscode()

    cmd = [vscode, "--list-extensions"]

    if enabled:
        cmd.append("--show-versions")

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
    )

    extensions = []
    if result.returncode == 0:
        lines = result.stdout.strip().split("\n")
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Parse extension ID and version
            if "@" in line:
                ext_id, version = line.rsplit("@", 1)
            else:
                ext_id = line
                version = None

            extensions.append({
                "id": ext_id,
                "version": version,
            })

    return extensions


def search_extensions(
    query: str,
    category: Optional[str] = None,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """Search for extensions in the VS Code marketplace.

    Note: VS Code CLI doesn't have a built-in search command.
    This uses the marketplace API directly.

    Args:
        query: Search query
        category: Filter by category
        limit: Maximum number of results

    Returns:
        List of extension dictionaries
    """
    import urllib.request
    import urllib.parse

    # VS Code marketplace API
    api_url = "https://marketplace.visualstudio.com/_apis/public/gallery/extensionquery"

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json;api-version=3.0-preview.1",
    }

    payload = {
        "filters": [
            {
                "criteria": [
                    {"filterType": 8, "value": "Microsoft.VisualStudio.Code"},
                    {"filterType": 10, "value": query},
                ],
                "pageNumber": 1,
                "pageSize": limit,
                "sortBy": 0,
                "sortOrder": 0,
            }
        ],
        "assetTypes": [],
        "flags": 0x1 | 0x2 | 0x80,  # Include versions, files, and statistics
    }

    if category:
        payload["filters"][0]["criteria"].append(
            {"filterType": 5, "value": category}
        )

    try:
        req = urllib.request.Request(
            api_url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))

        results = []
        for result in data.get("results", []):
            for extension in result.get("extensions", []):
                results.append({
                    "id": extension.get("extensionName", ""),
                    "publisher": extension.get("publisher", {}).get("publisherName", ""),
                    "full_id": f"{extension.get('publisher', {}).get('publisherName', '')}.{extension.get('extensionName', '')}",
                    "name": extension.get("displayName", ""),
                    "description": extension.get("shortDescription", ""),
                    "version": extension.get("versions", [{}])[0].get("version", ""),
                    "downloads": extension.get("statistics", [{}])[0].get("value", 0),
                    "rating": extension.get("statistics", [{}])[1].get("value", 0) if len(extension.get("statistics", [])) > 1 else 0,
                })

        return results

    except Exception as e:
        return [{"error": str(e), "message": "Failed to search marketplace"}]


def get_extension_info(extension_id: str) -> Dict[str, Any]:
    """Get detailed information about an extension.

    Args:
        extension_id: Extension ID

    Returns:
        Extension information dictionary
    """
    import urllib.request

    # Split publisher and extension name
    if "." not in extension_id:
        raise ValueError(f"Invalid extension ID format: {extension_id}. Expected 'publisher.name'.")

    publisher, name = extension_id.split(".", 1)

    api_url = f"https://marketplace.visualstudio.com/_apis/public/gallery/publishers/{publisher}/extensions/{name}"

    headers = {
        "Accept": "application/json;api-version=3.0-preview.1",
    }

    try:
        req = urllib.request.Request(api_url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))

        return {
            "id": extension_id,
            "name": data.get("displayName", ""),
            "description": data.get("shortDescription", ""),
            "long_description": data.get("description", ""),
            "publisher": data.get("publisher", {}).get("displayName", ""),
            "version": data.get("versions", [{}])[0].get("version", ""),
            "categories": data.get("categories", []),
            "tags": data.get("tags", []),
            "license": data.get("versions", [{}])[0].get("properties", [{}])[0].get("value", "") if data.get("versions") else None,
            "repository": data.get("versions", [{}])[0].get("properties", [{}])[1].get("value", "") if len(data.get("versions", [{}])[0].get("properties", [])) > 1 else None,
            "homepage": data.get("versions", [{}])[0].get("properties", [{}])[2].get("value", "") if len(data.get("versions", [{}])[0].get("properties", [])) > 2 else None,
            "downloads": data.get("statistics", [{}])[0].get("value", 0),
            "rating": data.get("statistics", [{}])[1].get("value", 0) if len(data.get("statistics", [])) > 1 else 0,
            "installs": data.get("statistics", [{}])[2].get("value", 0) if len(data.get("statistics", [])) > 2 else 0,
        }

    except Exception as e:
        return {
            "error": str(e),
            "message": f"Failed to get info for {extension_id}",
        }

