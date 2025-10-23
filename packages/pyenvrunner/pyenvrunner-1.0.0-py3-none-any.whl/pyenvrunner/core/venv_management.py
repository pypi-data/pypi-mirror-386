"""
Virtual Environment Management Module

This module handles the creation and management of Python virtual environments.

Key Features:
- Create new virtual environments using Python's venv module
- Reuse existing virtual environments
- Force recreate option to start fresh
- Option to use current Python environment instead of creating venv
- Cross-platform support (Windows, Linux, macOS)

Author: PyEnvRunner Team
License: MIT
"""

import os
import sys
import shutil
import subprocess
from typing import Tuple, Optional, List
from .exceptions import VenvCreationError, VenvPathError

def create_or_get_venv_paths(
    env_name: str = "env",
    force_recreate: bool = False,
    use_current_env: bool = False
) -> Tuple[Optional[str], str, List[str]]:
    """
    Create or get paths for a Python virtual environment.

    This function either creates a new virtual environment or returns paths
    to an existing one. It handles platform-specific path differences and
    provides options for using the current environment.

    Args:
        env_name: Name/path of the virtual environment directory. Default: "env"
        force_recreate: If True, delete and recreate the venv if it exists
        use_current_env: If True, use the current Python environment instead of venv

    Returns:
        Tuple of (activate_script_path, python_executable_path, pip_command_list):
        - activate_script_path: Path to activation script (None if use_current_env=True)
        - python_executable_path: Path to Python executable
        - pip_command_list: Command list to invoke pip

    Raises:
        VenvCreationError: If virtual environment creation fails
        VenvPathError: If expected executables are not found
        FileNotFoundError: If system Python executable not found

    Platform Notes:
        - Windows: Scripts in env/Scripts/, executables end with .exe
        - Unix/Mac: Scripts in env/bin/, no .exe extension

    Example:
        activate, python, pip = create_or_get_venv_paths("my_env", force_recreate=True)
        # Returns: ("my_env/bin/activate", "my_env/bin/python", ["my_env/bin/pip"])
    """
    # Option 1: Use current Python environment (no venv creation)
    if use_current_env:
        python_executable: str = sys.executable
        pip_command_list: List[str] = [sys.executable, "-m", "pip"]

        # Validate that current Python executable exists
        if not os.path.exists(python_executable):
            raise VenvPathError(f"Current Python executable not found at {python_executable}")

        # Return None for activate_script since we're not using a venv
        return None, python_executable, pip_command_list

    # Option 2: Create or reuse a virtual environment
    env_path: str = env_name

    # If force_recreate is True, delete existing venv to start fresh
    if force_recreate and os.path.exists(env_path) and os.path.isdir(env_path):
        try:
            shutil.rmtree(env_path)  # Recursively delete the directory
        except OSError as e:
            raise VenvCreationError(f"Error deleting existing virtual environment '{env_path}': {e}")

    # Create new virtual environment if it doesn't exist
    if not os.path.exists(env_path):
        try:
            # Use Python's built-in venv module to create the environment
            subprocess.run([sys.executable, "-m", "venv", env_path], check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            stderr_msg: str = f"\nStderr: {e.stderr.strip()}" if e.stderr else ""
            raise VenvCreationError(f"Error creating virtual environment: {e}{stderr_msg}")
        except FileNotFoundError:
            raise VenvCreationError(f"Error: '{sys.executable}' not found. Cannot create virtual environment.")

    # Determine platform-specific paths for virtual environment executables
    # Windows uses "Scripts" directory with .exe extensions
    # Unix/Mac uses "bin" directory without extensions
    if os.name == "nt":  # Windows
        activate_script: str = os.path.join(env_path, "Scripts", "activate")
        python_executable: str = os.path.join(env_path, "Scripts", "python.exe")
        pip_executable: str = os.path.join(env_path, "Scripts", "pip.exe")
    else:  # Unix, Linux, macOS
        activate_script = os.path.join(env_path, "bin", "activate")
        python_executable = os.path.join(env_path, "bin", "python")
        pip_executable = os.path.join(env_path, "bin", "pip")

    # Validate that required executables exist in the virtual environment
    if not os.path.exists(python_executable):
        raise VenvPathError(f"Python executable not found at {python_executable} in venv '{env_path}'")
    if not os.path.exists(pip_executable):
        raise VenvPathError(f"pip executable not found at {pip_executable} in venv '{env_path}'")

    # Return tuple of (activate_script, python_executable, pip_command_list)
    return activate_script, python_executable, [pip_executable]