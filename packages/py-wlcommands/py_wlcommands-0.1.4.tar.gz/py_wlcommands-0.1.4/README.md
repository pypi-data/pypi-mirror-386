# py_wlcommands

[![CI](https://github.com/wl-commands/py_wlcommands/actions/workflows/ci.yml/badge.svg)](https://github.com/wl-commands/py_wlcommands/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/py-wlcommands.svg)](https://badge.fury.io/py/py-wlcommands)
[![Python Versions](https://img.shields.io/pypi/pyversions/py-wlcommands.svg)](https://pypi.org/project/py-wlcommands/)

`py_wlcommands` is a command-line toolset based on Python that provides automated command support for project development, covering common development tasks such as environment initialization, building, testing, formatting, cleaning, and code checking. The project combines Python and Rust technology stacks, demonstrating attention to performance and scalability.

## Features

- **init**: Initialize project environment with Git, virtual environment, i18n, Rust submodule, etc.
- **build**: Execute build tasks, support Python package building and distribution
- **test**: Run project tests
- **format**: Support Python and Rust code formatting (integrated with black, rustfmt, etc.)
- **lint**: Execute code quality checks
- **clean**: Clean build artifacts and temporary files
- **self**: Self-management commands

## Installation

### From PyPI

```bash
pip install py-wlcommands
```

### From Source

```bash
# Clone the repository
git clone https://github.com/wl-commands/py_wlcommands.git
cd py_wlcommands

# Install in development mode
pip install -e .
```

## Usage

After installation, you can use the `wl` command:

```bash
# Show help
wl --help

# Initialize a new project
wl init

# Build the project
wl build

# Run tests
wl test

# Format code
wl format

# Lint code
wl lint

# Clean build artifacts
wl clean

# Update the tool itself
wl self update
```

## Development

### Prerequisites

- Python >= 3.10
- Rust toolchain
- Git

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/wl-commands/py_wlcommands.git
cd py_wlcommands

# Install dependencies
pip install -e .

# Or if using uv
uv pip install -e .
```

### Running Tests

```bash
# Run all tests
pytest tests/

# Or using the wl command
wl test
```

### Building Distribution Packages

```bash
# Build with wl command
wl build dist

# Or directly with maturin
maturin build --release --out dist --sdist
```

## CI/CD

This project uses GitHub Actions for continuous integration and deployment:

- **CI**: Runs tests on multiple platforms (Ubuntu, Windows, macOS) and Python versions (3.10, 3.11, 3.12)
- **Code Quality**: Runs linting and type checking
- **Publish**: Automatically publishes to PyPI when a new tag is pushed

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.