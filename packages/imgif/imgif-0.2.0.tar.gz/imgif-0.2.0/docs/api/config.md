# GifConfig API

The `GifConfig` class provides configuration options for customizing GIF generation.

## Class Definition

```python
from imgif import GifConfig

@dataclass
class GifConfig:
    """Configuration options for GIF generation."""
```

**Module:** `imgif.config`

**Source:** `src/img2gif/config.py`

**Type:** `dataclass`

## Constructor

### `GifConfig()`

Create a new configuration instance with specified parameters.

```python
def __init__(
    self,
    duration: Duration = 1.0,
    loop: int = 0,
    fps: Optional[float] = None,
    quality: int = 85,
    optimize: bool = False,
    width: Optional[int] = None,
    height: Optional[int] = None,
    maintain_aspect_ratio: bool = True,
)
```

**Parameters:**

- **`duration`** (`float | list[float]`, default: `1.0`) - Duration per frame in seconds (or list of durations)
- **`loop`** (`int`, default: `0`) - Number of times the GIF should loop (0 = infinite)
- **`fps`** (`float | None`, default: `None`) - Frames per second (alternative to duration)
- **`quality`** (`int`, default: `85`) - Quality level for optimization (1-100)
- **`optimize`** (`bool`, default: `False`) - Whether to optimize the GIF for file size
- **`width`** (`int | None`, default: `None`) - Target width in pixels (None = keep original)
- **`height`** (`int | None`, default: `None`) - Target height in pixels (None = keep original)
- **`maintain_aspect_ratio`** (`bool`, default: `True`) - Whether to maintain aspect ratio when resizing

**Raises:**

- `InvalidConfigurationError` - If any parameter is invalid

**Examples:**

```python
from imgif import GifConfig

# Default configuration
config = GifConfig()

# Custom configuration
config = GifConfig(
    fps=10,
    loop=0,
    optimize=True,
    width=800
)

# High-quality configuration
config = GifConfig(
    fps=30,
    quality=95,
    width=1920,
    optimize=False
)
```

## Attributes

### `duration`

**Type:** `float | list[float]`
**Default:** `1.0`

Duration per frame in seconds.

```python
# Single duration (all frames)
config = GifConfig(duration=0.5)

# Variable duration (per frame)
config = GifConfig(duration=[1.0, 0.5, 0.5, 2.0])
```

**Validation:**

- Must be greater than 0
- If a list, all values must be greater than 0
- Ignored if `fps` is set

### `loop`

**Type:** `int`
**Default:** `0`

Number of times the GIF should loop.

```python
config = GifConfig(loop=0)   # Infinite
config = GifConfig(loop=1)   # Play once
config = GifConfig(loop=3)   # Loop 3 times
```

**Validation:**

- Must be >= 0

**Values:**

- `0` - Infinite loop
- `1` - Play once
- `n` - Loop n times

### `fps`

**Type:** `float | None`
**Default:** `None`

Frames per second (alternative to `duration`).

```python
config = GifConfig(fps=10)   # 10 FPS (0.1s per frame)
config = GifConfig(fps=24)   # 24 FPS (smooth)
config = GifConfig(fps=None) # Use duration instead
```

**Validation:**

- Must be greater than 0 if set
- Takes precedence over `duration`

**Relationship to duration:**

```python
duration = 1.0 / fps
```

### `quality`

**Type:** `int`
**Default:** `85`
**Range:** `1-100`

Quality level for optimization (higher = better quality).

```python
config = GifConfig(quality=60)   # Lower quality, smaller file
config = GifConfig(quality=85)   # Balanced (default)
config = GifConfig(quality=95)   # High quality, larger file
```

**Validation:**

- Must be between 1 and 100 (inclusive)

### `optimize`

**Type:** `bool`
**Default:** `False`

Whether to optimize the GIF for smaller file size.

```python
config = GifConfig(optimize=True)   # Enable optimization
config = GifConfig(optimize=False)  # Disable (default)
```

**Effects:**

- `True` - Optimizes palette, removes duplicate data (slower, smaller files)
- `False` - No optimization (faster, larger files)

### `width`

**Type:** `int | None`
**Default:** `None`

Target width in pixels.

