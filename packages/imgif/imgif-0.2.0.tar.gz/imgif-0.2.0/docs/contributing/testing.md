# Testing Guide

This guide covers testing practices, conventions, and guidelines for the imgif project.

## Testing Philosophy

imgif follows these testing principles:

- **100% test coverage** - All code paths should be tested
- **Test-Driven Development (TDD)** - Write tests before implementation when possible
- **Unit and E2E tests** - Test both individual components and complete workflows
- **Clear test names** - Tests should be self-documenting
- **AAA pattern** - Arrange, Act, Assert structure

## Test Structure

### Directory Structure

The test directory mirrors the source tree:

```
tests/
├── test_converter.py      # Tests for converter.py
├── test_config.py         # Tests for config.py
├── test_exceptions.py     # Tests for exceptions.py
├── test_cli.py            # Tests for cli.py
├── test_types.py          # Tests for types.py
└── conftest.py            # Shared fixtures
```

### Test Organization

Each test file follows this structure:

```python
"""Tests for module_name module."""

import pytest
from imgif import ClassToTest


class TestClassName:
    """Test suite for ClassName."""

    def test_feature_success(self):
        """Test successful feature execution."""
        # Arrange
        instance = ClassToTest()

        # Act
        result = instance.method()

        # Assert
        assert result == expected

    def test_feature_error(self):
        """Test error handling for feature."""
        # Test error conditions
        pass
```

## Running Tests

### Basic Commands

```bash
# Run all tests
hatch run test

# Run specific test file
hatch run pytest tests/test_converter.py

# Run specific test class
hatch run pytest tests/test_converter.py::TestImageToGifConverter

# Run specific test method
hatch run pytest tests/test_converter.py::TestImageToGifConverter::test_convert

# Run with verbose output
hatch run pytest -v

# Run with extra verbose output
hatch run pytest -vv
```

### Coverage

```bash
# Run with coverage report
hatch run pytest --cov=src --cov-report=term-missing

# Generate HTML coverage report
hatch run pytest --cov=src --cov-report=html

# Open coverage report
open htmlcov/index.html
```

### Test Matrix

Test across multiple Python versions:

```bash
# Test on all Python versions
hatch run test:all

# Test on specific version
hatch run test:py39   # Python 3.9
hatch run test:py311  # Python 3.11
hatch run test:py313  # Python 3.13
```

## Writing Tests

### Test Naming

Use descriptive test names that explain what is being tested:

```python
# Good test names
def test_convert_creates_gif_file():
def test_convert_raises_error_on_invalid_input():
def test_config_validates_fps_range():
def test_resize_maintains_aspect_ratio():

# Bad test names
def test_1():
def test_convert():
def test_error():
```

### AAA Pattern

Follow the Arrange-Act-Assert pattern:

```python
def test_convert_creates_gif():
    """Test that convert() creates a GIF file."""
    # Arrange - Set up test conditions
    converter = ImageToGifConverter()
    output_path = Path("test_output.gif")

    # Act - Execute the code being tested
    converter.convert("./test_images", output_path)

    # Assert - Verify the results
    assert output_path.exists()
    assert output_path.stat().st_size > 0
```

### Using Fixtures

Use pytest fixtures for setup and teardown:

```python
# conftest.py
import pytest
from pathlib import Path

@pytest.fixture
def temp_image_dir(tmp_path):
    """Create temporary directory with test images."""
    image_dir = tmp_path / "images"
    image_dir.mkdir()

    # Create test images
    from PIL import Image
    for i in range(3):
        img = Image.new('RGB', (100, 100), color=(i*80, 100, 200))
        img.save(image_dir / f"frame_{i:03d}.png")

    return image_dir


# test_converter.py
def test_convert_with_fixture(temp_image_dir, tmp_path):
    """Test conversion using fixture."""
    converter = ImageToGifConverter()
    output = tmp_path / "output.gif"

    converter.convert(temp_image_dir, output)

    assert output.exists()
```

### Parametrized Tests

Test multiple scenarios with parametrization:

```python
@pytest.mark.parametrize("fps,expected_duration", [
    (10, 0.1),
    (20, 0.05),
    (24, 0.041666666666666664),
    (30, 0.03333333333333333),
])
def test_fps_to_duration(fps, expected_duration):
    """Test FPS to duration conversion."""
    config = GifConfig(fps=fps)
    assert config.get_duration() == pytest.approx(expected_duration)


@pytest.mark.parametrize("width,height,maintain_ratio,expected", [
    (800, None, True, (800, 600)),
    (None, 600, True, (800, 600)),
    (800, 800, True, (800, 600)),
    (800, 800, False, (800, 800)),
])
def test_resize_calculations(width, height, maintain_ratio, expected):
    """Test resize calculations with different configs."""
    config = GifConfig(
        width=width,
        height=height,
        maintain_aspect_ratio=maintain_ratio
    )
    result = config.get_target_size(1600, 1200)
    assert result == expected
```

