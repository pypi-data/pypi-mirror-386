# PyEnvRunner

**Automatically manage Python virtual environments and dependencies.**

PyEnvRunner is a command-line tool that runs Python scripts with automatic dependency detection and installation. When your script imports missing packages, PyEnvRunner automatically installs them in an isolated virtual environment. Perfect for quick prototyping, sharing scripts, and avoiding "works on my machine" issues.

[![PyPI version](https://badge.fury.io/py/pyenvrunner.svg)](https://badge.fury.io/py/pyenvrunner)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.6+](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)

## ✨ Features

- **🚀 Automatic Dependency Installation** - Detects missing imports at runtime and installs them automatically
- **🔒 Isolated Environments** - Creates virtual environments to keep your system Python clean
- **💨 Real-time Output Streaming** - See script output immediately, perfect for long-running services and APIs
- **📦 Import Name Mapping** - Handles cases where import names differ from PyPI names (e.g., `import cv2` → `pip install opencv-python`)
- **📝 Requirements Tracking** - Optionally save installed packages to a requirements file with version pinning
- **🎯 Zero External Dependencies** - Uses only Python standard library
- **🔧 Flexible CLI** - Supports various workflows with intuitive command-line flags

## 🎯 Use Cases

- **Quick Prototyping** - Run scripts without worrying about dependencies
- **Sharing Scripts** - Share a single `.py` file that anyone can run
- **CI/CD Pipelines** - Automatically install dependencies in clean environments
- **API Development** - Real-time output streaming for server logs
- **Education** - Students can run examples without manual setup
- **Testing** - Quickly test scripts in isolated environments

## 📦 Installation

```bash
pip install pyenvrunner
```

Or install from source:

```bash
git clone https://github.com/yourusername/pyenvrunner.git
cd pyenvrunner
pip install -e .
```

## 🚀 Quick Start

### Basic Usage

```bash
# Run a script - automatically installs missing packages
pyenvrunner my_script.py

# Run a script with arguments
pyenvrunner my_script.py --arg1 value1 --arg2 value2

# Save installed packages to requirements file
pyenvrunner --save-reqs my_script.py
```

### Example Script

Create a file `demo.py`:

```python
# No need to install requests first!
import requests

response = requests.get('https://api.github.com')
print(f"Status: {response.status_code}")
```

Run it:

```bash
$ pyenvrunner demo.py

Virtual environment is ready in './env'.
To activate it manually in your shell:
  source env/bin/activate
------------------------------

--- Running script: demo.py using env/bin/python ---
Traceback (most recent call last):
  File "demo.py", line 1, in <module>
    import requests
ModuleNotFoundError: No module named 'requests'

>>> Detected missing module: 'requests'. Attempting to install 'requests'...
--- pip install STDOUT for requests ---
Collecting requests
  Using cached requests-2.32.5-py3-none-any.whl (64 kB)
...
Successfully installed requests-2.32.5
>>> Installation of requests successful. Retrying script...

--- Running script: demo.py using env/bin/python ---
Status: 200

--- Script demo.py completed successfully ---
```

## 📖 CLI Documentation

### Command Syntax

```bash
pyenvrunner [OPTIONS] <script_path> [SCRIPT_ARGS...]
```

### Options

#### Script Execution
- **`script_path`** - Path to the Python script to execute (default: `main.py`)

#### Virtual Environment Options
- **`--env-name NAME`** - Name of the virtual environment directory (default: `env`)
- **`--use-current-env`** - Use the current Python environment instead of creating a venv
- **`--force-recreate-env`** - Delete and recreate the venv if it already exists

#### Package Management Options
- **`--save-reqs`** - Save newly installed packages to requirements file
- **`--reqs-file FILE`** - Specify custom requirements file name (default: `pyenvrunner_requirements.txt`)

#### Utility Commands
- **`--list-import-mappings`** - Display predefined import-to-package mappings and exit
- **`--clear-env`** - Remove all installed packages from the environment and exit
- **`-h, --help`** - Show help message and exit

### Usage Examples

```bash
# Basic execution with automatic venv creation
pyenvrunner my_script.py

# Save dependencies to requirements file
pyenvrunner --save-reqs my_script.py

# Use custom virtual environment name
pyenvrunner --env-name my_custom_env my_script.py

# Force recreate environment (fresh start)
pyenvrunner --force-recreate-env my_script.py

# Use current Python environment (no venv)
pyenvrunner --use-current-env my_script.py

# Save to custom requirements file
pyenvrunner --save-reqs --reqs-file deps.txt my_script.py

# Pass arguments to your script
pyenvrunner my_script.py --input data.csv --output results.json

# List import name mappings
pyenvrunner --list-import-mappings

# Clear all packages from environment
pyenvrunner --clear-env --env-name my_env
```

## 🗺️ Import Name Mapping

Some Python packages have different import names than their PyPI package names. PyEnvRunner handles these automatically:

| Import Statement | PyPI Package |
|-----------------|-------------|
| `import cv2` | `opencv-python` |
| `import sklearn` | `scikit-learn` |
| `from PIL import Image` | `Pillow` |
| `import yaml` | `PyYAML` |
| `from dotenv import load_dotenv` | `python-dotenv` |
| `import dateutil` | `python-dateutil` |

View all mappings:
```bash
pyenvrunner --list-import-mappings
```

## 🔧 How It Works

1. **Create/Reuse Virtual Environment** - PyEnvRunner creates a venv in the current directory (or uses an existing one)
2. **Run Your Script** - Executes your script using the venv's Python interpreter
3. **Detect Missing Imports** - Monitors stderr for `ModuleNotFoundError` messages
4. **Install Packages** - Automatically runs `pip install <package>` for missing modules
5. **Retry Execution** - Reruns the script after installing packages
6. **Real-time Output** - Streams stdout/stderr in real-time using multi-threading
7. **Success** - Script completes with all dependencies installed

## 📁 Project Structure

```
pyenvrunner/
├── pyenvrunner/
│   ├── __init__.py
│   ├── cli/
│   │   └── main.py              # CLI entry point and argument parsing
│   └── core/
│       ├── config.py            # Configuration (import mappings, defaults)
│       ├── exceptions.py        # Custom exception classes
│       ├── package_management.py # Package installation and script execution
│       └── venv_management.py   # Virtual environment creation
├── tests/
│   ├── test_cases/              # 20 comprehensive test cases
│   ├── run_tests.py             # Test runner with reporting
│   └── clear.sh                 # Cleanup script
├── setup.py                     # Package configuration
├── .gitignore                   # Git ignore rules
└── README.md                    # This file
```

## 🧪 Testing

PyEnvRunner includes a comprehensive test suite with 20 test cases covering all features:

```bash
cd tests
python3 run_tests.py
```

Test categories:
- **Core Functionality** - Basic execution, argument handling, auto-install
- **CLI Flags** - All command-line options
- **Error Handling** - Script errors, invalid imports, exit codes
- **Edge Cases** - No output, special characters, warnings

Clean up test artifacts:
```bash
cd tests
./clear.sh
```

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Make your changes**
4. **Add tests** for your changes
5. **Run the test suite** (`cd tests && python3 run_tests.py`)
6. **Commit your changes** (`git commit -m 'Add amazing feature'`)
7. **Push to the branch** (`git push origin feature/amazing-feature`)
8. **Open a Pull Request**

### Development Setup

```bash
git clone https://github.com/yourusername/pyenvrunner.git
cd pyenvrunner
pip install -e .
```

## 📋 Requirements

- Python 3.6 or higher
- No external dependencies (uses only Python standard library)

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by tools like `pipx`, `uvx`, and npm's automatic package installation
- Built with ❤️ for the Python community

## 🐛 Known Limitations

- **Import Detection** - Only detects `ModuleNotFoundError` at runtime. Imports inside try-except blocks won't be detected.
- **Dynamic Imports** - Doesn't detect imports using `importlib` or `__import__()`.
- **Sequential Installation** - Installs packages one at a time, not in parallel.

## 📞 Support

- **Issues** - [GitHub Issues](https://github.com/yourusername/pyenvrunner/issues)
- **Email** - thiyyaguraadityareddy@gmail.com

## 🗺️ Roadmap

- [ ] Add static analysis to detect imports before runtime
- [ ] Support for conda environments
- [ ] Parallel package installation
- [ ] Configuration file support (.pyenvrunner.toml)
- [ ] Integration with poetry/pipenv
- [ ] Docker container support

---

**Made with ❤️ by Aditya Thiyyagura**
