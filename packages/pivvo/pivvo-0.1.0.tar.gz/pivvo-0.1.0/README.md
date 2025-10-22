# pivvo

[![PyPI version](https://img.shields.io/pypi/v/pivvo.svg)](https://pypi.org/project/pivvo/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/Flaxmbot/pivvo/workflows/CI/badge.svg)](https://github.com/Flaxmbot/pivvo/actions)

<div align="center">
  <pre>
    ____  _                 
   / __ \(_)   ___   ______ 
  / /_/ / / | / / | / / __ \
 / ____/ /| |/ /| |/ / /_/ /
/_/   /_/ |___/ |___/\____/ 
  </pre>
</div>

> A small, pragmatic CLI tool to initialize and manage Python projects with ease. Bootstrap your projects, manage dependencies, and streamline your workflow—all from the command line.

pivvo helps developers quickly set up Python projects with virtual environments, Git repositories, and essential files. It provides a suite of commands to manage dependencies, run scripts, and maintain your project's environment without leaving the terminal.

## Table of Contents

- [✨ Features](#-features)
- [📦 Installation](#-installation)
- [🚀 Quickstart](#-quickstart)
- [📖 Commands](#-commands)
- [🛠️ Development](#️-development)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)
- [👥 Authors](#-authors)

## ✨ Features

- **Project Initialization**: Create new Python projects with virtual environments, Git repos, and basic files in seconds
- **Dependency Management**: Install, list, freeze, upgrade, and remove packages within the project's venv
- **Script Execution**: Run Python scripts directly inside the project's virtual environment
- **Beautiful Output**: Rich terminal interface with progress indicators and colored output
- **Error Handling**: Comprehensive error logging for troubleshooting
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Lightweight**: Minimal dependencies for fast installation and execution

## 📦 Installation

### From PyPI (Recommended)

```bash
pip install pivvo
```

### From Source

```bash
git clone https://github.com/Flaxmbot/pivvo.git
cd pivvo
pip install -e .
```

### Prerequisites

- Python 3.10 or higher
- pip (usually included with Python)

## 🚀 Quickstart

1. **Install pivvo**:
   ```bash
   pip install pivvo
   ```

2. **Initialize a new project**:
   ```bash
   pivvo init my-awesome-project
   cd my-awesome-project
   ```

3. **Install dependencies**:
   ```bash
   pivvo install-deps requests flask python-dotenv
   ```

4. **Run your application**:
   ```bash
   pivvo run app.py
   ```

That's it! Your project is ready with a virtual environment, Git repository, and all dependencies installed.

## 📖 Commands

pivvo provides the following commands:

| Command | Description |
|---------|-------------|
| `pivvo init <name>` | Initialize a new project directory with venv and Git |
| `pivvo install-deps [packages...]` | Install packages into the local venv. Use `-f/--file` to install from requirements file |
| `pivvo run <script.py>` | Execute a Python script inside the venv |
| `pivvo list` | List all packages installed in the venv |
| `pivvo freeze` | Write current venv packages to `requirements.txt` |
| `pivvo upgrade` | Upgrade all packages listed in `requirements.txt` to latest versions |
| `pivvo remove <package>` | Uninstall a package and update `requirements.txt` |

### Getting Help

```bash
# General help
pivvo --help

# Command-specific help
pivvo install-deps --help
pivvo init --help
```

## 🛠️ Development

### Setting Up Development Environment

```bash
git clone https://github.com/Flaxmbot/pivvo.git
cd pivvo
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
pip install -r requirements.txt
```

### Project Structure

```
pivvo/
├── pivvo/
│   ├── __init__.py
│   ├── cli.py          # Main CLI implementation
│   └── main.py         # Package entry point
├── tests/              # Unit tests
├── requirements.txt    # Dependencies
├── pyproject.toml      # Package configuration
├── LICENSE
├── CONTRIBUTING.md
└── README.md
```

### Running Tests

```bash
# Install test dependencies
pip install pytest

# Run tests
pytest

# Run with coverage
pytest --cov=pivvo
```

### Development Notes

- **CLI Implementation**: Located in `pivvo/cli.py` using Typer for argument parsing
- **Terminal Output**: Uses Rich for beautiful, colored terminal output
- **Error Logging**: Failed subprocess commands are logged to `pivvo-error.log`
- **Git Integration**: Uses GitPython for repository initialization
- **Cross-Platform**: Handles different Python executable paths for Windows/macOS/Linux

### Tips for Windows Development

When using Git Bash on Windows, you might see raw ANSI escape codes. Solutions:
- Force ANSI rendering: Modify `cli.py` to use `Console(force_terminal=True, color_system="auto")`
- Use `winpty`: `winpty python pivvo/main.py ...`
- Use PowerShell, CMD, or Windows Terminal instead of Git Bash

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details on:

- Reporting bugs
- Requesting features
- Setting up your development environment
- Submitting pull requests
- Code style guidelines

### Quick Contribution Flow

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Add tests for your changes
4. Ensure all tests pass: `pytest`
5. Commit your changes: `git commit -m "Add amazing feature"`
6. Push to your branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Authors

- **Devrat Kuntal** - *Creator & Maintainer* - [rdxdevbhai76@gmail.com](mailto:rdxdevbhai76@gmail.com)

---

<div align="center">
  <p>Made with ❤️ for the Python community</p>
  <p>
    <a href="#pivvo">Back to top</a> •
    <a href="https://github.com/Flaxmbot/pivvo/issues">Report Bug</a> •
    <a href="https://github.com/Flaxmbot/pivvo/issues">Request Feature</a>
  </p>
</div>
