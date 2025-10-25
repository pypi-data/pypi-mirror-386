# CLI Reference

imgif provides a command-line interface for converting images to GIFs without writing Python code.

## Installation

After installing imgif, the `imgif` command is available:

```bash
pip install imgif
imgif --help
```

## Basic Usage

The basic syntax is:

```bash
imgif INPUT_PATH OUTPUT_PATH [OPTIONS]
```

**Example:**

```bash
imgif ./screenshots demo.gif
```

## Arguments

### INPUT_PATH

**Required**

Path to either:

- A directory containing images
- A single image file

```bash
# Directory input
imgif ./my_frames output.gif

# Single file input
imgif ./image.png output.gif
```

The directory will be scanned for supported image formats (`.png`, `.jpg`, `.jpeg`, `.bmp`, `.gif`, `.tiff`, `.webp`).

### OUTPUT_PATH

**Required**

Path where the GIF will be saved.

```bash
imgif ./frames output.gif
imgif ./frames ./gifs/animation.gif  # creates ./gifs/ if needed
```

## Options

### Frame Timing

#### --duration, -d

Duration per frame in seconds.

**Default:** `1.0`

```bash
# 500ms per frame
imgif ./frames output.gif --duration 0.5

# 2 seconds per frame
imgif ./frames output.gif -d 2.0
```

#### --fps, -f

Frames per second (alternative to `--duration`).

**Default:** `None` (uses duration)

```bash
# 10 frames per second
imgif ./frames output.gif --fps 10

# 24 fps (smooth animation)
imgif ./frames output.gif -f 24
```

!!! note
    If both `--fps` and `--duration` are specified, `--fps` takes precedence.

### Looping

#### --loop, -l

Number of times to loop the GIF.

**Default:** `0` (infinite)

```bash
# Infinite loop (default)
imgif ./frames output.gif --loop 0

# Play once
imgif ./frames output.gif -l 1

# Loop 3 times
imgif ./frames output.gif --loop 3
```

### Quality & Optimization

#### --quality, -q

Quality level (1-100, higher = better).

**Default:** `85`

```bash
# High quality
imgif ./frames output.gif --quality 95

# Lower quality (smaller file)
imgif ./frames output.gif -q 60
```

#### --optimize, -o

Enable GIF optimization for smaller file size.

**Default:** `False` (disabled)

```bash
# Enable optimization
imgif ./frames output.gif --optimize

# Short form
imgif ./frames output.gif -o
```

!!! tip
    Use `--optimize` for web-destined GIFs to reduce file size.

### Sizing

#### --width, -w

Target width in pixels.

**Default:** `None` (original width)

```bash
# Resize to 800px wide
imgif ./frames output.gif --width 800

# Short form
imgif ./frames output.gif -w 1920
```

#### --height, -h

Target height in pixels.

**Default:** `None` (original height)

```bash
# Resize to 600px tall
imgif ./frames output.gif --height 600

# Note: -h is also used for help in some contexts
imgif ./frames output.gif --height 1080
```

!!! warning
    The `-h` flag is used for height, not help. Use `imgif --help` for help.

#### --no-aspect-ratio

Don't maintain aspect ratio when resizing.

**Default:** `False` (aspect ratio is maintained)

```bash
# Force exact dimensions (may distort)
imgif ./frames output.gif --width 800 --height 800 --no-aspect-ratio

# Maintain aspect ratio (default)
imgif ./frames output.gif --width 800
```

### Verbosity

#### --verbose, -v

Enable verbose output with detailed progress information.

**Default:** `False` (minimal output)

```bash
# Verbose mode
imgif ./frames output.gif --verbose

# Short form
imgif ./frames output.gif -v
```

Verbose mode shows:

- Welcome banner
- Input/output paths
- Configuration details
- Success message with border

## Common Examples

### Quick GIF

Create a GIF with default settings:

```bash
imgif ./screenshots demo.gif
```

### Web-Optimized GIF

Create an optimized GIF for websites:

```bash
imgif ./frames web.gif --fps 10 --optimize --width 800
```

### High-Quality GIF

Create a high-quality GIF for presentations:

```bash
imgif ./slides presentation.gif --fps 30 --quality 95 --width 1920
```

### Thumbnail GIF

Create a small thumbnail animation:

```bash
imgif ./preview thumb.gif --fps 8 --optimize --width 200
```

### Custom Timing

Control animation speed:

```bash
# Slow animation
imgif ./frames slow.gif --duration 2.0

# Fast animation
imgif ./frames fast.gif --fps 20
```

### One-Shot Animation

Play once without looping:

```bash
imgif ./intro intro.gif --loop 1 --fps 24
```

### Square Social Media GIF

Create a square GIF for Instagram:

