"""
🎨 Type definitions and protocols for img2gif library

This module contains type aliases, protocols, and type-related utilities
used throughout the library to ensure type safety and clear interfaces.
"""

from pathlib import Path
from typing import Protocol, Union

# Type aliases for clarity
PathLike = Union[str, Path]
"""Type alias for anything that can represent a file path."""

Duration = Union[float, list[float]]
"""Type alias for frame duration - can be single float or list of floats per frame."""


class ImageReader(Protocol):
    """Protocol for objects that can read image files."""

    def read(self, uri: PathLike) -> object:
        """
        Read an image from the given URI.

        Args:
            uri: Path to the image file

        Returns:
            Image data in array format
        """
        ...


class GifWriter(Protocol):
    """Protocol for objects that can write GIF files."""

    def write(self, uri: PathLike, data: object, **kwargs: object) -> None:
        """
        Write image data as a GIF file.

        Args:
            uri: Output path for the GIF file
            data: Image data to write
            **kwargs: Additional writer-specific options
        """
        ...
