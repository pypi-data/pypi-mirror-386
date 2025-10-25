# Exceptions API

This page documents all custom exceptions used in imgif.

## Exception Hierarchy

```
Exception
└── Img2GifError (base exception)
    ├── InvalidInputError
    ├── NoImagesFoundError
    ├── ImageLoadError
    ├── ConversionError
    └── InvalidConfigurationError
```

**Module:** `imgif.exceptions`

**Source:** `src/img2gif/exceptions.py`

## Base Exception

### `Img2GifError`

Base exception for all imgif errors.

```python
class Img2GifError(Exception):
    """Base exception for all img2gif errors."""
```

**Usage:**

Use this to catch all imgif-related errors:

```python
from imgif import ImageToGifConverter, Img2GifError

converter = ImageToGifConverter()

try:
    converter.convert("./images", "output.gif")
except Img2GifError as e:
    print(f"imgif error occurred: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Input/Output Exceptions

### `InvalidInputError`

Raised when input directory or files are invalid.

```python
class InvalidInputError(Img2GifError):
    """Raised when input directory or files are invalid."""
```

**When raised:**

- Input path doesn't exist
- Input path is neither file nor directory
- Input file is not a supported image format

**Examples:**

```python
from imgif import ImageToGifConverter, InvalidInputError

converter = ImageToGifConverter()

# Path doesn't exist
try:
    converter.convert("./nonexistent", "output.gif")
except InvalidInputError as e:
    print(e)  # "Input path does not exist: ./nonexistent"

# Unsupported file format
try:
    converter.convert("./document.txt", "output.gif")
except InvalidInputError as e:
    print(e)  # "File is not a supported image format: .txt"
```

**Common causes:**

- Typo in path
- Path doesn't exist
- Wrong file type
- Insufficient permissions

**How to fix:**

- Verify the path exists
- Check file permissions
- Ensure the input is a supported image format

### `NoImagesFoundError`

Raised when no valid images are found in the input directory.

```python
class NoImagesFoundError(Img2GifError):
    """Raised when no valid images are found in the input directory."""
```

**When raised:**

- Input directory exists but contains no supported image files
- All files in directory have unsupported extensions

**Examples:**

```python
from imgif import ImageToGifConverter, NoImagesFoundError

converter = ImageToGifConverter()

# Empty directory
try:
    converter.convert("./empty_folder", "output.gif")
except NoImagesFoundError as e:
    print(e)  # "No valid images found in: ./empty_folder"

# Directory with only non-image files
try:
    converter.convert("./documents", "output.gif")
except NoImagesFoundError as e:
    print(e)  # "No valid images found in: ./documents"
```

**Common causes:**

- Empty directory
- Directory contains only non-image files
- All images have unsupported formats

**How to fix:**

- Verify directory contains image files
- Check file extensions are supported (`.png`, `.jpg`, `.jpeg`, `.bmp`, `.gif`, `.tiff`, `.webp`)
- Use the correct input path

## Processing Exceptions

### `ImageLoadError`

Raised when an image file cannot be loaded or is corrupted.

```python
class ImageLoadError(Img2GifError):
    """Raised when an image file cannot be loaded or is corrupted."""
```

**When raised:**

- Image file is corrupted
- File has wrong extension (e.g., `.png` file that's actually a `.txt`)
- Insufficient permissions to read file
- PIL/Pillow cannot decode the image

**Examples:**

```python
from imgif import ImageToGifConverter, ImageLoadError

converter = ImageToGifConverter()

# Corrupted image
try:
    converter.convert("./corrupted_images", "output.gif")
except ImageLoadError as e:
    print(e)  # "Failed to load image ./corrupted_images/broken.png (#1): ..."
```

**Common causes:**

- Corrupted image files
- Incomplete downloads
- Wrong file extensions
- Unsupported image encoding

**How to fix:**

- Verify image files are not corrupted
- Re-download or regenerate damaged images
- Use image validation tools to check file integrity
- Ensure files have correct extensions

### `ConversionError`

Raised when the GIF conversion process fails.

```python
class ConversionError(Img2GifError):
    """Raised when the GIF conversion process fails."""
```

**When raised:**

- Failed to create GIF file
- Insufficient disk space
- Output directory permissions issue
- PIL/Pillow GIF encoding error

**Examples:**

```python
from imgif import ImageToGifConverter, ConversionError

converter = ImageToGifConverter()

try:
    converter.convert("./images", "/read_only_path/output.gif")
except ConversionError as e:
    print(e)  # "Failed to create GIF: [Errno 13] Permission denied: ..."
```

**Common causes:**

- Insufficient disk space
- No write permissions for output directory
- Output path is invalid
- System resource limitations

**How to fix:**

- Check available disk space
- Verify write permissions for output directory
- Ensure output path is valid
- Try a different output location

## Configuration Exceptions

### `InvalidConfigurationError`

Raised when configuration parameters are invalid.

```python
class InvalidConfigurationError(Img2GifError):
    """Raised when configuration parameters are invalid."""
```

**When raised:**

- Invalid `GifConfig` parameters
- Values out of acceptable range
- Incompatible parameter combinations

**Examples:**

```python
from imgif import GifConfig, InvalidConfigurationError

# Invalid FPS
try:
    config = GifConfig(fps=-1)
except InvalidConfigurationError as e:
    print(e)  # "FPS must be > 0, got -1"

# Invalid quality
try:
    config = GifConfig(quality=150)
