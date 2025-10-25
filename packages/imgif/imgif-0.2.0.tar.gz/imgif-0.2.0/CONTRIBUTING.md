# 🤝 Contributing to imgif

Thank you for your interest in contributing to imgif! We love community contributions and appreciate your help making this library even better! 🎉

## 🚀 Getting Started

### Prerequisites

- Python 3.9 or higher 🐍
- [uv](https://github.com/astral-sh/uv) package manager
- Git

### Setting Up Your Development Environment

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/atick-faisal/img2gif.git
   cd img2gif
   ```

2. **Install dependencies**
   ```bash
   uv sync
   ```

3. **Install pre-commit hooks**
   ```bash
   pre-commit install
   ```

4. **Create a new branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

## 🎯 Development Workflow

### Making Changes

1. **Write code** with proper type annotations
2. **Add tests** - We aim for 100% coverage! 🎯
3. **Add docstrings** - Help others understand your code 📝
4. **Format & lint** - Run `ruff format .` and `ruff check .`
5. **Run tests** - Make sure everything passes! ✅

### Code Standards

#### ✨ Type Annotations
All functions, methods, and variables must have type annotations:

```python
def convert_images(paths: list[str], output: str) -> None:
    """Convert images to GIF."""
    ...
```

#### 📚 Documentation
All public APIs require comprehensive docstrings:

```python
def my_function(param: str) -> int:
    """
    Brief description of what this does.

    Args:
        param: Description of parameter

    Returns:
        Description of return value

    Raises:
        ValueError: When something goes wrong

    Example:
        >>> my_function("hello")
        5
    """
```

#### 🧪 Testing
- Write unit tests for individual components
- Write E2E tests for complete workflows
- Mirror the source tree structure in tests
- Use descriptive test names
- Aim for 100% coverage

### Running Tests

```bash
# Run all tests
hatch run test:all

# Run with coverage report
hatch run test:cov

# Run specific test file
hatch run pytest tests/test_converter.py

# Run specific test
hatch run pytest tests/test_converter.py::test_function_name
```

### Code Quality Checks

```bash
# Format code
ruff format .

# Run linter
ruff check .

# Auto-fix linting issues
ruff check --fix .
```

## 📝 Commit Message Guidelines

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation changes
- `test:` - Test additions/changes
- `refactor:` - Code refactoring
- `chore:` - Build process/tooling changes
- `ci:` - CI/CD changes

**Examples:**
```
feat: add support for custom frame durations
fix: resolve memory leak in image loading
docs: update installation instructions
test: add tests for edge cases in converter
```

## 🔄 Pull Request Process

1. **Update tests** - Add or modify tests as needed
2. **Update documentation** - Keep README and docs in sync
3. **Run the full test suite** - Make sure everything passes
4. **Push your changes** and create a pull request
5. **Describe your changes** - What, why, and how
6. **Wait for review** - We'll review as soon as possible! ⏰

### PR Checklist

- [ ] Tests pass locally
- [ ] Code is formatted (`ruff format .`)
- [ ] No linting errors (`ruff check .`)
- [ ] Tests added/updated for changes
- [ ] Documentation updated if needed
- [ ] Commit messages follow convention
- [ ] PR description is clear and complete

## 🐛 Reporting Bugs

Found a bug? Please create an issue with:

1. **Clear title** - Describe the issue briefly
2. **Steps to reproduce** - How can we see the bug?
3. **Expected behavior** - What should happen?
4. **Actual behavior** - What actually happens?
5. **Environment** - Python version, OS, etc.
6. **Code sample** - Minimal example if possible

## 💡 Suggesting Features

Have an idea? We'd love to hear it! Please create an issue with:

1. **Clear description** - What do you want to add?
2. **Use case** - Why is this useful?
3. **Example** - How would it work?

## 📜 Code of Conduct

Be kind, respectful, and constructive. We're all here to learn and build something great together! 🌟

## 🎉 Recognition

All contributors will be recognized in our README and release notes. Thank you for making imgif better! 🙏

## ❓ Questions?

Feel free to open an issue with your question or reach out to the maintainers!

---

Happy coding! 🚀✨
