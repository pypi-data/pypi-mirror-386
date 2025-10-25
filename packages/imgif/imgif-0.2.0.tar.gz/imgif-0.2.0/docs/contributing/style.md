# Code Style Guide

This guide outlines the coding standards and style conventions for the imgif project.

## Overview

imgif follows modern Python best practices with emphasis on:

- **Type safety** - Full type annotations
- **Readability** - Clear, self-documenting code
- **Consistency** - Uniform style throughout
- **Simplicity** - Straightforward implementations

## Code Formatting

### Formatter

We use [Ruff](https://docs.astral.sh/ruff/) for code formatting and linting.

```bash
# Format code
ruff format .

# Check formatting
ruff format --check .
```

### Line Length

- **Maximum line length**: 100 characters
- **Docstring line length**: 88 characters

```python
# Good
def convert(
    self,
    input_path: PathLike,
    output_path: PathLike,
    duration: Duration = 1.0,
) -> None:

# Avoid (too long)
def convert(self, input_path: PathLike, output_path: PathLike, duration: Duration = 1.0) -> None:
```

### Imports

Sort and organize imports:

```python
# Standard library imports
import os
import sys
from pathlib import Path
from typing import Optional

# Third-party imports
import click
from PIL import Image
from rich.console import Console

# Local imports
from .config import GifConfig
from .exceptions import ConversionError
```

Use Ruff to auto-sort imports:

```bash
ruff check --select I --fix .
```

### String Quotes

- Use **double quotes** for strings by default
- Use single quotes for dictionary keys when needed

```python
# Good
message = "Hello, world!"
config = {"key": "value"}

# Also acceptable
char = 'x'
sql = 'SELECT * FROM table WHERE name = "John"'
```

### Trailing Commas

Use trailing commas in multi-line structures:

```python
# Good
config = GifConfig(
    fps=10,
    optimize=True,
    width=800,
)

# Also good
names = [
    "Alice",
    "Bob",
    "Charlie",
]
```

## Type Annotations

### Required Annotations

All public functions, methods, and variables must have type annotations:

```python
# Good
def convert(
    self,
    input_path: PathLike,
    output_path: PathLike,
    duration: Duration = 1.0,
    loop: int = 0,
) -> None:
    """Convert images to GIF."""
    pass


# Bad (missing types)
def convert(self, input_path, output_path, duration=1.0, loop=0):
    pass
```

### Type Aliases

Use type aliases for complex types:

```python
# types.py
from pathlib import Path
from typing import Union

PathLike = Union[str, Path]
Duration = Union[float, list[float]]
```

### Optional Types

Use `Optional` for parameters that can be `None`:

```python
from typing import Optional

def resize(
    self,
    width: Optional[int] = None,
    height: Optional[int] = None,
) -> tuple[int, int]:
    pass
```

### Modern Type Syntax

Use Python 3.9+ type syntax when possible:

```python
# Good (Python 3.9+)
def get_files(self) -> list[Path]:
    return []

def get_config(self) -> dict[str, object]:
    return {}

# Avoid (old syntax)
from typing import List, Dict

def get_files(self) -> List[Path]:
    return []
```

## Documentation

### Docstring Style

Use Google-style docstrings:

```python
def convert(
    self,
    input_path: PathLike,
    output_path: PathLike,
    duration: Duration = 1.0,
    loop: int = 0,
) -> None:
    """
    Convert a sequence of images into an animated GIF.

    Args:
        input_path: Path to directory containing images or a single image file
        output_path: Path where the GIF should be saved
        duration: Duration per frame in seconds (or list of durations per frame)
        loop: Number of times the GIF should loop (0 = infinite)

    Raises:
        InvalidInputError: If input path doesn't exist or is invalid
        NoImagesFoundError: If no valid images found in input directory
        ImageLoadError: If images cannot be loaded
        ConversionError: If GIF creation fails

    Example:
        >>> converter = ImageToGifConverter()
        >>> converter.convert("./frames", "animation.gif", duration=0.5, loop=0)
    """
    pass
```

### Module Docstrings

Every module should have a docstring:

```python
"""
Core image to GIF conversion functionality.

This module provides the main ImageToGifConverter class which handles
the conversion of image sequences into animated GIF files.
"""
```

### Class Docstrings

Document class purpose and attributes:

```python
class ImageToGifConverter:
    """
    Converts sequences of images into animated GIF files.

    This class provides a simple interface for creating animated GIFs from
    a directory of images. It handles image loading, validation, and conversion
    with support for various configuration options.

    Example:
        >>> converter = ImageToGifConverter()
        >>> converter.convert("./images", "output.gif", duration=0.5)
        GIF created successfully!

    Attributes:
        console: Rich console instance for pretty output
    """
```

### Comments

Use comments sparingly, prefer self-documenting code:

```python
# Good (self-documenting)
def calculate_aspect_ratio(width: int, height: int) -> float:
    return width / height

# Less ideal (needs comment)
def calc_ar(w: int, h: int) -> float:
    # Calculate aspect ratio
    return w / h
```

Use comments for complex logic:

```python
# Calculate target size maintaining aspect ratio
# Use the smaller ratio to fit within bounds
width_ratio = target_width / current_width
height_ratio = target_height / current_height
ratio = min(width_ratio, height_ratio)
```

## Naming Conventions

### Functions and Variables

Use `snake_case`:

```python
# Good
def convert_images():
    pass

input_path = "./images"
output_path = "./output.gif"
frame_duration = 0.5

# Bad
def ConvertImages():
    pass

InputPath = "./images"
```

### Classes

Use `PascalCase`:

```python
# Good
class ImageToGifConverter:
    pass

class GifConfig:
    pass

# Bad
class image_to_gif_converter:
    pass
```

### Constants

Use `UPPER_SNAKE_CASE`:

```python
# Good
SUPPORTED_FORMATS = {".png", ".jpg", ".jpeg"}
DEFAULT_DURATION = 1.0
MAX_QUALITY = 100

# Bad
supported_formats = {".png", ".jpg"}
```

### Private Members

Use single underscore prefix:

```python
class Converter:
    def __init__(self):
        self._internal_state = None

    def _internal_method(self):
        pass

    def public_method(self):
        self._internal_method()
```

## Code Organization

### Class Structure

Organize class members in this order:

```python
class MyClass:
    """Class docstring."""

    # 1. Class variables
    CLASS_CONSTANT = 42

    # 2. Constructor
    def __init__(self, param: str) -> None:
        """Initialize."""
        self.param = param
        self._private = None

    # 3. Public methods
    def public_method(self) -> int:
        """Public method."""
        return self._private_method()

    # 4. Private methods
    def _private_method(self) -> int:
        """Private method."""
        return 42

    # 5. Special methods
    def __str__(self) -> str:
        """String representation."""
        return f"MyClass({self.param})"
```

### Function Length

Keep functions focused and concise:

```python
# Good (focused, single responsibility)
def validate_input(path: Path) -> None:
    """Validate input path exists and is readable."""
    if not path.exists():
        raise InvalidInputError(f"Path does not exist: {path}")

def load_images(paths: list[Path]) -> list[Image.Image]:
    """Load images from paths."""
    return [Image.open(p) for p in paths]

# Less ideal (too long, multiple responsibilities)
def process_everything(path: Path) -> list[Image.Image]:
    """Do everything."""
    if not path.exists():
        raise InvalidInputError(f"Path does not exist: {path}")
    # ... 50 more lines
```

## Error Handling

### Exception Handling

Be specific with exceptions:

```python
# Good (specific)
try:
    image = Image.open(path)
except FileNotFoundError as e:
    raise ImageLoadError(f"Image not found: {path}") from e
except PermissionError as e:
    raise ImageLoadError(f"Permission denied: {path}") from e

# Bad (too broad)
try:
    image = Image.open(path)
except Exception as e:
    raise ImageLoadError(f"Error: {e}")
```

### Custom Exceptions

Use descriptive exception names and messages:

```python
# Good
class NoImagesFoundError(Img2GifError):
    """Raised when no valid images are found in the input directory."""
    pass

raise NoImagesFoundError(f"No valid images found in: {input_path}")

# Bad
class Error(Exception):
    pass

raise Error("error")
```

## Best Practices

### Use Pathlib

Prefer `pathlib.Path` over string paths:

```python
# Good
from pathlib import Path

def process_file(path: Path) -> None:
    if path.exists():
        content = path.read_text()

# Less ideal
import os

def process_file(path: str) -> None:
    if os.path.exists(path):
        with open(path) as f:
            content = f.read()
```

### Use Dataclasses

Use `@dataclass` for data containers:

```python
from dataclasses import dataclass

@dataclass
class GifConfig:
    """Configuration for GIF generation."""
    duration: float = 1.0
    loop: int = 0
    optimize: bool = False
```

### Use Context Managers

Use context managers for resources:

```python
# Good
with Image.open(path) as img:
    img = img.convert("RGB")

# Less ideal
img = Image.open(path)
img = img.convert("RGB")
# img not properly closed
```

### Use List Comprehensions

Prefer comprehensions for simple transformations:

```python
# Good
image_files = [f for f in path.iterdir() if f.suffix == ".png"]

# Less ideal
image_files = []
for f in path.iterdir():
    if f.suffix == ".png":
        image_files.append(f)
```

But avoid complex nested comprehensions:

```python
# Bad (too complex)
result = [[y for y in x if y > 0] for x in matrix if sum(x) > 10]

# Better
filtered_rows = [row for row in matrix if sum(row) > 10]
result = [[value for value in row if value > 0] for row in filtered_rows]
```

### Avoid Magic Numbers

Use named constants:

```python
# Good
DEFAULT_QUALITY = 85
MIN_QUALITY = 1
MAX_QUALITY = 100

def validate_quality(quality: int) -> None:
    if not MIN_QUALITY <= quality <= MAX_QUALITY:
        raise ValueError(f"Quality must be between {MIN_QUALITY} and {MAX_QUALITY}")

# Bad
def validate_quality(quality: int) -> None:
    if not 1 <= quality <= 100:
        raise ValueError("Quality must be between 1 and 100")
```

## Testing Style

### Test Naming

Use descriptive test names:

```python
# Good
def test_convert_creates_gif_file():
    pass

def test_convert_raises_error_on_invalid_input():
    pass

def test_config_validates_fps_range():
    pass

# Bad
def test_1():
    pass

def test_convert():
    pass
```

### Test Organization

Follow AAA pattern:

```python
def test_convert():
    """Test GIF conversion."""
    # Arrange
    converter = ImageToGifConverter()
    output = Path("output.gif")

    # Act
    converter.convert("./images", output)

    # Assert
    assert output.exists()
```

See [Testing Guide](testing.md) for more details.

## Linting

### Running Linter

```bash
# Check for issues
ruff check .

# Auto-fix issues
ruff check --fix .

# Format code
ruff format .
```

### Linting Rules

Key rules enforced:

- Line length (100 characters)
- Import sorting
- Unused imports
- Unused variables
- Undefined names
- Type annotation requirements

### Ignoring Rules

Avoid ignoring rules, but when necessary:

```python
# Ignore specific rule on a line
result = some_function()  # noqa: E501

# Ignore rule for entire file (top of file)
# ruff: noqa: E501
```

## Git Commit Style

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```bash
# Good
git commit -m "feat: add support for WebP format"
git commit -m "fix: handle corrupted images gracefully"
git commit -m "docs: update API reference"
git commit -m "test: add tests for resize functionality"
git commit -m "refactor: simplify image loading logic"
git commit -m "chore: update dependencies"

# Bad
git commit -m "updates"
git commit -m "fix stuff"
git commit -m "wip"
```

### Commit Types

- **feat** - New features
- **fix** - Bug fixes
- **docs** - Documentation changes
- **test** - Test additions/changes
- **refactor** - Code refactoring
- **chore** - Build process/tooling changes
- **style** - Code style changes (formatting)
- **perf** - Performance improvements

## IDE Configuration

### VS Code

Recommended `settings.json`:

```json
{
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.fixAll": true,
      "source.organizeImports": true
    }
  },
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true
}
```

### PyCharm

Configure Ruff as external tool:

- **Program**: `ruff`
- **Arguments**: `format $FilePath$`
- **Working directory**: `$ProjectFileDir$`

## Pre-commit Checklist

Before committing, ensure:

- [ ] Code is formatted: `ruff format .`
- [ ] No linting errors: `ruff check .`
- [ ] All tests pass: `hatch run test`
- [ ] Type annotations are complete
- [ ] Docstrings are up-to-date
- [ ] Commit message follows convention

## Resources

- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [PEP 8](https://pep8.org/) - Python style guide
- [PEP 484](https://www.python.org/dev/peps/pep-0484/) - Type hints
- [Google Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Conventional Commits](https://www.conventionalcommits.org/)

## Next Steps

- Read [Development Guide](development.md) for setup
- Review [Testing Guide](testing.md) for test standards
- Check [API Reference](../api/converter.md) for examples
- See [Contributing](development.md) for workflow
