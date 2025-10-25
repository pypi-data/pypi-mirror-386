# 🚀 Quick Start

Get up and running with imgif in 5 minutes!

## Basic Usage

### 1. Import the Library

```python
from imgif import ImageToGifConverter
```

### 2. Create a Converter

```python
converter = ImageToGifConverter()
```

### 3. Convert Images to GIF

```python
converter.convert(
    input_path="./my_images",  # Directory with images
    output_path="./output.gif",  # Where to save GIF
    duration=0.5,  # Seconds per frame
)
```

That's it! 🎉

## Command Line Usage

You can also use imgif from the command line:

```bash
# Basic conversion
imgif ./my_images output.gif

# With custom duration
imgif ./my_images output.gif --duration 0.5

# With loop count
imgif ./my_images output.gif --loop 3
```

## Advanced Configuration

For more control, use `GifConfig`:

```python
from imgif import ImageToGifConverter, GifConfig

# Create configuration
config = GifConfig(
    fps=10,  # Frames per second
    loop=0,  # Loop forever
    width=800,  # Resize to 800px wide
    optimize=True,  # Optimize file size
)

# Convert with config
converter = ImageToGifConverter()
converter.convert_with_config("./images", "output.gif", config)
```

## Common Patterns

### Fixed Duration Per Frame

```python
converter.convert(
    input_path="./frames",
    output_path="animation.gif",
    duration=0.5,  # All frames: 0.5 seconds
)
```

### Variable Duration Per Frame

```python
converter.convert(
    input_path="./frames",
    output_path="animation.gif",
    duration=[0.5, 1.0, 0.5, 2.0],  # Different for each frame
)
```

### Using FPS Instead of Duration

```python
config = GifConfig(fps=24)  # 24 frames per second
converter.convert_with_config("./frames", "output.gif", config)
```

### Resize Images

```python
config = GifConfig(
    width=800,  # Target width
    maintain_aspect_ratio=True,  # Keep proportions
)
converter.convert_with_config("./frames", "output.gif", config)
```

## Error Handling

imgif provides clear error messages:

```python
from imgif import ImageToGifConverter, InvalidInputError

converter = ImageToGifConverter()

try:
    converter.convert("./nonexistent", "output.gif")
except InvalidInputError as e:
    print(f"Error: {e}")
```

## What's Next?

- 🎨 [See more examples](examples.md)
- 📚 [Read the full guide](../guide/basic-usage.md)
- 💻 [CLI reference](../guide/cli.md)
- ⚙️ [Configuration options](../guide/configuration.md)
