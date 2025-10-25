# Development Guide

Welcome to the imgif development guide! This guide will help you set up your development environment and contribute to the project.

## Prerequisites

Before you begin, ensure you have:

- Python 3.9 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- Git
- A GitHub account (for contributing)

## Setting Up Development Environment

### 1. Fork and Clone

Fork the repository on GitHub and clone it locally:

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/img2gif.git
cd img2gif

# Add upstream remote
git remote add upstream https://github.com/atick-faisal/img2gif.git
```

### 2. Install Dependencies

Use `uv` to install all dependencies including development tools:

```bash
# Install all dependencies (including dev dependencies)
uv sync
```

This installs:

- Core dependencies (Pillow, rich, click)
- Development tools (pytest, ruff, hatch)
- Documentation tools (mkdocs, mkdocs-material)

### 3. Verify Installation

Verify everything is set up correctly:

```bash
# Run tests
hatch run test

# Run linter
ruff check .

# Serve documentation
mkdocs serve
```

## Project Structure

```
img2gif/
├── src/
│   └── img2gif/           # Main package
│       ├── __init__.py    # Public API exports
│       ├── converter.py   # ImageToGifConverter class
│       ├── config.py      # GifConfig class
│       ├── exceptions.py  # Custom exceptions
│       ├── types.py       # Type definitions
│       ├── cli.py         # CLI implementation
│       └── __main__.py    # Entry point
├── tests/                 # Test suite (mirrors src structure)
│   ├── test_converter.py
│   ├── test_config.py
│   ├── test_exceptions.py
│   └── test_cli.py
├── docs/                  # Documentation
│   ├── index.md
│   ├── getting-started/
│   ├── guide/
│   ├── api/
│   └── contributing/
├── .github/
│   └── workflows/         # CI/CD workflows
├── pyproject.toml         # Project configuration
├── mkdocs.yml            # Documentation configuration
└── README.md
```

## Development Workflow

### 1. Create a Feature Branch

```bash
# Update main branch
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/your-feature-name
```

### 2. Make Changes

Edit code following our [code style guidelines](style.md).

### 3. Run Tests

Always run tests before committing:

```bash
# Run all tests
hatch run test

# Run specific test file
hatch run pytest tests/test_converter.py

# Run with coverage
hatch run pytest --cov=src --cov-report=term-missing
```

### 4. Run Linter

Format and lint your code:

```bash
# Auto-format code
ruff format .

# Check for linting issues
ruff check .

# Auto-fix linting issues
ruff check --fix .
```

### 5. Commit Changes

Follow [Conventional Commits](https://www.conventionalcommits.org/) specification:

```bash
# Stage changes
git add .

# Commit with conventional commit message
git commit -m "feat: add new configuration option"
git commit -m "fix: handle corrupted images gracefully"
git commit -m "docs: update API reference"
```

**Commit types:**

- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation changes
- `test:` - Test additions/changes
- `refactor:` - Code refactoring
- `chore:` - Build process/tooling changes

### 6. Push and Create PR

```bash
# Push to your fork
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## Adding New Features

### 1. Plan Your Feature

Before coding:

- Open an issue to discuss the feature
- Get feedback from maintainers
- Plan the implementation

### 2. Write Tests First (TDD)

Write tests before implementing:

```python
# tests/test_new_feature.py
import pytest
from imgif import ImageToGifConverter

def test_new_feature():
    """Test the new feature."""
    converter = ImageToGifConverter()
    # Test your feature
    assert result == expected
```

### 3. Implement Feature

Implement the feature following our code standards:

```python
# src/img2gif/converter.py
def new_feature(self, param: str) -> int:
    """
    Brief description of feature.

    Args:
        param: Description of parameter

    Returns:
        Description of return value

    Example:
        >>> converter = ImageToGifConverter()
        >>> result = converter.new_feature("test")
        >>> result
        42
    """
    # Implementation
    return 42
```

### 4. Add Documentation

Document your feature in:

- Docstrings (code documentation)
- API reference (docs/api/)
- User guide (docs/guide/)
- Examples (docs/getting-started/examples.md)

### 5. Update Tests

Ensure 100% coverage:

```bash
# Run tests with coverage
hatch run pytest --cov=src --cov-report=term-missing

# Check coverage report
# Aim for 100% coverage
```

## Fixing Bugs

### 1. Reproduce the Bug

Create a failing test that demonstrates the bug:

```python
def test_bug_reproduction():
    """Reproduce the reported bug."""
    # Setup that triggers the bug
    converter = ImageToGifConverter()

    # This should fail before the fix
    with pytest.raises(ExpectedException):
        converter.problematic_method()
```

### 2. Fix the Bug

Fix the issue in the source code.

### 3. Verify Fix

Ensure the test now passes:

```bash
hatch run pytest tests/test_bug_fix.py -v
```

### 4. Add Regression Test

Keep the test to prevent regression.

## Working with Tests

### Running Tests

```bash
# Run all tests
hatch run test

# Run specific test file
hatch run pytest tests/test_converter.py

# Run specific test
hatch run pytest tests/test_converter.py::test_convert

# Run with verbose output
hatch run pytest -v

# Run with coverage
hatch run pytest --cov=src --cov-report=html
```

