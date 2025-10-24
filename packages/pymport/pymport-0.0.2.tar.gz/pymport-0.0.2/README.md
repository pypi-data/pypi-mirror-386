# pymport

[![PyPI](https://img.shields.io/pypi/v/pymport.svg)](https://pypi.python.org/pypi/pymport)
[![CI](https://github.com/rmoralespp/pymport/workflows/CI/badge.svg)](https://github.com/rmoralespp/pymport/actions?query=event%3Arelease+workflow%3ACI)
[![versions](https://img.shields.io/pypi/pyversions/pymport.svg)](https://github.com/rmoralespp/pymport)
[![codecov](https://codecov.io/gh/rmoralespp/pymport/branch/main/graph/badge.svg)](https://app.codecov.io/gh/rmoralespp/pymport)
[![license](https://img.shields.io/github/license/rmoralespp/pymport.svg)](https://github.com/rmoralespp/pymport/blob/main/LICENSE)
[![Linter: ruff](https://img.shields.io/badge/linter-_ruff-orange)](https://github.com/charliermarsh/ruff)

## About

A lightweight Python linter for checking unused imports

### Features

* 🧹 Detects unused or shadowed `imports` that linters like **ruff** may miss
* 🚫 Use `noqa` comments to ignore imports you want to keep
* ⚙️ Minimalist CLI interface for easy integration in **CI/CD** pipelines
* 🐍 No external dependencies beyond the Python standard library
* ✅ **100%** test coverage with automated tests

> [!IMPORTANT]
> **False positives**
>
> This tool is not possible to assure a 100% false positive free result due to the
> possible collateral execution effects when importing a module.
> This is, importing a module can affect or enable some feature needed somewhere
> else, so not using anything from that imported package/module does not necessarily mean is not needed.

A minimal typical example could be:

```python
import os.path

print(os.curdir)
```

## Installation

To install **pymport** using `pip`, run the following command:

```bash
pip install pymport --upgrade
```

## Quick Start

To run the linter on the current directory, use the following command:

```bash
pymport .
```

* This will check all Python files in the current directory and its subdirectories.

### Command-Line Interface

`pymport [FILE] [--help]`

| Argument / Option | Description                                                             |
|-------------------|-------------------------------------------------------------------------|
| `[FILE]`          | Files or directories to lint. (Need at least one file or dir to check.) |
| `--help`          | Show help message and exit.                                             |

> [!TIP]
> **Ignoring Unused Imports**
>
> Use a comment like `# noqa: unused-import` to ignore the line.

### Output

When unused imports are detected, they will be reported in the following format:

```text
path/to/file.py:LINE-NUMBER: UNUSED-IMPORT-NAME
```

> [!NOTE]
>
> * Exit code `0` means no unused imports were found; exit code `1` indicates that unused imports were detected.
> * When no unused imports are found, success message is printed.

## Development

To contribute to the project, you can run the following commands for testing and documentation:

First, ensure you have the latest version of `pip`:

```bash
python -m pip install --upgrade pip
```

### Running Tests

```bash
pip install --group=test --upgrade # Install test dependencies, skip if already installed
python -m pytest tests/ # Run all tests
python -m pytest tests/ --cov # Run tests with coverage
```

### Running Linter

```bash
pip install --group=lint --upgrade  # Install lint dependencies, skip if already installed
ruff check . # Run linter
```

## License

This project is licensed under the [MIT license](LICENSE).