```python
config = GifConfig(width=800)   # Resize to 800px wide
config = GifConfig(width=None)  # Keep original width
```

**Validation:**

- Must be greater than 0 if set

### `height`

**Type:** `int | None`
**Default:** `None`

Target height in pixels.

```python
config = GifConfig(height=600)  # Resize to 600px tall
config = GifConfig(height=None) # Keep original height
```

**Validation:**

- Must be greater than 0 if set

### `maintain_aspect_ratio`

**Type:** `bool`
**Default:** `True`

Whether to maintain aspect ratio when resizing.

```python
config = GifConfig(
    width=800,
    maintain_aspect_ratio=True  # Height calculated automatically
)

config = GifConfig(
    width=800,
    height=600,
    maintain_aspect_ratio=False  # Force exact size
)
```

## Methods

### `get_duration()`

Get the effective duration (calculated from FPS if needed).

```python
def get_duration(self) -> Duration
```

**Returns:** `float | list[float]` - Duration value(s) in seconds

**Examples:**

```python
# Using FPS
config = GifConfig(fps=10)
duration = config.get_duration()  # 0.1

# Using duration directly
config = GifConfig(duration=0.5)
duration = config.get_duration()  # 0.5

# Variable duration
config = GifConfig(duration=[1.0, 0.5])
duration = config.get_duration()  # [1.0, 0.5]
```

**Behavior:**

- If `fps` is set: returns `1.0 / fps`
- Otherwise: returns `duration` as-is

### `should_resize()`

Check if images should be resized based on configuration.

```python
def should_resize(self) -> bool
```

**Returns:** `bool` - True if width or height is specified, False otherwise

**Examples:**

```python
config = GifConfig(width=800)
config.should_resize()  # True

config = GifConfig(height=600)
config.should_resize()  # True

config = GifConfig()
config.should_resize()  # False
```

### `get_target_size()`

Calculate target size for resizing, maintaining aspect ratio if requested.

```python
def get_target_size(
    self,
    current_width: int,
    current_height: int
) -> tuple[int, int]
```

**Parameters:**

- **`current_width`** (`int`) - Current image width in pixels
- **`current_height`** (`int`) - Current image height in pixels

**Returns:** `tuple[int, int]` - (target_width, target_height)

**Examples:**

```python
config = GifConfig(width=800, maintain_aspect_ratio=True)
target = config.get_target_size(1600, 1200)
# Returns: (800, 600) - maintains 4:3 aspect ratio

config = GifConfig(width=800, height=600, maintain_aspect_ratio=False)
target = config.get_target_size(1600, 1200)
# Returns: (800, 600) - exact size, may distort

config = GifConfig()
target = config.get_target_size(1600, 1200)
# Returns: (1600, 1200) - no resize
```

**Behavior:**

- **No dimensions set**: Returns original size
- **Width only** (maintain ratio): Calculates height proportionally
- **Height only** (maintain ratio): Calculates width proportionally
- **Both dimensions** (maintain ratio): Uses smaller ratio to fit within bounds
- **Both dimensions** (ignore ratio): Returns exact dimensions

### `to_dict()`

Convert configuration to dictionary format.

```python
def to_dict(self) -> dict[str, object]
```

**Returns:** `dict[str, object]` - Dictionary representation

**Example:**

```python
config = GifConfig(fps=10, optimize=True)
config_dict = config.to_dict()

# Result:
# {
#     'duration': 1.0,
#     'loop': 0,
#     'fps': 10,
#     'quality': 85,
#     'optimize': True,
#     'width': None,
#     'height': None,
#     'maintain_aspect_ratio': True
# }
```

## Factory Function

### `create_config()`

Factory function to create a GifConfig with custom parameters.

```python
def create_config(**kwargs: object) -> GifConfig
```

**Module:** `imgif.config`

**Parameters:**

- **`**kwargs`** - Configuration parameters to override defaults

**Returns:** `GifConfig` - Configured instance

**Raises:**

- `InvalidConfigurationError` - If any parameter is invalid

**Examples:**

```python
from imgif import create_config

# Equivalent to GifConfig(fps=10, optimize=True)
config = create_config(fps=10, optimize=True)

# Programmatic configuration
def get_config(preset):
    presets = {
        "web": {"fps": 10, "optimize": True, "width": 800},
        "hq": {"fps": 30, "quality": 95},
    }
    return create_config(**presets[preset])

config = get_config("web")
```

