# ImageToGifConverter API

The `ImageToGifConverter` class is the main interface for converting image sequences into animated GIFs.

## Class Definition

```python
from imgif import ImageToGifConverter

class ImageToGifConverter:
    """Converts sequences of images into animated GIF files."""
```

**Module:** `imgif.converter`

**Source:** `src/img2gif/converter.py`

## Constructor

### `__init__()`

Initialize a new converter instance.

```python
def __init__(self) -> None
```

**Parameters:** None

**Example:**

```python
from imgif import ImageToGifConverter

converter = ImageToGifConverter()
```

The constructor creates a Rich console instance for pretty output formatting.

## Methods

### `convert()`

Convert a sequence of images into an animated GIF with basic options.

```python
def convert(
    self,
    input_path: PathLike,
    output_path: PathLike,
    duration: Duration = 1.0,
    loop: int = 0,
) -> None
```

**Parameters:**

- **`input_path`** (`PathLike`) - Path to directory containing images or a single image file
- **`output_path`** (`PathLike`) - Path where the GIF should be saved
- **`duration`** (`Duration`, default: `1.0`) - Duration per frame in seconds, or list of durations per frame
- **`loop`** (`int`, default: `0`) - Number of times the GIF should loop (0 = infinite)

**Returns:** `None`

**Raises:**

- `InvalidInputError` - If input path doesn't exist or is invalid
- `NoImagesFoundError` - If no valid images found in input directory
- `ImageLoadError` - If images cannot be loaded
- `ConversionError` - If GIF creation fails

**Examples:**

```python
# Basic conversion
converter = ImageToGifConverter()
converter.convert("./frames", "output.gif")

# Custom duration and loop
converter.convert(
    input_path="./images",
    output_path="./animation.gif",
    duration=0.5,
    loop=3
)

# Variable frame durations
converter.convert(
    input_path="./images",
    output_path="./variable.gif",
    duration=[1.0, 0.5, 0.5, 2.0]
)
```

**Notes:**

- Images are loaded in alphabetical order by filename
- All images are automatically converted to RGB mode
- Output directory is created automatically if it doesn't exist
- A success message is printed to console upon completion

### `convert_with_config()`

Convert images to GIF using a configuration object for advanced control.

```python
def convert_with_config(
    self,
    input_path: PathLike,
    output_path: PathLike,
    config: GifConfig,
) -> None
```

**Parameters:**

- **`input_path`** (`PathLike`) - Path to directory containing images or a single image file
- **`output_path`** (`PathLike`) - Path where the GIF should be saved
- **`config`** (`GifConfig`) - Configuration object with conversion settings

**Returns:** `None`

**Raises:**

- `InvalidInputError` - If input path doesn't exist or is invalid
- `NoImagesFoundError` - If no valid images found in input directory
- `ImageLoadError` - If images cannot be loaded
- `ConversionError` - If GIF creation fails

**Examples:**

```python
from imgif import ImageToGifConverter, GifConfig

# Basic config usage
config = GifConfig(fps=10, optimize=True)
converter = ImageToGifConverter()
converter.convert_with_config("./frames", "output.gif", config)

# Advanced configuration
config = GifConfig(
    fps=24,
    loop=0,
    width=800,
    height=600,
    maintain_aspect_ratio=True,
    optimize=True,
    quality=90
)
converter.convert_with_config("./images", "optimized.gif", config)
```

**Features:**

- Full control via `GifConfig` object
- Automatic image resizing based on config
- Optimization support
- Quality control
- Aspect ratio preservation

### `get_supported_formats()`

Get the set of supported image formats.

```python
def get_supported_formats(self) -> set[str]
```

**Parameters:** None

**Returns:** `set[str]` - Set of supported file extensions (including the dot)

**Example:**

```python
converter = ImageToGifConverter()
formats = converter.get_supported_formats()
print(formats)
# Output: {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.webp'}

# Check if a format is supported
if ".png" in formats:
    print("PNG is supported!")
```

**Supported Formats:**

- `.png` - Portable Network Graphics
- `.jpg`, `.jpeg` - JPEG
- `.bmp` - Bitmap
- `.gif` - Graphics Interchange Format
- `.tiff` - Tagged Image File Format
- `.webp` - WebP

## Type Aliases

### PathLike

Accepts both strings and Path objects:

```python
from pathlib import Path

converter = ImageToGifConverter()

# String path
converter.convert("./images", "output.gif")

# Path object
input_path = Path("./images")
output_path = Path("./output.gif")
converter.convert(input_path, output_path)
```

### Duration

Can be a single value or a list:

```python
# Single duration (all frames)
duration: float = 0.5

# Multiple durations (per frame)
duration: list[float] = [1.0, 0.5, 0.5, 2.0]
```

## Attributes

### `console`

Rich console instance for formatted output.

```python
from rich.console import Console

converter = ImageToGifConverter()
print(type(converter.console))  # <class 'rich.console.Console'>
```

