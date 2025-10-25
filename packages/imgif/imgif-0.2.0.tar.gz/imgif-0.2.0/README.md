# 🎬 imgif

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://github.com/atick-faisal/img2gif/workflows/CI/badge.svg)](https://github.com/atick-faisal/img2gif/actions)
[![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen.svg)](https://github.com/atick-faisal/img2gif)

> ✨ A playful Python library for converting image sequences into animated GIFs with ease!

Turn your image sequences into delightful animated GIFs with just a few lines of code. Whether you're creating animations from screenshots, visualizing data, or just having fun, `imgif` makes it simple and enjoyable! 🚀

## 🌟 Features

- 🎨 **Simple API** - Convert images to GIF in just 3 lines of code
- ⚡ **Fast & Efficient** - Built on Pillow for optimal performance
- 🎛️ **Highly Configurable** - Control duration, quality, size, and more
- 💻 **CLI Interface** - Use directly from the command line
- 📝 **Fully Typed** - Complete type annotations for great IDE support
- 🧪 **100% Test Coverage** - Reliable and well-tested
- 🎭 **Rich Output** - Beautiful progress indicators and error messages

## 📦 Installation

```bash
# Using pip
pip install imgif

# Using uv (recommended for development)
uv pip install imgif
```

## 🚀 Quick Start

### Python API

```python
from img2gif import ImageToGifConverter

# Create converter
converter = ImageToGifConverter()

# Convert images to GIF
converter.convert(
    input_dir="./my_images",
    output_path="./output.gif",
    duration=0.5,  # seconds per frame
)

print("🎉 GIF created successfully!")
```

### Command Line

```bash
# Basic usage
imgif ./my_images output.gif

# With options
imgif ./my_images output.gif --duration 0.5 --loop 0

# See all options
imgif --help
```

## 📖 Documentation

Full documentation is available at [imgif.readthedocs.io](https://imgif.readthedocs.io) (coming soon!)

## 🛠️ Development

### Setup

```bash
# Clone the repository
git clone https://github.com/atick-faisal/img2gif.git
cd img2gif

# Install dependencies using uv
uv sync

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run tests on default Python version
hatch run test:all

# Run tests on all supported Python versions
hatch run test:all

# Run with coverage
hatch run test:cov
```

### Linting & Formatting

```bash
# Check code
ruff check .

# Format code
ruff format .
```

## 🤝 Contributing

Contributions are welcome! Please check out our [Contributing Guide](CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Pillow](https://pillow.readthedocs.io/) 📸
- CLI powered by [click](https://click.palletsprojects.com/) 🖱️
- Beautiful output by [rich](https://rich.readthedocs.io/) 💎

---

Made with ❤️ and Python 🐍