except InvalidConfigurationError as e:
    print(e)  # "Quality must be between 1 and 100, got 150"

# Invalid loop count
try:
    config = GifConfig(loop=-1)
except InvalidConfigurationError as e:
    print(e)  # "Loop count must be >= 0, got -1"

# Invalid duration
try:
    config = GifConfig(duration=0)
except InvalidConfigurationError as e:
    print(e)  # "Duration must be > 0, got 0"

# Invalid dimensions
try:
    config = GifConfig(width=-100)
except InvalidConfigurationError as e:
    print(e)  # "Width must be > 0, got -100"
```

**Parameter constraints:**

- **`loop`**: Must be >= 0
- **`duration`**: Must be > 0 (or all values > 0 if list)
- **`fps`**: Must be > 0 if set
- **`quality`**: Must be between 1 and 100
- **`width`**: Must be > 0 if set
- **`height`**: Must be > 0 if set

**Common causes:**

- Negative values for positive-only parameters
- Zero values for parameters requiring positive values
- Quality out of 1-100 range
- Empty duration list

**How to fix:**

- Check parameter values are within valid ranges
- Refer to [GifConfig API](config.md) for valid ranges
- Use sensible default values

## Error Handling Patterns

### Catch All imgif Errors

```python
from imgif import ImageToGifConverter, Img2GifError

converter = ImageToGifConverter()

try:
    converter.convert("./images", "output.gif")
except Img2GifError as e:
    print(f"Error: {e}")
    # Handle all imgif errors
```

### Catch Specific Errors

```python
from imgif import (
    ImageToGifConverter,
    InvalidInputError,
    NoImagesFoundError,
    ImageLoadError,
    ConversionError,
)

converter = ImageToGifConverter()

try:
    converter.convert("./images", "output.gif")
except InvalidInputError as e:
    print(f"Invalid input: {e}")
    # Handle invalid input
except NoImagesFoundError as e:
    print(f"No images found: {e}")
    # Handle empty directory
except ImageLoadError as e:
    print(f"Failed to load image: {e}")
    # Handle corrupted images
except ConversionError as e:
    print(f"Conversion failed: {e}")
    # Handle conversion failure
```

### Production Error Handling

```python
import logging
from imgif import ImageToGifConverter, Img2GifError

logger = logging.getLogger(__name__)

def create_gif_safely(input_path, output_path):
    """Create GIF with comprehensive error handling."""
    try:
        converter = ImageToGifConverter()
        converter.convert(input_path, output_path)
        logger.info(f"Successfully created GIF: {output_path}")
        return True

    except InvalidInputError as e:
        logger.error(f"Invalid input path {input_path}: {e}")
        return False

    except NoImagesFoundError as e:
        logger.warning(f"No images found in {input_path}: {e}")
        return False

    except ImageLoadError as e:
        logger.error(f"Failed to load images from {input_path}: {e}")
        return False

    except ConversionError as e:
        logger.error(f"Failed to create GIF {output_path}: {e}")
        return False

    except Img2GifError as e:
        logger.error(f"Unexpected imgif error: {e}")
        return False

    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return False
```

### Retry Logic

```python
import time
from imgif import ImageToGifConverter, ConversionError

def create_gif_with_retry(input_path, output_path, max_retries=3):
    """Create GIF with retry logic for transient failures."""
    converter = ImageToGifConverter()

    for attempt in range(max_retries):
        try:
            converter.convert(input_path, output_path)
            return True
        except ConversionError as e:
            if attempt < max_retries - 1:
                print(f"Attempt {attempt + 1} failed, retrying...")
                time.sleep(1)
            else:
                print(f"Failed after {max_retries} attempts: {e}")
                return False
```

### Graceful Degradation

```python
from pathlib import Path
from imgif import ImageToGifConverter, ImageLoadError

def create_gif_skip_corrupted(input_dir, output_path):
    """Create GIF, skipping corrupted images."""
    from PIL import Image

    # Manually validate and load images
    valid_images = []
    input_path = Path(input_dir)

    for img_file in sorted(input_path.glob("*.png")):
        try:
            img = Image.open(img_file)
            valid_images.append(img)
        except Exception as e:
            print(f"Skipping corrupted image {img_file}: {e}")

    if not valid_images:
        raise NoImagesFoundError(f"No valid images in {input_dir}")

    # Create GIF from valid images
    # (Note: This is a simplified example)
    valid_images[0].save(
        output_path,
        save_all=True,
        append_images=valid_images[1:],
        duration=1000,
        loop=0
    )
```

## Exception Context

All exceptions include context about what failed:

```python
try:
    converter.convert("./images", "output.gif")
except InvalidInputError as e:
    print(f"Error: {e}")           # User-friendly message
    print(f"Type: {type(e).__name__}")  # Exception type
    print(f"Args: {e.args}")       # Exception arguments
```

## Best Practices

1. **Catch specific exceptions** - Handle different error types appropriately
2. **Log errors** - Use logging for production applications
3. **Provide user feedback** - Show clear error messages to users
4. **Validate early** - Check inputs before processing
5. **Graceful degradation** - Skip problematic items when possible
6. **Retry transient errors** - Implement retry logic for temporary failures

## See Also

- [ImageToGifConverter API](converter.md) - Methods that raise exceptions
- [GifConfig API](config.md) - Configuration validation
- [Basic Usage](../guide/basic-usage.md) - Error handling examples
- [Examples](../getting-started/examples.md) - Practical error handling patterns
