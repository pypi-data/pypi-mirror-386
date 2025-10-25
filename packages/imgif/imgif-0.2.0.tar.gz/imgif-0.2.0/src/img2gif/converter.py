"""
🎬 Core image to GIF conversion functionality

This module provides the main ImageToGifConverter class which handles
the conversion of image sequences into animated GIF files.
"""

from pathlib import Path

from PIL import Image
from rich.console import Console

from .config import GifConfig
from .exceptions import (
    ConversionError,
    ImageLoadError,
    InvalidInputError,
    NoImagesFoundError,
)
from .types import Duration, PathLike

# Supported image formats 🖼️
SUPPORTED_FORMATS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff", ".webp"}


class ImageToGifConverter:
    """
    🎨 Converts sequences of images into animated GIF files.

    This class provides a simple interface for creating animated GIFs from
    a directory of images. It handles image loading, validation, and conversion
    with support for various configuration options.

    Example:
        >>> converter = ImageToGifConverter()
        >>> converter.convert("./images", "output.gif", duration=0.5)
        🎉 GIF created successfully!

    Attributes:
        console: Rich console instance for pretty output
    """

    def __init__(self) -> None:
        """Initialize the converter with a Rich console for output."""
        self.console = Console()

    def convert(
        self,
        input_path: PathLike,
        output_path: PathLike,
        duration: Duration = 1.0,
        loop: int = 0,
    ) -> None:
        """
        🎬 Convert a sequence of images into an animated GIF.

        Args:
            input_path: Path to directory containing images or a single image file
            output_path: Path where the GIF should be saved
            duration: Duration per frame in seconds (or list of durations per frame)
            loop: Number of times the GIF should loop (0 = infinite)

        Raises:
            InvalidInputError: If input path doesn't exist or is invalid
            NoImagesFoundError: If no valid images found in input directory
            ImageLoadError: If images cannot be loaded
            ConversionError: If GIF creation fails

        Example:
            >>> converter = ImageToGifConverter()
            >>> converter.convert("./frames", "animation.gif", duration=0.5, loop=0)
        """
        # Validate inputs 🔍
        input_path = Path(input_path)
        output_path = Path(output_path)

        if not input_path.exists():
            raise InvalidInputError(f"Input path does not exist: {input_path}")

        # Get list of image files 📁
        image_files = self._get_image_files(input_path)

        if not image_files:
            raise NoImagesFoundError(f"No valid images found in: {input_path}")

        # Load images 🖼️
        images = self._load_images(image_files)

        # Convert to GIF 🎞️
        self._create_gif(images, output_path, duration, loop)

        self.console.print(f"[green]✅ GIF created successfully:[/green] {output_path}")

    def convert_with_config(
        self,
        input_path: PathLike,
        output_path: PathLike,
        config: GifConfig,
    ) -> None:
        """
        🎬 Convert images to GIF using a configuration object.

        This method provides more fine-grained control over GIF generation
        through a GifConfig object, including resizing, quality, and optimization.

        Args:
            input_path: Path to directory containing images or a single image file
            output_path: Path where the GIF should be saved
            config: GifConfig object with conversion settings

        Raises:
            InvalidInputError: If input path doesn't exist or is invalid
            NoImagesFoundError: If no valid images found in input directory
            ImageLoadError: If images cannot be loaded
            ConversionError: If GIF creation fails

        Example:
            >>> from img2gif import ImageToGifConverter, GifConfig
            >>> converter = ImageToGifConverter()
            >>> config = GifConfig(fps=10, optimize=True, width=800)
            >>> converter.convert_with_config("./frames", "output.gif", config)
        """
        # Validate inputs 🔍
        input_path = Path(input_path)
        output_path = Path(output_path)

        if not input_path.exists():
            raise InvalidInputError(f"Input path does not exist: {input_path}")

        # Get list of image files 📁
        image_files = self._get_image_files(input_path)

        if not image_files:
            raise NoImagesFoundError(f"No valid images found in: {input_path}")

        # Load images 🖼️
        images = self._load_images(image_files)

        # Resize images if needed 📏
        if config.should_resize() and images:
            images = self._resize_images(images, config)

        # Convert to GIF with config 🎞️
        self._create_gif_with_config(images, output_path, config)

        self.console.print(f"[green]✅ GIF created successfully:[/green] {output_path}")

    def _get_image_files(self, input_path: Path) -> list[Path]:
        """
        📁 Get all valid image files from input path.

        Args:
            input_path: Directory or file path to scan for images

        Returns:
            Sorted list of image file paths

        Raises:
            InvalidInputError: If input is neither file nor directory
        """
        if input_path.is_file():
            # Single file - validate it's an image
            if input_path.suffix.lower() in SUPPORTED_FORMATS:
                return [input_path]
            raise InvalidInputError(f"File is not a supported image format: {input_path.suffix}")

        if input_path.is_dir():
            # Directory - find all images
            image_files = [
                f
                for f in input_path.iterdir()
                if f.is_file() and f.suffix.lower() in SUPPORTED_FORMATS
            ]
            # Sort to ensure consistent ordering 🔢
            return sorted(image_files)

        raise InvalidInputError(f"Input path is neither file nor directory: {input_path}")

    def _load_images(self, image_files: list[Path]) -> list[Image.Image]:
        """
        🖼️ Load all images from file paths.

        Args:
            image_files: List of paths to image files

        Returns:
            List of loaded PIL Image objects

        Raises:
            ImageLoadError: If any image fails to load
        """
        images = []

        for idx, image_file in enumerate(image_files):
            try:
                # Load image using PIL 📸
                image = Image.open(image_file)
                # Convert to RGB if needed (handles RGBA, grayscale, etc.)
                if image.mode not in ("RGB", "P"):
                    image = image.convert("RGB")
                images.append(image)
            except Exception as e:
                raise ImageLoadError(
                    f"Failed to load image {image_file} (#{idx + 1}): {str(e)}"
                ) from e

        return images

    def _create_gif(
        self,
        images: list[Image.Image],
        output_path: Path,
        duration: Duration,
        loop: int,
    ) -> None:
        """
        🎞️ Create GIF file from loaded images.

        Args:
            images: List of loaded PIL Image objects
            output_path: Where to save the GIF
            duration: Frame duration(s) in seconds
            loop: Loop count (0 = infinite)

        Raises:
            ConversionError: If GIF creation fails
        """
        try:
            # Ensure output directory exists 📂
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Convert duration to milliseconds (PIL expects integers)
            if isinstance(duration, (int, float)):
                duration_ms = int(duration * 1000)
            else:
                duration_ms = [int(d * 1000) for d in duration]

            # Create GIF using PIL ✨
            # save_all=True for animated GIF, append_images for remaining frames
            images[0].save(
                output_path,
                save_all=True,
                append_images=images[1:],
                duration=duration_ms,
                loop=loop,
                optimize=False,
            )

        except Exception as e:
            raise ConversionError(f"Failed to create GIF: {str(e)}") from e

    def _resize_images(self, images: list[Image.Image], config: GifConfig) -> list[Image.Image]:
        """
        📏 Resize images according to configuration.

        Args:
            images: List of loaded PIL Image objects
            config: Configuration with resize parameters

        Returns:
            List of resized PIL Image objects
        """
        if not images:
            return images

        # Get current dimensions from first image
        first_image = images[0]
        current_width, current_height = first_image.size

        # Calculate target size
        target_width, target_height = config.get_target_size(current_width, current_height)

        # Resize all images using PIL (high quality resizing)
        resized_images = []
        for img in images:
            # Resize with high-quality Lanczos filter
            resized = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
            resized_images.append(resized)

        return resized_images

    def _create_gif_with_config(
        self,
        images: list[Image.Image],
        output_path: Path,
        config: GifConfig,
    ) -> None:
        """
        🎞️ Create GIF file using configuration object.

        Args:
            images: List of loaded (and possibly resized) PIL Image objects
            output_path: Where to save the GIF
            config: Configuration with GIF generation parameters

        Raises:
            ConversionError: If GIF creation fails
        """
        try:
            # Ensure output directory exists 📂
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Get effective duration
            duration = config.get_duration()

            # Convert duration to milliseconds (PIL expects integers)
            if isinstance(duration, (int, float)):
                duration_ms = int(duration * 1000)
            else:
                duration_ms = [int(d * 1000) for d in duration]

            # Create GIF using PIL with config options ✨
            images[0].save(
                output_path,
                save_all=True,
                append_images=images[1:],
                duration=duration_ms,
                loop=config.loop,
                optimize=config.optimize,
            )

        except Exception as e:
            raise ConversionError(f"Failed to create GIF: {str(e)}") from e

    def get_supported_formats(self) -> set[str]:
        """
        📋 Get set of supported image formats.

        Returns:
            Set of supported file extensions (including the dot)

        Example:
            >>> converter = ImageToGifConverter()
            >>> formats = converter.get_supported_formats()
            >>> ".png" in formats
            True
        """
        return SUPPORTED_FORMATS.copy()