## Unit Tests

### Testing Classes

```python
class TestImageToGifConverter:
    """Test suite for ImageToGifConverter class."""

    def test_init(self):
        """Test converter initialization."""
        converter = ImageToGifConverter()
        assert converter.console is not None

    def test_convert_basic(self, temp_image_dir, tmp_path):
        """Test basic conversion."""
        converter = ImageToGifConverter()
        output = tmp_path / "output.gif"

        converter.convert(temp_image_dir, output)

        assert output.exists()
        assert output.stat().st_size > 0

    def test_convert_with_duration(self, temp_image_dir, tmp_path):
        """Test conversion with custom duration."""
        converter = ImageToGifConverter()
        output = tmp_path / "output.gif"

        converter.convert(temp_image_dir, output, duration=0.5)

        assert output.exists()

    def test_convert_with_loop(self, temp_image_dir, tmp_path):
        """Test conversion with custom loop count."""
        converter = ImageToGifConverter()
        output = tmp_path / "output.gif"

        converter.convert(temp_image_dir, output, loop=3)

        assert output.exists()
```

### Testing Functions

```python
def test_create_config():
    """Test create_config factory function."""
    config = create_config(fps=10, optimize=True)

    assert config.fps == 10
    assert config.optimize is True
    assert config.duration == 1.0  # default
```

## Error Testing

### Testing Exceptions

```python
def test_invalid_input_error():
    """Test InvalidInputError is raised for nonexistent path."""
    converter = ImageToGifConverter()

    with pytest.raises(InvalidInputError) as exc_info:
        converter.convert("./nonexistent", "output.gif")

    assert "does not exist" in str(exc_info.value)


def test_no_images_found_error(tmp_path):
    """Test NoImagesFoundError for empty directory."""
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    converter = ImageToGifConverter()

    with pytest.raises(NoImagesFoundError) as exc_info:
        converter.convert(empty_dir, "output.gif")

    assert "No valid images found" in str(exc_info.value)


def test_config_validation_error():
    """Test InvalidConfigurationError for invalid config."""
    with pytest.raises(InvalidConfigurationError):
        GifConfig(fps=-1)

    with pytest.raises(InvalidConfigurationError):
        GifConfig(quality=150)
```

### Testing Error Messages

```python
def test_error_message_format():
    """Test error messages are informative."""
    converter = ImageToGifConverter()

    try:
        converter.convert("./nonexistent", "output.gif")
    except InvalidInputError as e:
        error_msg = str(e)
        assert "./nonexistent" in error_msg
        assert "does not exist" in error_msg.lower()
```

## Integration Tests

### E2E Tests

Test complete workflows:

```python
def test_end_to_end_conversion(temp_image_dir, tmp_path):
    """Test complete conversion workflow."""
    # Setup
    converter = ImageToGifConverter()
    output = tmp_path / "animation.gif"

    # Execute complete workflow
    converter.convert(
        input_path=temp_image_dir,
        output_path=output,
        duration=0.5,
        loop=0
    )

    # Verify results
    assert output.exists()
    assert output.stat().st_size > 0

    # Verify GIF properties
    from PIL import Image
    with Image.open(output) as img:
        assert img.format == "GIF"
        assert img.is_animated


def test_config_workflow(temp_image_dir, tmp_path):
    """Test conversion with configuration."""
    # Create configuration
    config = GifConfig(
        fps=10,
        optimize=True,
        width=400,
        maintain_aspect_ratio=True
    )

    # Convert with config
    converter = ImageToGifConverter()
    output = tmp_path / "optimized.gif"
    converter.convert_with_config(temp_image_dir, output, config)

    # Verify
    assert output.exists()

    from PIL import Image
    with Image.open(output) as img:
        assert img.size[0] == 400  # width was resized
```

## CLI Tests

### Testing Click Commands

