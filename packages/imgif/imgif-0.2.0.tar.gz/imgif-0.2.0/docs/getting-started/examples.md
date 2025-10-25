# Examples

Here are some practical examples demonstrating different use cases for imgif.

## Basic Animation

Create a simple animated GIF from a directory of images:

```python
from imgif import ImageToGifConverter

converter = ImageToGifConverter()
converter.convert(
    input_path="./screenshots",
    output_path="./demo.gif",
    duration=0.5,
    loop=0  # infinite loop
)
```

## Custom Frame Durations

Create a GIF with different duration for each frame:

```python
from imgif import ImageToGifConverter

converter = ImageToGifConverter()

# First frame shows for 1s, second for 0.5s, third for 2s, etc.
converter.convert(
    input_path="./frames",
    output_path="./custom_timing.gif",
    duration=[1.0, 0.5, 2.0, 0.5],
    loop=0
)
```

## Optimized GIF with Resizing

Create a smaller, optimized GIF perfect for web use:

```python
from imgif import ImageToGifConverter, GifConfig

# Configure for web optimization
config = GifConfig(
    fps=10,              # 10 frames per second
    loop=0,              # infinite loop
    width=800,           # resize to 800px width
    optimize=True,       # optimize file size
    maintain_aspect_ratio=True
)

converter = ImageToGifConverter()
converter.convert_with_config(
    input_path="./screenshots",
    output_path="./optimized.gif",
    config=config
)
```

## High-Quality Animation

Create a high-quality GIF for presentations:

```python
from imgif import GifConfig, ImageToGifConverter

config = GifConfig(
    fps=30,              # smooth 30 fps
    quality=95,          # high quality
    width=1920,          # Full HD width
    optimize=False       # prioritize quality over size
)

converter = ImageToGifConverter()
converter.convert_with_config(
    input_path="./presentation_frames",
    output_path="./presentation.gif",
    config=config
)
```

## Processing Single Images

You can also use imgif with a single image (useful for format conversion):

```python
from imgif import ImageToGifConverter

converter = ImageToGifConverter()
converter.convert(
    input_path="./image.png",
    output_path="./output.gif",
    duration=1.0
)
```

## Data Visualization Animation

Create an animation from matplotlib plots:

```python
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from imgif import ImageToGifConverter, GifConfig

# Create temporary directory for frames
frames_dir = Path("./temp_frames")
frames_dir.mkdir(exist_ok=True)

# Generate multiple plot frames
for i in range(20):
    x = np.linspace(0, 2 * np.pi, 100)
    y = np.sin(x + i * 0.1)

    plt.figure(figsize=(10, 6))
    plt.plot(x, y)
    plt.title(f"Sine Wave Animation - Frame {i+1}")
    plt.ylim(-1.5, 1.5)
    plt.savefig(frames_dir / f"frame_{i:03d}.png", dpi=100)
    plt.close()

# Convert to GIF
config = GifConfig(fps=10, optimize=True, width=800)
converter = ImageToGifConverter()
converter.convert_with_config(
    input_path=frames_dir,
    output_path="./sine_wave.gif",
    config=config
)

# Cleanup temporary frames
import shutil
shutil.rmtree(frames_dir)

print("Animation created successfully!")
```

## Game Asset Animation

Create game sprite animations:

```python
from imgif import ImageToGifConverter, GifConfig

# Create a looping sprite animation
config = GifConfig(
    fps=12,              # sprite animation speed
    loop=0,              # loop forever
    width=256,           # sprite size
    height=256,
    maintain_aspect_ratio=False  # exact size needed
)

converter = ImageToGifConverter()
converter.convert_with_config(
    input_path="./sprite_frames",
    output_path="./character_walk.gif",
    config=config
)
```

## Loading Animation

Create a loading spinner animation that plays once:

```python
from imgif import ImageToGifConverter, GifConfig

config = GifConfig(
    fps=24,              # smooth animation
    loop=1,              # play once
    width=100,
    height=100,
    optimize=True
)

converter = ImageToGifConverter()
converter.convert_with_config(
    input_path="./spinner_frames",
    output_path="./loading.gif",
    config=config
)
```

## Tutorial Animation

Create a tutorial GIF with different timing for each step:

```python
from imgif import ImageToGifConverter

converter = ImageToGifConverter()

# Show each tutorial step for different durations
# First step: 2 seconds, other steps: 1 second each
converter.convert(
    input_path="./tutorial_screenshots",
    output_path="./tutorial.gif",
    duration=[2.0, 1.0, 1.0, 1.0, 2.0],  # pause on first and last
    loop=0
)
```

## Working with Different Image Formats

imgif supports various image formats:

```python
from imgif import ImageToGifConverter

converter = ImageToGifConverter()

# Check supported formats
formats = converter.get_supported_formats()
print(f"Supported formats: {formats}")
# Output: {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.webp'}

# Mix different image formats in one directory
converter.convert(
    input_path="./mixed_formats",  # contains .png, .jpg, .webp
    output_path="./combined.gif",
    duration=0.5
)
```

## Error Handling

Handle errors gracefully in production code:

```python
from imgif import ImageToGifConverter
from imgif import (
    InvalidInputError,
    NoImagesFoundError,
    ImageLoadError,
    ConversionError
)

converter = ImageToGifConverter()

try:
    converter.convert(
        input_path="./images",
        output_path="./output.gif",
        duration=0.5
    )
    print("Success!")

except InvalidInputError as e:
    print(f"Invalid input path: {e}")

except NoImagesFoundError as e:
    print(f"No images found: {e}")

except ImageLoadError as e:
    print(f"Failed to load image: {e}")

except ConversionError as e:
    print(f"Conversion failed: {e}")

except Exception as e:
    print(f"Unexpected error: {e}")
```

## Next Steps

- Learn more about [Basic Usage](../guide/basic-usage.md)
- Explore [Configuration Options](../guide/configuration.md)
- Check out the [CLI Reference](../guide/cli.md)
- Read the [API Reference](../api/converter.md)
