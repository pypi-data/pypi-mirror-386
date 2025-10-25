# Basic Usage

This guide covers the fundamental concepts and basic usage patterns of imgif.

## Core Concepts

### The ImageToGifConverter

The `ImageToGifConverter` class is the main entry point for creating animated GIFs. It provides two primary methods:

- `convert()` - Simple conversion with basic options
- `convert_with_config()` - Advanced conversion with full configuration control

### Simple Conversion

The simplest way to create a GIF:

```python
from imgif import ImageToGifConverter

converter = ImageToGifConverter()
converter.convert(
    input_path="./images",
    output_path="./output.gif",
    duration=0.5,
    loop=0
)
```

**Parameters:**

- `input_path`: Path to a directory containing images or a single image file
- `output_path`: Where to save the generated GIF
- `duration`: How long each frame displays (in seconds)
- `loop`: How many times to loop (0 = infinite)

### Advanced Conversion

For more control, use `convert_with_config()` with a `GifConfig` object:

```python
from imgif import ImageToGifConverter, GifConfig

config = GifConfig(
    fps=10,
    loop=0,
    width=800,
    optimize=True
)

converter = ImageToGifConverter()
converter.convert_with_config(
    input_path="./images",
    output_path="./output.gif",
    config=config
)
```

## Input Formats

### Supported Image Formats

imgif supports the following image formats:

- PNG (`.png`)
- JPEG (`.jpg`, `.jpeg`)
- BMP (`.bmp`)
- GIF (`.gif`)
- TIFF (`.tiff`)
- WebP (`.webp`)

You can check supported formats programmatically:

```python
converter = ImageToGifConverter()
formats = converter.get_supported_formats()
print(formats)  # {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.webp'}
```

### Directory Input

When you provide a directory path, imgif will:

1. Find all supported image files in the directory
2. Sort them alphabetically by filename
3. Convert them into frames in that order

```python
# Directory structure:
# ./frames/
#   ├── frame_001.png
#   ├── frame_002.png
#   └── frame_003.png

converter.convert("./frames", "output.gif", duration=0.5)
```

!!! tip "File Naming"
    Use numbered filenames (e.g., `frame_001.png`, `frame_002.png`) to ensure frames appear in the correct order.

### Single File Input

You can also provide a single image file:

```python
converter.convert("./image.png", "output.gif", duration=1.0)
```

This creates a single-frame GIF (useful for format conversion).

## Frame Duration

### Fixed Duration

Set the same duration for all frames:

```python
converter.convert(
    input_path="./images",
    output_path="./output.gif",
    duration=0.5  # 500ms per frame
)
```

### Variable Duration

Set different durations for each frame:

```python
converter.convert(
    input_path="./images",
    output_path="./output.gif",
    duration=[1.0, 0.5, 0.5, 2.0]  # custom timing per frame
)
```

!!! warning "Duration List Length"
    If you provide a list, it should match the number of frames. If it's shorter, the behavior depends on Pillow's handling.

### Using FPS

Instead of duration, you can specify frames per second:

```python
config = GifConfig(fps=10)  # 10 frames per second
converter.convert_with_config("./images", "output.gif", config)
```

Duration and FPS are related: `duration = 1.0 / fps`

## Looping Behavior

Control how many times the GIF loops:

```python
# Infinite loop (most common)
converter.convert("./images", "output.gif", duration=0.5, loop=0)

# Play once
converter.convert("./images", "output.gif", duration=0.5, loop=1)

# Loop 3 times
converter.convert("./images", "output.gif", duration=0.5, loop=3)
```

## Image Processing

### Automatic Color Conversion

imgif automatically handles different image color modes:

- RGBA images are converted to RGB
- Grayscale images are converted to RGB
- Palette-based images are preserved when possible

```python
# These all work seamlessly
converter.convert("./rgba_images", "output.gif")     # RGBA → RGB
converter.convert("./grayscale", "output.gif")       # Gray → RGB
converter.convert("./mixed_modes", "output.gif")     # Mixed → Normalized
```

### Image Order

Images are processed in alphabetical order by filename. To control the order:

```python
# Good naming (lexicographic order):
# frame_001.png
# frame_002.png
# frame_010.png

# Bad naming (wrong order):
# frame_1.png  → comes before
# frame_10.png → frame_2.png
# frame_2.png  → alphabetically!
```

## Output

### File Creation

The output GIF is created at the specified path. Parent directories are created automatically:

```python
# This works even if ./output/ doesn't exist
converter.convert("./images", "./output/animation.gif")
```

### Output Validation

After successful conversion, you'll see a success message:

```python
converter.convert("./images", "output.gif")
# Output: ✅ GIF created successfully: output.gif
```

## Error Handling

imgif provides specific exceptions for different error scenarios:

```python
from imgif import (
    ImageToGifConverter,
    InvalidInputError,
    NoImagesFoundError,
    ImageLoadError,
    ConversionError
)

converter = ImageToGifConverter()

try:
    converter.convert("./images", "output.gif")
except InvalidInputError:
    print("The input path doesn't exist or is invalid")
except NoImagesFoundError:
    print("No valid images found in the directory")
except ImageLoadError:
    print("One or more images couldn't be loaded")
except ConversionError:
    print("Failed to create the GIF")
```

See the [Exceptions API reference](../api/exceptions.md) for details on each exception type.

## Common Patterns

### Quick GIF Creation

For most use cases, the simple pattern is enough:

```python
from imgif import ImageToGifConverter

ImageToGifConverter().convert(
    "./screenshots",
    "./demo.gif",
    duration=0.5
)
```

### Reusing Converter

You can reuse the same converter instance:

```python
converter = ImageToGifConverter()

# Convert multiple sets of images
converter.convert("./set1", "./animation1.gif")
converter.convert("./set2", "./animation2.gif")
converter.convert("./set3", "./animation3.gif")
```

### Configuration Reuse

Create a configuration once and use it multiple times:

```python
from imgif import ImageToGifConverter, GifConfig

# Define once
web_config = GifConfig(
    fps=10,
    optimize=True,
    width=800
)

converter = ImageToGifConverter()

# Use for multiple conversions
converter.convert_with_config("./batch1", "./out1.gif", web_config)
converter.convert_with_config("./batch2", "./out2.gif", web_config)
```

## Best Practices

### File Organization

Organize your input images in a dedicated directory:

```
project/
├── frames/
│   ├── 001.png
│   ├── 002.png
│   └── 003.png
└── output/
    └── animation.gif
```

### Naming Convention

Use zero-padded numbers for proper ordering:

```python
# Good
frame_001.png, frame_002.png, ..., frame_100.png

# Bad
frame_1.png, frame_2.png, ..., frame_100.png  # 100 comes before 2!
```

### Performance Tips

1. **Optimize image size before conversion** - Resize images to target dimensions before creating GIFs
2. **Use appropriate FPS** - Higher FPS = larger file size
3. **Enable optimization** - Use `optimize=True` for web use
4. **Batch process** - Reuse the converter instance for multiple conversions

## Next Steps

- Explore [Configuration Options](configuration.md) for advanced settings
- See [Examples](../getting-started/examples.md) for real-world use cases
- Learn about the [CLI](cli.md) for command-line usage
- Read the [API Reference](../api/converter.md) for detailed documentation