## Validation

All parameters are validated in `__post_init__()`:

### Validation Rules

- **`loop`**: Must be >= 0
- **`duration`**: Must be > 0 (or all values > 0 if list)
- **`fps`**: Must be > 0 if set
- **`quality`**: Must be between 1 and 100
- **`width`**: Must be > 0 if set
- **`height`**: Must be > 0 if set

### Validation Examples

```python
# These raise InvalidConfigurationError

GifConfig(loop=-1)           # ❌ Loop must be >= 0
GifConfig(duration=0)        # ❌ Duration must be > 0
GifConfig(duration=-0.5)     # ❌ Duration must be > 0
GifConfig(fps=0)             # ❌ FPS must be > 0
GifConfig(quality=0)         # ❌ Quality must be 1-100
GifConfig(quality=150)       # ❌ Quality must be 1-100
GifConfig(width=0)           # ❌ Width must be > 0
GifConfig(width=-100)        # ❌ Width must be > 0
```

## Type Aliases

### Duration

```python
Duration = float | list[float]
```

Can be either:

- **`float`** - Single duration for all frames
- **`list[float]`** - Different duration for each frame

## Configuration Presets

### Web-Optimized

```python
web_config = GifConfig(
    fps=10,
    optimize=True,
    width=800,
    maintain_aspect_ratio=True,
    loop=0
)
```

### High Quality

```python
hq_config = GifConfig(
    fps=30,
    quality=95,
    optimize=False,
    width=1920,
    maintain_aspect_ratio=True,
    loop=0
)
```

### Thumbnail

```python
thumb_config = GifConfig(
    fps=8,
    optimize=True,
    width=200,
    maintain_aspect_ratio=True,
    loop=0
)
```

### Social Media

```python
social_config = GifConfig(
    fps=15,
    optimize=True,
    width=640,
    maintain_aspect_ratio=True,
    loop=0
)
```

## Usage with Converter

### Basic Usage

```python
from imgif import ImageToGifConverter, GifConfig

config = GifConfig(fps=10, optimize=True)
converter = ImageToGifConverter()
converter.convert_with_config("./images", "output.gif", config)
```

### Configuration Reuse

```python
# Create once, use multiple times
config = GifConfig(fps=10, width=800, optimize=True)

converter = ImageToGifConverter()
converter.convert_with_config("./batch1", "out1.gif", config)
converter.convert_with_config("./batch2", "out2.gif", config)
converter.convert_with_config("./batch3", "out3.gif", config)
```

### Dynamic Configuration

```python
def create_optimized_gif(input_path, output_path, size):
    config = GifConfig(
        fps=10,
        optimize=True,
        width=size,
        maintain_aspect_ratio=True
    )
    converter = ImageToGifConverter()
    converter.convert_with_config(input_path, output_path, config)

create_optimized_gif("./images", "small.gif", 400)
create_optimized_gif("./images", "large.gif", 1200)
```

## Aspect Ratio Calculations

### Width Only

```python
config = GifConfig(width=800, maintain_aspect_ratio=True)
# Original: 1600x1200 (4:3)
# Result:   800x600   (4:3 preserved)
```

### Height Only

```python
config = GifConfig(height=600, maintain_aspect_ratio=True)
# Original: 1600x1200 (4:3)
# Result:   800x600   (4:3 preserved)
```

### Both Dimensions (Maintain)

```python
config = GifConfig(width=800, height=800, maintain_aspect_ratio=True)
# Original: 1600x1200 (4:3)
# Result:   800x600   (fits within 800x800, maintains 4:3)
```

### Both Dimensions (Force)

```python
config = GifConfig(width=800, height=800, maintain_aspect_ratio=False)
# Original: 1600x1200 (4:3)
# Result:   800x800   (forced to square, distorted)
```

## See Also

- [ImageToGifConverter API](converter.md) - Main converter class
- [Exceptions API](exceptions.md) - Exception reference
- [Configuration Guide](../guide/configuration.md) - Detailed configuration guide
- [Basic Usage](../guide/basic-usage.md) - Usage patterns
- [Examples](../getting-started/examples.md) - Practical examples
