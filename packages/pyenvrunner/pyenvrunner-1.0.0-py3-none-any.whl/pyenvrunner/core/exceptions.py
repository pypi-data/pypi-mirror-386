"""
Custom Exceptions Module

This module defines a hierarchy of custom exceptions for PyEnvRunner.
All exceptions inherit from PyEnvRunnerError for easy catching.

Exception Hierarchy:
    PyEnvRunnerError (base)
    ├── VenvError
    │   ├── VenvCreationError
    │   └── VenvPathError
    ├── ScriptExecutionError
    └── PackageManagementError
        ├── PackageInstallationError
        └── RequirementsFileError

Author: PyEnvRunner Team
License: MIT
"""


class PyEnvRunnerError(Exception):
    """
    Base exception for all PyEnvRunner errors.

    All custom exceptions in PyEnvRunner inherit from this class,
    allowing users to catch all PyEnvRunner-specific errors with:
        except PyEnvRunnerError as e:
            ...
    """
    pass


class VenvError(PyEnvRunnerError):
    """
    Base exception for virtual environment related errors.

    Raised when there are issues with creating, accessing, or
    managing virtual environments.
    """
    pass


class VenvCreationError(VenvError):
    """
    Error during virtual environment creation.

    Raised when:
    - Python's venv module fails to create environment
    - System Python executable is not found
    - Unable to delete existing environment for force_recreate
    """
    pass


class VenvPathError(VenvError):
    """
    Error related to paths within a virtual environment.

    Raised when:
    - Expected executables (python, pip) are not found in venv
    - Virtual environment structure is corrupted or incomplete
    - Current Python executable cannot be found (when using --use-current-env)
    """
    pass


class ScriptExecutionError(PyEnvRunnerError):
    """
    Error during target script execution.

    Raised when:
    - Script exits with non-zero code (and it's not a ModuleNotFoundError)
    - Script fails to start
    - Script contains runtime errors (ZeroDivisionError, ValueError, etc.)
    """
    pass


class PackageManagementError(PyEnvRunnerError):
    """
    Base exception for package management errors.

    Covers all errors related to pip operations and requirements files.
    """
    pass


class PackageInstallationError(PackageManagementError):
    """
    Error during package installation via pip.

    Raised when:
    - pip install command fails (package doesn't exist on PyPI)
    - Network errors prevent package download
    - pip executable is not found or not working
    - Package has incompatible dependencies
    """
    pass


class RequirementsFileError(PackageManagementError):
    """
    Error related to requirements file operations.

    Raised when:
    - Cannot read or write to requirements file
    - Requirements file has invalid format
    - Permission issues with requirements file
    """
    pass