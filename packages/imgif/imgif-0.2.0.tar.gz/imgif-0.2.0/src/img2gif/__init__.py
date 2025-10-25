"""
🎬 imgif - A playful Python library for converting image sequences into animated GIFs

This library provides a simple and intuitive API for creating animated GIFs from
sequences of images. It's designed to be easy to use while offering powerful
configuration options for advanced users.

Example:
    >>> from imgif import ImageToGifConverter
    >>> converter = ImageToGifConverter()
    >>> converter.convert("./images", "output.gif", duration=0.5)
"""

__version__ = "0.1.0"
__author__ = "Atick Faisal"
__license__ = "MIT"

# Public API exports 🎉
from .config import GifConfig, create_config
from .converter import ImageToGifConverter
from .exceptions import (
    ConversionError,
    ImageLoadError,
    Img2GifError,
    InvalidConfigurationError,
    InvalidInputError,
    NoImagesFoundError,
)

__all__ = [
    "__version__",
    # Core converter
    "ImageToGifConverter",
    # Configuration
    "GifConfig",
    "create_config",
    # Exceptions
    "Img2GifError",
    "InvalidInputError",
    "NoImagesFoundError",
    "ImageLoadError",
    "ConversionError",
    "InvalidConfigurationError",
]
