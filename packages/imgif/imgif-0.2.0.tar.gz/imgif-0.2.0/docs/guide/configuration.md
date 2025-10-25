# Configuration

This guide explains all configuration options available through the `GifConfig` class.

## Overview

The `GifConfig` class provides fine-grained control over GIF generation. It's used with the `convert_with_config()` method:

```python
from imgif import ImageToGifConverter, GifConfig

config = GifConfig(
    fps=10,
    loop=0,
    optimize=True,
    width=800
)

converter = ImageToGifConverter()
converter.convert_with_config("./images", "output.gif", config)
```

## Configuration Options

### Frame Timing

#### duration

**Type:** `float | list[float]`
**Default:** `1.0`

Duration per frame in seconds.

```python
# Fixed duration for all frames
config = GifConfig(duration=0.5)  # 500ms per frame

# Variable duration per frame
config = GifConfig(duration=[1.0, 0.5, 0.5, 2.0])
```

!!! note
    If `fps` is set, it takes precedence over `duration`.

#### fps

**Type:** `float | None`
**Default:** `None`

Frames per second (alternative to duration).

```python
config = GifConfig(fps=10)  # 10 frames per second (100ms per frame)
config = GifConfig(fps=24)  # 24 fps (smooth animation)
config = GifConfig(fps=5)   # 5 fps (slow animation)
```

The relationship between FPS and duration:

```
duration = 1.0 / fps
```

### Looping

#### loop

**Type:** `int`
**Default:** `0`

Number of times the GIF should loop.

```python
# Infinite loop (most common)
config = GifConfig(loop=0)

# Play once
config = GifConfig(loop=1)

# Loop 3 times
config = GifConfig(loop=3)
```

**Values:**

- `0` - Infinite loop (default)
- `1` - Play once
- `n` - Loop n times

### Quality & Optimization

#### quality

**Type:** `int`
**Default:** `85`
**Range:** `1-100`

Quality level for optimization (higher = better quality).

```python
# High quality (larger file size)
config = GifConfig(quality=95)

# Balanced quality
config = GifConfig(quality=85)  # default

# Lower quality (smaller file size)
config = GifConfig(quality=60)
```

!!! info
    This setting primarily affects the optimization process. Higher quality typically results in larger file sizes.

#### optimize

**Type:** `bool`
**Default:** `False`

Whether to optimize the GIF for smaller file size.

```python
# Enable optimization (recommended for web)
config = GifConfig(optimize=True)

# Disable optimization (faster processing)
config = GifConfig(optimize=False)  # default
```

**Effects:**

- `True` - Optimizes palette and removes duplicate pixel data (smaller files, slower processing)
- `False` - No optimization (larger files, faster processing)

### Sizing

#### width

**Type:** `int | None`
**Default:** `None`

Target width in pixels.

```python
# Resize to 800px wide
config = GifConfig(width=800)

# Keep original width
config = GifConfig(width=None)  # default
```

#### height

**Type:** `int | None`
**Default:** `None`

Target height in pixels.

```python
# Resize to 600px tall
config = GifConfig(height=600)

# Keep original height
config = GifConfig(height=None)  # default
```

#### maintain_aspect_ratio

**Type:** `bool`
**Default:** `True`

Whether to maintain aspect ratio when resizing.

```python
# Maintain aspect ratio (recommended)
config = GifConfig(
    width=800,
    maintain_aspect_ratio=True  # height calculated automatically
)

# Force exact dimensions (may distort)
config = GifConfig(
    width=800,
    height=600,
    maintain_aspect_ratio=False  # exact size, possible distortion
)
```

**Behavior with `maintain_aspect_ratio=True`:**

- If only `width` is set: height is calculated proportionally
- If only `height` is set: width is calculated proportionally
- If both are set: the smaller ratio is used to fit within bounds

## Configuration Patterns

### Web-Optimized GIF

Perfect for websites and social media:

```python
web_config = GifConfig(
    fps=10,                      # smooth but not excessive
    optimize=True,               # reduce file size
    width=800,                   # reasonable web size
    maintain_aspect_ratio=True,  # preserve proportions
    loop=0                       # loop forever
)
```

### High-Quality GIF

For presentations and high-quality displays:

```python
hq_config = GifConfig(
    fps=30,                      # very smooth
    quality=95,                  # high quality
    optimize=False,              # prioritize quality
    width=1920,                  # Full HD
    maintain_aspect_ratio=True,
    loop=0
)
```

### Social Media GIF

Optimized for Twitter, Instagram, etc.:

```python
social_config = GifConfig(
    fps=15,                      # balanced smoothness
    optimize=True,               # smaller upload
    width=640,                   # common social media size
    maintain_aspect_ratio=True,
    loop=0
)
```

### Thumbnail GIF

Small preview animations:

