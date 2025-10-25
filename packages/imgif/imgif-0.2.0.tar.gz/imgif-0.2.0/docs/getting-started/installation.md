# 📦 Installation

## Requirements

- Python 3.9 or higher 🐍
- pip or uv package manager

## Install from PyPI

The easiest way to install imgif is from PyPI:

```bash
pip install imgif
```

This will install imgif and all required dependencies.

## Install from Source

For development or to get the latest features:

```bash
# Clone the repository
git clone https://github.com/atick-faisal/img2gif.git
cd img2gif

# Using uv (recommended)
uv sync

# Or using pip
pip install -e ".[dev]"
```

## Verify Installation

Check that imgif is installed correctly:

```bash
# Check version
imgif --help

# Or in Python
python -c "import imgif; print(imgif.__version__)"
```

## Dependencies

imgif requires the following packages:

- **Pillow** (≥10.0.0) - Image I/O and GIF operations 📸
- **rich** (≥13.7.0) - Beautiful terminal output 💎
- **click** (≥8.1.0) - CLI interface 🖱️

All dependencies are automatically installed.

## Optional Dependencies

For development:

```bash
pip install imgif[dev]
```

This includes:
- pytest - Testing framework
- pytest-cov - Coverage reporting
- ruff - Linting and formatting
- pre-commit - Git hooks

For documentation:

```bash
pip install imgif[docs]
```

This includes:
- mkdocs - Documentation generator
- mkdocs-material - Material theme
- pymdown-extensions - Markdown extensions

## Next Steps

Now that you have imgif installed:

- 🚀 [Quick Start Guide](quickstart.md) - Create your first GIF
- 🎨 [Examples](examples.md) - See what's possible
- 📚 [API Reference](../api/converter.md) - Dive into the details
