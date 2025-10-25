"""
💻 Command-line interface for img2gif

This module provides a user-friendly CLI for converting images to GIFs
using the click library for argument parsing and rich for beautiful output.
"""

from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.traceback import install

from .config import GifConfig
from .converter import ImageToGifConverter
from .exceptions import Img2GifError

# Install rich tracebacks for better error display 🎨
install(show_locals=True)

# Console for output
console = Console()


@click.command(name="img2gif")
@click.argument(
    "input_path",
    type=click.Path(exists=True, path_type=Path),
)
@click.argument(
    "output_path",
    type=click.Path(path_type=Path),
)
@click.option(
    "--duration",
    "-d",
    type=float,
    default=1.0,
    help="⏱️  Duration per frame in seconds",
    show_default=True,
)
@click.option(
    "--fps",
    "-f",
    type=float,
    default=None,
    help="🎬 Frames per second (alternative to --duration)",
)
@click.option(
    "--loop",
    "-l",
    type=int,
    default=0,
    help="🔁 Number of loops (0 = infinite)",
    show_default=True,
)
@click.option(
    "--quality",
    "-q",
    type=int,
    default=85,
    help="✨ Quality level (1-100)",
    show_default=True,
)
@click.option(
    "--optimize",
    "-o",
    is_flag=True,
    help="🗜️  Optimize GIF for smaller file size",
)
@click.option(
    "--width",
    "-w",
    type=int,
    default=None,
    help="📏 Target width in pixels",
)
@click.option(
    "--height",
    "-h",
    type=int,
    default=None,
    help="📏 Target height in pixels",
)
@click.option(
    "--no-aspect-ratio",
    is_flag=True,
    help="🔲 Don't maintain aspect ratio when resizing",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="📢 Verbose output",
)
def main(
    input_path: Path,
    output_path: Path,
    duration: float,
    fps: Optional[float],
    loop: int,
    quality: int,
    optimize: bool,
    width: Optional[int],
    height: Optional[int],
    no_aspect_ratio: bool,
    verbose: bool,
) -> None:
    """
    🎬 Convert a sequence of images into an animated GIF.

    INPUT_PATH: Directory containing images or path to a single image

    OUTPUT_PATH: Where to save the generated GIF file

    \b
    Examples:
        img2gif ./frames output.gif
        img2gif ./frames output.gif --fps 10
        img2gif ./frames output.gif --duration 0.5 --loop 3
        img2gif ./frames output.gif --width 800 --optimize
    """
    try:
        # Show welcome message 👋
        if verbose:
            console.print(
                Panel.fit(
                    "[bold blue]img2gif[/bold blue] - Image to GIF Converter 🎬",
                    border_style="blue",
                )
            )
            console.print(f"📂 Input:  {input_path}")
            console.print(f"💾 Output: {output_path}")
            console.print()

        # Create configuration 📋
        config = GifConfig(
            duration=duration,
            fps=fps,
            loop=loop,
            quality=quality,
            optimize=optimize,
            width=width,
            height=height,
            maintain_aspect_ratio=not no_aspect_ratio,
        )

        if verbose:
            _print_config(config)

        # Create converter and convert 🎨
        converter = ImageToGifConverter()

        # Use config-based conversion if any advanced options are set
        if width or height or optimize or fps:
            converter.convert_with_config(input_path, output_path, config)
        else:
            # Use simple conversion for basic usage
            converter.convert(input_path, output_path, duration=duration, loop=loop)

        # Success! 🎉
        if verbose:
            console.print()
            console.print(
                Panel.fit(
                    "[bold green]✅ GIF created successfully![/bold green]",
                    border_style="green",
                )
            )

    except Img2GifError as e:
        # Handle img2gif-specific errors
        console.print(f"\n[bold red]❌ Error:[/bold red] {str(e)}\n", style="red")
        raise click.Abort() from e

    except Exception as e:
        # Handle unexpected errors
        console.print(f"\n[bold red]💥 Unexpected error:[/bold red] {str(e)}\n", style="red")
        if verbose:
            console.print_exception()
        raise click.Abort() from e


def _print_config(config: GifConfig) -> None:
    """
    📋 Print configuration details in a nice format.

    Args:
        config: GifConfig to display
    """
    console.print("[bold]Configuration:[/bold]")

    if config.fps:
        console.print(f"  🎬 FPS: {config.fps}")
        console.print(f"  ⏱️  Frame duration: {config.get_duration():.3f}s")
    else:
        console.print(f"  ⏱️  Duration: {config.duration}s")

    console.print(f"  🔁 Loop: {config.loop if config.loop > 0 else 'infinite'}")
    console.print(f"  ✨ Quality: {config.quality}")

    if config.optimize:
        console.print("  🗜️  Optimization: enabled")

    if config.width or config.height:
        size_str = f"{config.width or 'auto'} x {config.height or 'auto'}"
        console.print(f"  📏 Target size: {size_str}")
        if config.maintain_aspect_ratio:
            console.print("  📐 Aspect ratio: maintained")

    console.print()


if __name__ == "__main__":
    main()
