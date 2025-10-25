"""
🚨 Custom exceptions for img2gif library

This module defines all custom exceptions used throughout the library,
providing clear and specific error messages for different failure scenarios.
"""


class Img2GifError(Exception):
    """Base exception for all img2gif errors."""

    pass


class InvalidInputError(Img2GifError):
    """Raised when input directory or files are invalid."""

    pass


class NoImagesFoundError(Img2GifError):
    """Raised when no valid images are found in the input directory."""

    pass


class ImageLoadError(Img2GifError):
    """Raised when an image file cannot be loaded or is corrupted."""

    pass


class ConversionError(Img2GifError):
    """Raised when the GIF conversion process fails."""

    pass


class InvalidConfigurationError(Img2GifError):
    """Raised when configuration parameters are invalid."""

    pass