```bash
imgif ./frames insta.gif \
  --width 640 \
  --height 640 \
  --no-aspect-ratio \
  --optimize \
  --fps 15
```

## Combining Options

You can combine multiple options:

```bash
imgif ./screenshots demo.gif \
  --fps 10 \
  --loop 0 \
  --optimize \
  --width 800 \
  --quality 85 \
  --verbose
```

## Help

Get help anytime with:

```bash
imgif --help
```

This displays:

```
Usage: imgif [OPTIONS] INPUT_PATH OUTPUT_PATH

  Convert a sequence of images into an animated GIF.

  INPUT_PATH: Directory containing images or path to a single image

  OUTPUT_PATH: Where to save the generated GIF file

Examples:
    imgif ./frames output.gif
    imgif ./frames output.gif --fps 10
    imgif ./frames output.gif --duration 0.5 --loop 3
    imgif ./frames output.gif --width 800 --optimize

Options:
  -d, --duration FLOAT       Duration per frame in seconds  [default: 1.0]
  -f, --fps FLOAT            Frames per second (alternative to --duration)
  -l, --loop INTEGER         Number of loops (0 = infinite)  [default: 0]
  -q, --quality INTEGER      Quality level (1-100)  [default: 85]
  -o, --optimize             Optimize GIF for smaller file size
  -w, --width INTEGER        Target width in pixels
  --height INTEGER           Target height in pixels
  --no-aspect-ratio          Don't maintain aspect ratio when resizing
  -v, --verbose              Verbose output
  --help                     Show this message and exit.
```

## Output Examples

### Default Output

```bash
$ imgif ./frames output.gif
✅ GIF created successfully: output.gif
```

### Verbose Output

```bash
$ imgif ./frames output.gif --verbose
╭─────────────────────────────────────────╮
│ img2gif - Image to GIF Converter        │
╰─────────────────────────────────────────╯
📂 Input:  ./frames
💾 Output: output.gif

Configuration:
  ⏱️  Duration: 1.0s
  🔁 Loop: infinite
  ✨ Quality: 85

✅ GIF created successfully: output.gif

╭─────────────────────────────────────────╮
│ ✅ GIF created successfully!            │
╰─────────────────────────────────────────╯
```

## Error Messages

imgif provides clear error messages:

```bash
# Invalid input path
$ imgif ./nonexistent output.gif
❌ Error: Input path does not exist: ./nonexistent

# No images found
$ imgif ./empty_directory output.gif
❌ Error: No valid images found in: ./empty_directory

# Invalid configuration
$ imgif ./frames output.gif --quality 150
❌ Error: Quality must be between 1 and 100, got 150
```

## Scripting & Automation

### Batch Processing

Process multiple directories:

```bash
#!/bin/bash
for dir in ./projects/*/frames; do
  output="${dir%/frames}/output.gif"
  imgif "$dir" "$output" --optimize --fps 10
done
```

### CI/CD Integration

Use in continuous integration:

```bash
# In your CI script
imgif ./test_frames ./artifacts/test.gif --verbose || exit 1
```

### Makefile Integration

```makefile
.PHONY: gifs
gifs:
    imgif ./screenshots demo.gif --optimize --width 800
    imgif ./tutorial tutorial.gif --fps 5 --width 640
```

## Python vs CLI

Choosing between Python API and CLI:

**Use CLI when:**

- Quick one-off conversions
- Shell scripting
- CI/CD pipelines
- Command-line workflows

**Use Python API when:**

- Complex programmatic control
- Integration with Python applications
- Custom processing workflows
- Variable frame durations

### CLI Example

```bash
imgif ./frames output.gif --fps 10 --optimize
```

### Equivalent Python Code

```python
from imgif import ImageToGifConverter, GifConfig

config = GifConfig(fps=10, optimize=True)
converter = ImageToGifConverter()
converter.convert_with_config("./frames", "output.gif", config)
```

## Environment Variables

Currently, imgif doesn't use environment variables. Configuration is done through command-line options only.

## Exit Codes

- `0` - Success
- `1` - Error (invalid input, conversion failure, etc.)

```bash
imgif ./frames output.gif
echo $?  # 0 on success, 1 on error
```

## Performance Tips

1. **Use optimization wisely** - `--optimize` reduces file size but slows processing
2. **Lower FPS for smaller files** - `--fps 10` vs `--fps 30`
3. **Resize for web** - `--width 800` reduces file size significantly
4. **Batch similar operations** - Process similar images together

## Next Steps

- Learn about [Configuration](configuration.md) for detailed option explanations
- See [Examples](../getting-started/examples.md) for use case ideas
- Check [Basic Usage](basic-usage.md) for Python API usage
- Read the [API Reference](../api/converter.md) for programmatic control