```python
thumb_config = GifConfig(
    fps=8,                       # lower fps for small size
    optimize=True,               # maximize compression
    width=200,                   # thumbnail size
    maintain_aspect_ratio=True,
    loop=0
)
```

### Game Sprite Animation

Precise sizing for game assets:

```python
sprite_config = GifConfig(
    fps=12,                      # sprite animation speed
    width=256,
    height=256,
    maintain_aspect_ratio=False, # exact size needed
    optimize=False,              # preserve quality
    loop=0
)
```

## Factory Function

You can also use the `create_config()` factory function:

```python
from imgif import create_config

# Equivalent to GifConfig(fps=10, optimize=True)
config = create_config(fps=10, optimize=True)
```

This is useful for programmatic configuration:

```python
from imgif import create_config

def make_gif_config(profile: str):
    profiles = {
        "web": {"fps": 10, "optimize": True, "width": 800},
        "hq": {"fps": 30, "quality": 95, "width": 1920},
        "thumb": {"fps": 8, "optimize": True, "width": 200},
    }
    return create_config(**profiles[profile])

config = make_gif_config("web")
```

## Configuration Validation

All configuration parameters are validated when the `GifConfig` is created:

```python
# This raises InvalidConfigurationError
config = GifConfig(fps=-1)  # ❌ FPS must be > 0

config = GifConfig(loop=-1)  # ❌ Loop must be >= 0

config = GifConfig(quality=150)  # ❌ Quality must be 1-100

config = GifConfig(width=0)  # ❌ Width must be > 0
```

## Utility Methods

### get_duration()

Get the effective duration (calculated from FPS if needed):

```python
config = GifConfig(fps=10)
duration = config.get_duration()  # 0.1 (seconds)

config = GifConfig(duration=0.5)
duration = config.get_duration()  # 0.5 (seconds)
```

### should_resize()

Check if resizing will occur:

```python
config = GifConfig(width=800)
config.should_resize()  # True

config = GifConfig()
config.should_resize()  # False
```

### get_target_size()

Calculate target dimensions:

```python
config = GifConfig(width=800, maintain_aspect_ratio=True)
target_width, target_height = config.get_target_size(1600, 1200)
# Returns: (800, 600) - maintains 4:3 aspect ratio
```

### to_dict()

Convert configuration to dictionary:

```python
config = GifConfig(fps=10, optimize=True)
config_dict = config.to_dict()
# {'duration': 1.0, 'fps': 10, 'optimize': True, ...}
```

## Aspect Ratio Behavior

Understanding how `maintain_aspect_ratio` works:

### Only Width Set

```python
config = GifConfig(width=800, maintain_aspect_ratio=True)

# Original: 1600x1200 (4:3)
# Result:   800x600   (4:3 preserved)
```

### Only Height Set

```python
config = GifConfig(height=600, maintain_aspect_ratio=True)

# Original: 1600x1200 (4:3)
# Result:   800x600   (4:3 preserved)
```

### Both Dimensions Set (Maintain Ratio)

```python
config = GifConfig(
    width=800,
    height=800,
    maintain_aspect_ratio=True
)

# Original: 1600x1200 (4:3)
# Result:   800x600   (fits within 800x800, maintains 4:3)
```

### Both Dimensions Set (Force Size)

```python
config = GifConfig(
    width=800,
    height=800,
    maintain_aspect_ratio=False
)

# Original: 1600x1200 (4:3)
# Result:   800x800   (forced to square, distorted)
```

## Performance Considerations

### File Size vs Quality

Configuration choices affect file size:

```python
# Smallest file size
GifConfig(
    fps=5,           # fewer frames
    optimize=True,   # compression
    width=400        # smaller dimensions
)

# Largest file size
GifConfig(
    fps=30,          # many frames
    optimize=False,  # no compression
    quality=100,     # max quality
    width=1920       # large dimensions
)
```

### Processing Speed

Some settings affect processing speed:

- `optimize=True` - Slower (compression takes time)
- `optimize=False` - Faster (no compression)
- Higher resolution - Slower (more pixels to process)
- Lower resolution - Faster (fewer pixels)

## Default Configuration

If you don't specify options, these defaults are used:

```python
GifConfig(
    duration=1.0,                # 1 second per frame
    loop=0,                      # infinite loop
    fps=None,                    # use duration instead
    quality=85,                  # balanced quality
    optimize=False,              # faster processing
    width=None,                  # original width
    height=None,                 # original height
    maintain_aspect_ratio=True   # preserve proportions
)
```

## Next Steps

- See [Examples](../getting-started/examples.md) for practical use cases
- Learn about [Basic Usage](basic-usage.md) for core concepts
- Check the [GifConfig API reference](../api/config.md) for technical details
- Explore the [CLI](cli.md) for command-line configuration
