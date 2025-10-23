"""
PyEnvRunner CLI Entry Point

This module provides the command-line interface for PyEnvRunner,
a tool that automatically manages Python virtual environments and dependencies.

Main Features:
- Automatic virtual environment creation and management
- Runtime detection and installation of missing packages
- Support for import name to PyPI package name mapping
- Real-time output streaming for long-running scripts
- Flexible CLI flags for various use cases

Author: PyEnvRunner Team
License: MIT
"""

import os
import sys
import argparse

from pyenvrunner.core.venv_management import create_or_get_venv_paths
from pyenvrunner.core.package_management import install_missing_packages, clear_environment_packages
from pyenvrunner.core.config import DEFAULT_IMPORT_TO_PACKAGE_MAP, DEFAULT_REQUIREMENTS_FILE
from pyenvrunner.core.exceptions import PyEnvRunnerError


def main() -> None:
    """
    Main entry point for the PyEnvRunner CLI.

    This function:
    1. Parses command-line arguments (separating tool args from script args)
    2. Handles utility commands (--list-import-mappings, --clear-env)
    3. Creates or manages virtual environments
    4. Executes the target script with automatic dependency installation

    Exit Codes:
        0: Success
        1: Error occurred (script error, package installation failure, etc.)

    Raises:
        PyEnvRunnerError: For known errors in PyEnvRunner operations
        Exception: For unexpected errors during execution
    """
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        prog="pyenvrunner",
        description=(
            "PyEnvRunner - Automatically manage Python virtual environments and dependencies.\n\n"
            "Runs Python scripts with automatic dependency detection and installation. When your\n"
            "script imports missing packages, PyEnvRunner automatically installs them in an\n"
            "isolated virtual environment. Perfect for quick prototyping and sharing scripts."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run a script with automatic dependency management
  pyenvrunner my_script.py

  # Run a script and save installed packages to requirements file
  pyenvrunner --save-reqs my_script.py

  # Pass arguments to the script (everything after script path goes to your script)
  pyenvrunner my_script.py --arg1 value1 --arg2 value2

  # Use a custom virtual environment name
  pyenvrunner --env-name my_env my_script.py

  # Force recreate the virtual environment (useful for fresh start)
  pyenvrunner --force-recreate-env my_script.py

  # Use current Python environment instead of creating a venv
  pyenvrunner --use-current-env my_script.py

  # Save requirements to a custom file
  pyenvrunner --save-reqs --reqs-file deps.txt my_script.py

  # List all import-to-package mappings (e.g., cv2 → opencv-python)
  pyenvrunner --list-import-mappings

  # Clear all installed packages from the virtual environment
  pyenvrunner --clear-env --env-name my_env

For more information, visit: https://github.com/yourusername/pyenvrunner
"""
    )

    # Script execution arguments
    script_group = parser.add_argument_group('Script Execution')
    script_group.add_argument(
        "script_path",
        nargs="?",
        default="main.py",
        help="Path to the Python script to execute. Default: main.py"
    )

    # Virtual environment options
    venv_group = parser.add_argument_group('Virtual Environment Options')
    venv_group.add_argument(
        "--env-name",
        default="env",
        metavar="NAME",
        help="Name of the virtual environment directory to create or use. Default: env"
    )
    venv_group.add_argument(
        "--use-current-env",
        action="store_true",
        help="Use the currently active Python environment instead of creating/using a virtual environment. "
             "Useful when running in containers or pre-configured environments."
    )
    venv_group.add_argument(
        "--force-recreate-env",
        action="store_true",
        help="Delete and recreate the virtual environment if it already exists. "
             "Use this for a fresh start or when dependencies are corrupted. Ignored with --use-current-env."
    )

    # Package management options
    pkg_group = parser.add_argument_group('Package Management Options')
    pkg_group.add_argument(
        "--save-reqs",
        action="store_true",
        help="Save newly installed packages to the requirements file. "
             "Useful for tracking dependencies as you develop."
    )
    pkg_group.add_argument(
        "--reqs-file",
        default=DEFAULT_REQUIREMENTS_FILE,
        metavar="FILE",
        help=f"Name or path of the requirements file. Default: {DEFAULT_REQUIREMENTS_FILE}"
    )

    # Utility commands
    util_group = parser.add_argument_group('Utility Commands')
    util_group.add_argument(
        "--list-import-mappings",
        action="store_true",
        help="Display the predefined import-to-package mappings and exit. "
             "Shows how import names map to PyPI package names (e.g., cv2 → opencv-python)."
    )
    util_group.add_argument(
        "--clear-env",
        action="store_true",
        help="Remove all installed non-editable packages from the target environment and exit. "
             "Useful for cleaning up before rebuilding from requirements.txt."
    )

    # ============================================================================
    # ARGUMENT PARSING LOGIC
    # ============================================================================
    # Separate pyenvrunner arguments from script arguments.
    # This is necessary because we want to support:
    #   pyenvrunner --save-reqs my_script.py --script-arg value
    # Where:
    #   - --save-reqs belongs to pyenvrunner
    #   - my_script.py is the script path
    #   - --script-arg value should be passed to my_script.py
    #
    # Algorithm:
    # 1. Iterate through all CLI arguments
    # 2. Flags before the script path → pyenvrunner args
    # 3. First non-flag argument → script path (goes to pyenvrunner args)
    # 4. Everything after script path → script args
    # ============================================================================

    pyenvrunner_args: list[str] = []  # Arguments for pyenvrunner itself
    script_args: list[str] = []       # Arguments to pass to the target script
    script_path_found: bool = False   # Flag to track when we've found the script path
    skip_next: bool = False           # Flag to skip next arg (it's a value for a flag)

    argv_list: list[str] = sys.argv[1:]  # All CLI arguments except program name

    for i, arg in enumerate(argv_list):
        if skip_next:
            # This was a value for a previous flag, already added
            skip_next = False
            continue

        if script_path_found:
            # Everything after script path goes to the script
            script_args.append(arg)
        elif not arg.startswith('-'):
            # First non-flag argument is the script path
            script_path_found = True
            pyenvrunner_args.append(arg)
        else:
            # This is a pyenvrunner flag
            pyenvrunner_args.append(arg)
            # Check if this flag takes a value (not all flags do)
            if arg in ['--reqs-file', '--env-name']:
                if i + 1 < len(argv_list) and not argv_list[i + 1].startswith('-'):
                    # Next argument is the value for this flag
                    pyenvrunner_args.append(argv_list[i + 1])
                    skip_next = True  # Skip this value in next iteration

    # Parse only pyenvrunner's arguments
    args: argparse.Namespace = parser.parse_args(pyenvrunner_args)

    # ============================================================================
    # UTILITY COMMAND: List Import Mappings
    # ============================================================================
    # If user requested to see import-to-package mappings, display them and exit
    if args.list_import_mappings:
        print("--- Import to Package Mappings ---")
        for imp, pkg in DEFAULT_IMPORT_TO_PACKAGE_MAP.items():
            print(f"  {imp} -> {pkg}")
        print("----------------------------------")
        sys.exit(0)

    try:
        # ========================================================================
        # UTILITY COMMAND: Clear Environment Packages
        # ========================================================================
        # If user requested to clear packages, do so and exit
        if args.clear_env:
            pip_to_use_for_clear: list[str] = []
            env_description: str = ""
            if args.use_current_env:
                env_description = "current Python environment"
                print(f"Preparing to clear packages from the {env_description}.")
                pip_to_use_for_clear = [sys.executable, "-m", "pip"]
            else:
                env_dir_to_clear: str = args.env_name
                env_description = f"virtual environment: '{env_dir_to_clear}'"
                print(f"Preparing to clear packages from {env_description}.")
                if not os.path.isdir(env_dir_to_clear):
                    print(f"Virtual environment directory '{env_dir_to_clear}' does not exist. Nothing to clear.")
                    sys.exit(0)

                pip_exe_path: str
                if os.name == "nt":
                    pip_exe_path = os.path.join(env_dir_to_clear, "Scripts", "pip.exe")
                else:
                    pip_exe_path = os.path.join(env_dir_to_clear, "bin", "pip")

                if not os.path.exists(pip_exe_path):
                    print(f"Pip executable not found at '{pip_exe_path}' in venv '{env_dir_to_clear}'. Cannot clear.")
                    sys.exit(1)

                pip_to_use_for_clear = [pip_exe_path]

            print(f"Target for clearing: {env_description}")
            clear_environment_packages(pip_to_use_for_clear)
            sys.exit(0)

        # ========================================================================
        # MAIN EXECUTION FLOW: Run Script with Dependency Management
        # ========================================================================

        # Validate that the target script exists
        target_script_path: str = args.script_path
        if not os.path.exists(target_script_path):
            print(f"Error: Target script '{target_script_path}' not found.")
            sys.exit(1)

        # Create or get virtual environment paths
        # Returns: (activate_script_path, python_executable_path, pip_command_list)
        activate_script_path: str | None
        venv_python_path: str | None
        venv_pip_command_list: list[str]

        activate_script_path, venv_python_path, venv_pip_command_list = create_or_get_venv_paths(
            env_name=args.env_name,
            force_recreate=args.force_recreate_env,
            use_current_env=args.use_current_env
        )

        # Display activation instructions to the user
        if not args.use_current_env and activate_script_path:
            print(f"\nVirtual environment is ready in './{args.env_name}'.")
            print(f"To activate it manually in your shell:")
            try:
                rel_activate_path: str = os.path.relpath(activate_script_path, os.getcwd())
            except ValueError:
                rel_activate_path = activate_script_path

            if os.name == 'nt':
                print(f"  {rel_activate_path}")
            else:
                print(f"  source {rel_activate_path}")
            print("-" * 30)
        elif args.use_current_env:
            print("\nRunning in current Python environment. No venv activation needed by this script.")
            print("-" * 30)

        # Execute the script with automatic dependency management
        # This function will:
        # 1. Run the script
        # 2. Detect ModuleNotFoundError in stderr
        # 3. Automatically install missing packages
        # 4. Retry the script until it succeeds or encounters a non-module error
        install_missing_packages(
            script_path=target_script_path,
            import_to_package_map=DEFAULT_IMPORT_TO_PACKAGE_MAP,
            venv_python_executable=venv_python_path,
            venv_pip_command_list=venv_pip_command_list,
            save_requirements_flag=args.save_reqs,
            requirements_file_name=args.reqs_file,
            script_args=script_args
        )

    except PyEnvRunnerError as e:
        # Handle known PyEnvRunner errors
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        # Handle unexpected errors
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)

    print("\nWrapper script finished.")


if __name__ == "__main__":
    main()