"""
PyEnvRunner Setup Configuration

This setup.py file configures the package for distribution on PyPI.
It defines package metadata, dependencies, and entry points.

To install in development mode:
    pip install -e .

To build and upload to PyPI:
    python setup.py sdist bdist_wheel
    twine upload dist/*

Author: Aditya Thiyyagura
License: MIT
"""

from setuptools import setup, find_packages

setup(
    # ============================================================================
    # PACKAGE METADATA
    # ============================================================================
    name="pyenvrunner",
    version="1.0.0",
    description="Wrapper to manage Python venvs & run scripts, installing missing dependencies",
    long_description=open("README.md").read() if __name__ == "__main__" else "",
    long_description_content_type="text/markdown",
    author="Aditya Thiyyagura",
    author_email="thiyyaguraadityareddy@gmail.com",
    url="https://github.com/yourusername/pyenvrunner",
    license="MIT",

    # ============================================================================
    # PACKAGE DISCOVERY
    # ============================================================================
    # Automatically find all packages in the project
    # This will find: pyenvrunner, pyenvrunner.cli, pyenvrunner.core
    packages=find_packages(),

    # ============================================================================
    # COMMAND-LINE INTERFACE
    # ============================================================================
    # Create a 'pyenvrunner' command that users can run from terminal
    # Maps to: pyenvrunner.cli.main:main() function
    entry_points={
        "console_scripts": [
            "pyenvrunner=pyenvrunner.cli.main:main",
        ],
    },

    # ============================================================================
    # DEPENDENCIES
    # ============================================================================
    # Minimum Python version required
    python_requires=">=3.6",

    # Runtime dependencies (PyEnvRunner has no external dependencies!)
    # It uses only Python standard library modules
    install_requires=[
        # No external dependencies - uses only Python stdlib
    ],

    # ============================================================================
    # PACKAGE CLASSIFIERS
    # ============================================================================
    # These help users find your package on PyPI
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Installation/Setup",
    ],

    # ============================================================================
    # ADDITIONAL METADATA
    # ============================================================================
    keywords="venv virtualenv dependency-management pip automation",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/pyenvrunner/issues",
        "Source": "https://github.com/yourusername/pyenvrunner",
    },
)