### Test Matrix

Test across multiple Python versions:

```bash
# Test on all Python versions (3.9, 3.11, 3.13)
hatch run test:all

# Test on specific version
hatch run test:py39
hatch run test:py311
hatch run test:py313
```

### Writing Tests

Follow these guidelines:

```python
import pytest
from pathlib import Path
from imgif import ImageToGifConverter

class TestConverter:
    """Test suite for ImageToGifConverter."""

    def test_basic_conversion(self, tmp_path):
        """Test basic GIF conversion."""
        # Setup
        converter = ImageToGifConverter()
        output = tmp_path / "output.gif"

        # Execute
        converter.convert("./test_images", output)

        # Assert
        assert output.exists()
        assert output.stat().st_size > 0

    def test_error_handling(self):
        """Test error handling for invalid input."""
        converter = ImageToGifConverter()

        with pytest.raises(InvalidInputError):
            converter.convert("./nonexistent", "output.gif")
```

See [Testing Guide](testing.md) for detailed testing practices.

## Working with Documentation

### Serving Documentation Locally

```bash
# Start development server
mkdocs serve

# Open http://127.0.0.1:8000 in your browser
```

### Building Documentation

```bash
# Build static site
mkdocs build

# Output is in site/ directory
```

### Documentation Structure

- **index.md** - Home page
- **getting-started/** - Installation, quickstart, examples
- **guide/** - User guides (basic usage, configuration, CLI)
- **api/** - API reference (converter, config, exceptions)
- **contributing/** - Development guides (this section)

### Writing Documentation

Use MkDocs Material features:

```markdown
!!! note "Note Title"
    This is a note admonition.

!!! tip
    This is a helpful tip.

!!! warning
    This is a warning.

=== "Tab 1"
    Content for tab 1

=== "Tab 2"
    Content for tab 2
```

## Dependency Management

### Adding Dependencies

```bash
# Add runtime dependency
uv add pillow

# Add development dependency
uv add --dev pytest

# Update dependencies
uv sync
```

### Updating Dependencies

```bash
# Update all dependencies
uv sync --upgrade

# Update specific package
uv add pillow --upgrade
```

## Pre-commit Hooks

Pre-commit hooks automatically run linting and tests:

### Setup

Hooks are configured in `.pre-commit-config.yaml` (if available) or run manually:

```bash
# Before committing, always run:
ruff format .
ruff check --fix .
hatch run test
```

### Bypass Hooks (Not Recommended)

Only in emergencies:

```bash
git commit --no-verify -m "emergency fix"
```

## Continuous Integration

### GitHub Actions Workflows

#### CI Workflow

Runs on every push and PR:

- Linting with ruff
- Tests on Python 3.9, 3.11, 3.13
- Coverage reporting

#### CD Workflow

Runs on tags/releases:

- Linting
- Testing
- Publishing to PyPI

### Local CI Simulation

Simulate CI locally:

```bash
# Run linter (as CI does)
ruff check .

# Run tests on all versions (as CI does)
hatch run test:all

# Check coverage
hatch run pytest --cov=src --cov-report=term-missing
```

## Getting Help

- **Issues** - [GitHub Issues](https://github.com/atick-faisal/img2gif/issues)
- **Discussions** - [GitHub Discussions](https://github.com/atick-faisal/img2gif/discussions)
- **Documentation** - Check existing docs first

## Code Review Process

### Submitting PRs

1. Ensure all tests pass
2. Ensure linting passes
3. Update documentation
4. Write clear PR description
5. Reference related issues

### PR Checklist

- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Linting passes
- [ ] All tests pass
- [ ] Conventional commit messages
- [ ] PR description is clear

### Review Guidelines

Reviewers will check:

- Code quality and style
- Test coverage
- Documentation completeness
- Backward compatibility
- Performance implications

## Release Process

Releases are handled by maintainers:

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create git tag: `git tag v0.2.0`
4. Push tag: `git push origin v0.2.0`
5. GitHub Actions publishes to PyPI

### Versioning

Follow [Semantic Versioning](https://semver.org/):

- **MAJOR** (v1.0.0 → v2.0.0) - Breaking changes
- **MINOR** (v1.0.0 → v1.1.0) - New features (backward compatible)
- **PATCH** (v1.0.0 → v1.0.1) - Bug fixes (backward compatible)

## Best Practices

### Code Quality

- Write clear, self-documenting code
- Add type annotations everywhere
- Write comprehensive docstrings
- Keep functions small and focused
- Avoid premature optimization

### Testing

- Aim for 100% coverage
- Test edge cases
- Test error conditions
- Use descriptive test names
- Follow AAA pattern (Arrange, Act, Assert)

### Documentation

- Keep documentation up-to-date
- Include code examples
- Write for your audience
- Use clear, simple language

### Git Workflow

- Keep commits atomic and focused
- Write clear commit messages
- Rebase before pushing (when appropriate)
- Keep branch up-to-date with main

## Next Steps

- Read the [Testing Guide](testing.md)
- Review [Code Style Guidelines](style.md)
- Check out [Examples](../getting-started/examples.md)
- Explore the [API Reference](../api/converter.md)
