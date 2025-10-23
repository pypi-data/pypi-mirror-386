"""
Configuration Module

This module contains configuration constants for PyEnvRunner.

Constants:
- DEFAULT_IMPORT_TO_PACKAGE_MAP: Mapping of import names to PyPI package names
- DEFAULT_REQUIREMENTS_FILE: Default name for requirements file

Author: PyEnvRunner Team
License: MIT
"""

# ============================================================================
# IMPORT TO PACKAGE NAME MAPPING
# ============================================================================
# Many Python packages have different import names than their PyPI names.
# This dictionary maps the import name (what you use in code) to the
# PyPI package name (what you install with pip).
#
# Example:
#   import cv2           → pip install opencv-python
#   import sklearn       → pip install scikit-learn
#   from PIL import ...  → pip install Pillow
#
# When PyEnvRunner detects "ModuleNotFoundError: No module named 'cv2'",
# it will look up 'cv2' in this map and install 'opencv-python' instead.
# ============================================================================

DEFAULT_IMPORT_TO_PACKAGE_MAP = {
    "yaml": "PyYAML",                # Import: import yaml
    "cv2": "opencv-python",          # Import: import cv2
    "sklearn": "scikit-learn",       # Import: import sklearn
    "PIL": "Pillow",                 # Import: from PIL import Image
    "dotenv": "python-dotenv",       # Import: from dotenv import load_dotenv
    "dateutil": "python-dateutil",   # Import: import dateutil
}

# ============================================================================
# DEFAULT REQUIREMENTS FILE
# ============================================================================
# Name of the file where installed packages are saved when using --save-reqs
# ============================================================================

DEFAULT_REQUIREMENTS_FILE = "pyenvrunner_requirements.txt"