This attribute is used internally for pretty printing messages.

## Internal Methods

These methods are implementation details and not intended for public use:

### `_get_image_files()`

Scans input path for valid image files.

```python
def _get_image_files(self, input_path: Path) -> list[Path]
```

**Behavior:**

- If `input_path` is a file: validates it's a supported format
- If `input_path` is a directory: finds all supported images
- Returns sorted list of paths (alphabetical order)

### `_load_images()`

Loads images from file paths into PIL Image objects.

```python
def _load_images(self, image_files: list[Path]) -> list[Image.Image]
```

**Behavior:**

- Opens each image using PIL
- Converts to RGB mode if needed (handles RGBA, grayscale, etc.)
- Raises `ImageLoadError` if any image fails to load

### `_create_gif()`

Creates GIF from loaded images using basic parameters.

```python
def _create_gif(
    self,
    images: list[Image.Image],
    output_path: Path,
    duration: Duration,
    loop: int,
) -> None
```

**Behavior:**

- Converts duration from seconds to milliseconds
- Creates output directory if needed
- Saves GIF using PIL with specified parameters

### `_resize_images()`

Resizes images according to configuration.

```python
def _resize_images(
    self,
    images: list[Image.Image],
    config: GifConfig
) -> list[Image.Image]
```

**Behavior:**

- Calculates target size from config
- Resizes all images using high-quality Lanczos filter
- Maintains aspect ratio if configured

### `_create_gif_with_config()`

Creates GIF using configuration object.

```python
def _create_gif_with_config(
    self,
    images: list[Image.Image],
    output_path: Path,
    config: GifConfig,
) -> None
```

**Behavior:**

- Uses config parameters for GIF creation
- Supports optimization and quality settings
- Handles both single and variable frame durations

## Usage Patterns

### Simple Usage

For quick conversions with default settings:

```python
from imgif import ImageToGifConverter

converter = ImageToGifConverter()
converter.convert("./images", "output.gif")
```

### Reusing Converter

Reuse the same instance for multiple conversions:

```python
converter = ImageToGifConverter()

converter.convert("./project1/frames", "./project1/output.gif")
converter.convert("./project2/frames", "./project2/output.gif")
converter.convert("./project3/frames", "./project3/output.gif")
```

### Advanced Configuration

For fine-grained control:

```python
from imgif import ImageToGifConverter, GifConfig

config = GifConfig(
    fps=24,
    optimize=True,
    width=800,
    quality=90
)

converter = ImageToGifConverter()
converter.convert_with_config("./images", "output.gif", config)
```

### Error Handling

Handle exceptions gracefully:

```python
from imgif import ImageToGifConverter
from imgif import InvalidInputError, NoImagesFoundError, ConversionError

converter = ImageToGifConverter()

try:
    converter.convert("./images", "output.gif")
except InvalidInputError as e:
    print(f"Invalid input: {e}")
except NoImagesFoundError as e:
    print(f"No images found: {e}")
except ConversionError as e:
    print(f"Conversion failed: {e}")
```

### Format Detection

Check supported formats before processing:

```python
import os
from imgif import ImageToGifConverter

converter = ImageToGifConverter()
formats = converter.get_supported_formats()

# Filter files by supported formats
image_files = [
    f for f in os.listdir("./images")
    if os.path.splitext(f)[1].lower() in formats
]
print(f"Found {len(image_files)} supported images")
```

## Performance Considerations

### Memory Usage

- All images are loaded into memory at once
- For large image sets, consider the total memory requirement
- High-resolution images consume more memory

### Processing Speed

Factors affecting speed:

- **Number of images** - More images = longer processing time
- **Image resolution** - Higher resolution = slower processing
- **Optimization** - `optimize=True` increases processing time
- **Resizing** - Image resizing adds processing overhead

### Best Practices

1. **Resize before conversion** - Resize source images to target size beforehand
2. **Use appropriate FPS** - Balance smoothness vs. file size
3. **Enable optimization selectively** - Use for final output, not during development
4. **Reuse converter instance** - Avoid creating new instances unnecessarily

## Thread Safety

The `ImageToGifConverter` class is **not thread-safe**. Each thread should create its own instance:

```python
from concurrent.futures import ThreadPoolExecutor
from imgif import ImageToGifConverter

def convert_batch(input_dir, output_path):
    # Create converter instance per thread
    converter = ImageToGifConverter()
    converter.convert(input_dir, output_path)

with ThreadPoolExecutor(max_workers=4) as executor:
    executor.map(convert_batch, input_dirs, output_paths)
```

## See Also

- [GifConfig API](config.md) - Configuration options
- [Exceptions API](exceptions.md) - Exception reference
- [Basic Usage Guide](../guide/basic-usage.md) - Usage guide
- [Configuration Guide](../guide/configuration.md) - Configuration details
- [Examples](../getting-started/examples.md) - Practical examples
