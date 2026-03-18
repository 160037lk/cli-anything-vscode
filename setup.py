"""Setup configuration for cli-anything-vscode."""

from setuptools import setup, find_namespace_packages

setup(
    name="cli-anything-vscode",
    version="1.0.0",
    description="A stateful CLI for Visual Studio Code",
    long_description="""
        CLI-Anything harness for Visual Studio Code.

        Provides a command-line interface for:
        - Opening files, folders, and workspaces
        - Installing and managing extensions
        - Running tasks
        - Searching files and content
        - Git operations
        - Editor control
    """,
    author="CLI-Anything",
    python_requires=">=3.10",
    packages=find_namespace_packages(include=["cli_anything.*"]),
    install_requires=[
        "click>=8.0.0",
        "prompt-toolkit>=3.0.0",
    ],
    entry_points={
        "console_scripts": [
            "cli-anything-vscode=cli_anything.vscode.vscode_cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