```python
from click.testing import CliRunner
from imgif.cli import main


def test_cli_basic(temp_image_dir, tmp_path):
    """Test basic CLI usage."""
    runner = CliRunner()
    output = tmp_path / "output.gif"

    result = runner.invoke(main, [str(temp_image_dir), str(output)])

    assert result.exit_code == 0
    assert output.exists()


def test_cli_with_options(temp_image_dir, tmp_path):
    """Test CLI with options."""
    runner = CliRunner()
    output = tmp_path / "output.gif"

    result = runner.invoke(main, [
        str(temp_image_dir),
        str(output),
        "--fps", "10",
        "--optimize",
        "--width", "800"
    ])

    assert result.exit_code == 0
    assert output.exists()


def test_cli_error_handling():
    """Test CLI error handling."""
    runner = CliRunner()

    result = runner.invoke(main, ["./nonexistent", "output.gif"])

    assert result.exit_code != 0
    assert "Error" in result.output
```

## Mock and Patch

### Mocking External Dependencies

```python
from unittest.mock import Mock, patch


def test_with_mock():
    """Test using mocks."""
    with patch('img2gif.converter.Image') as mock_image:
        # Setup mock
        mock_img = Mock()
        mock_image.open.return_value = mock_img

        # Test code that uses Image
        converter = ImageToGifConverter()
        # ... test with mocked Image
```

## Test Fixtures

### Common Fixtures

```python
# conftest.py
import pytest
from pathlib import Path
from PIL import Image


@pytest.fixture
def sample_image(tmp_path):
    """Create a sample test image."""
    img_path = tmp_path / "sample.png"
    img = Image.new('RGB', (100, 100), color='red')
    img.save(img_path)
    return img_path


@pytest.fixture
def image_sequence(tmp_path):
    """Create a sequence of test images."""
    image_dir = tmp_path / "frames"
    image_dir.mkdir()

    for i in range(5):
        img = Image.new('RGB', (100, 100), color=(i*50, 100, 200))
        img.save(image_dir / f"frame_{i:03d}.png")

    return image_dir


@pytest.fixture
def gif_config():
    """Provide default GifConfig for tests."""
    return GifConfig(fps=10, optimize=True, width=800)
```

## Performance Tests

### Benchmarking

```python
import time


def test_conversion_performance(temp_image_dir, tmp_path):
    """Test conversion performance."""
    converter = ImageToGifConverter()
    output = tmp_path / "output.gif"

    start = time.time()
    converter.convert(temp_image_dir, output)
    duration = time.time() - start

    # Should complete in reasonable time
    assert duration < 5.0  # 5 seconds
```

## Coverage Goals

### Target Coverage

- **Overall**: 100% coverage
- **Per module**: 100% coverage
- **Per class**: 100% coverage

### Checking Coverage

```bash
# Generate coverage report
hatch run pytest --cov=src --cov-report=term-missing

# Output shows:
# Name                          Stmts   Miss  Cover   Missing
# -----------------------------------------------------------
# src/img2gif/__init__.py          10      0   100%
# src/img2gif/config.py            85      0   100%
# src/img2gif/converter.py        120      0   100%
# src/img2gif/exceptions.py        12      0   100%
# -----------------------------------------------------------
# TOTAL                           227      0   100%
```

## Test Best Practices

### Do's

- Write tests before code (TDD)
- Test edge cases
- Test error conditions
- Use descriptive test names
- Keep tests simple and focused
- Use fixtures for setup
- Test one thing per test
- Use parametrization for similar tests
- Clean up resources

### Don'ts

- Don't test implementation details
- Don't write interdependent tests
- Don't ignore failing tests
- Don't test third-party code
- Don't use sleep() for timing
- Don't hardcode paths
- Don't leave debug print statements

## Continuous Integration

Tests run automatically on:

- Every push to branches
- Every pull request
- All supported Python versions (3.9, 3.11, 3.13)

### Local CI Simulation

Simulate CI environment locally:

```bash
# Run tests as CI does
hatch run test:all

# Check coverage
hatch run pytest --cov=src --cov-report=term-missing

# Ensure 100% coverage before pushing
```

## Debugging Tests

### Running Specific Tests

```bash
# Run single test
hatch run pytest tests/test_converter.py::test_convert -vv

# Run with pdb debugger
hatch run pytest --pdb

# Drop into debugger on failure
hatch run pytest --pdb -x

# Show local variables on failure
hatch run pytest -l
```

### Print Debugging

```python
def test_with_debug_output(capsys):
    """Test with captured output."""
    print("Debug info")

    # Test code...

    captured = capsys.readouterr()
    assert "Debug info" in captured.out
```

## Next Steps

- Read [Development Guide](development.md) for setup instructions
- Review [Code Style Guide](style.md) for coding standards
- Check [API Reference](../api/converter.md) for API details
- See [Examples](../getting-started/examples.md) for usage patterns
