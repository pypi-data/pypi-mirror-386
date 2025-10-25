"""
⚙️ Configuration classes for GIF generation

This module provides configuration options for customizing GIF generation,
including frame duration, quality, size, and optimization settings.
"""

from dataclasses import dataclass
from typing import Optional

from .exceptions import InvalidConfigurationError
from .types import Duration


@dataclass
class GifConfig:
    """
    🎛️ Configuration options for GIF generation.

    This class encapsulates all configuration parameters for creating GIFs,
    providing sensible defaults while allowing fine-grained control.

    Attributes:
        duration: Duration per frame in seconds (or list of durations per frame)
        loop: Number of times the GIF should loop (0 = infinite)
        fps: Frames per second (alternative to duration)
        quality: Quality level for optimization (1-100, higher is better)
        optimize: Whether to optimize the GIF for file size
        width: Target width in pixels (None = keep original)
        height: Target height in pixels (None = keep original)
        maintain_aspect_ratio: Whether to maintain aspect ratio when resizing

    Example:
        >>> config = GifConfig(duration=0.5, loop=0, optimize=True)
        >>> config.duration
        0.5
    """

    duration: Duration = 1.0
    loop: int = 0
    fps: Optional[float] = None
    quality: int = 85
    optimize: bool = False
    width: Optional[int] = None
    height: Optional[int] = None
    maintain_aspect_ratio: bool = True

    def __post_init__(self) -> None:
        """
        ✅ Validate configuration parameters after initialization.

        Raises:
            InvalidConfigurationError: If any parameter is invalid
        """
        self._validate()

    def _validate(self) -> None:
        """
        🔍 Validate all configuration parameters.

        Raises:
            InvalidConfigurationError: If validation fails
        """
        # Validate loop count
        if self.loop < 0:
            raise InvalidConfigurationError(f"Loop count must be >= 0, got {self.loop}")

        # Validate duration
        if self.fps is None:
            # Using duration
            if isinstance(self.duration, (int, float)):
                if self.duration <= 0:
                    raise InvalidConfigurationError(f"Duration must be > 0, got {self.duration}")
            elif isinstance(self.duration, list):
                if not self.duration:
                    raise InvalidConfigurationError("Duration list cannot be empty")
                if any(d <= 0 for d in self.duration):
                    raise InvalidConfigurationError("All duration values must be > 0")
            else:
                raise InvalidConfigurationError(
                    f"Duration must be float or list of floats, got {type(self.duration)}"
                )

        # Validate FPS (if provided)
        if self.fps is not None:
            if self.fps <= 0:
                raise InvalidConfigurationError(f"FPS must be > 0, got {self.fps}")

        # Validate quality
        if not 1 <= self.quality <= 100:
            raise InvalidConfigurationError(
                f"Quality must be between 1 and 100, got {self.quality}"
            )

        # Validate dimensions
        if self.width is not None and self.width <= 0:
            raise InvalidConfigurationError(f"Width must be > 0, got {self.width}")

        if self.height is not None and self.height <= 0:
            raise InvalidConfigurationError(f"Height must be > 0, got {self.height}")

    def get_duration(self) -> Duration:
        """
        ⏱️ Get the effective duration (calculated from FPS if needed).

        Returns:
            Duration value(s) in seconds

        Example:
            >>> config = GifConfig(fps=10)
            >>> config.get_duration()
            0.1
        """
        if self.fps is not None:
            # Calculate duration from FPS
            return 1.0 / self.fps
        return self.duration

    def should_resize(self) -> bool:
        """
        📏 Check if images should be resized based on configuration.

        Returns:
            True if width or height is specified, False otherwise

        Example:
            >>> config = GifConfig(width=800)
            >>> config.should_resize()
            True
        """
        return self.width is not None or self.height is not None

    def get_target_size(self, current_width: int, current_height: int) -> tuple[int, int]:
        """
        📐 Calculate target size for resizing, maintaining aspect ratio if requested.

        Args:
            current_width: Current image width in pixels
            current_height: Current image height in pixels

        Returns:
            Tuple of (target_width, target_height)

        Example:
            >>> config = GifConfig(width=800, maintain_aspect_ratio=True)
            >>> config.get_target_size(1600, 1200)
            (800, 600)
        """
        if not self.should_resize():
            return current_width, current_height

        # If both dimensions specified, use them (possibly ignoring aspect ratio)
        if self.width is not None and self.height is not None:
            if not self.maintain_aspect_ratio:
                return self.width, self.height

            # Maintain aspect ratio - use the dimension that results in smaller scaling
            width_ratio = self.width / current_width
            height_ratio = self.height / current_height
            ratio = min(width_ratio, height_ratio)

            return int(current_width * ratio), int(current_height * ratio)

        # Only width specified
        if self.width is not None:
            if self.maintain_aspect_ratio:
                ratio = self.width / current_width
                return self.width, int(current_height * ratio)
            return self.width, current_height

        # Only height specified
        if self.height is not None:
            if self.maintain_aspect_ratio:
                ratio = self.height / current_height
                return int(current_width * ratio), self.height
            return current_width, self.height

        return current_width, current_height

    def to_dict(self) -> dict[str, object]:
        """
        📋 Convert configuration to dictionary format.

        Returns:
            Dictionary representation of the configuration

        Example:
            >>> config = GifConfig(duration=0.5, loop=0)
            >>> config.to_dict()
            {'duration': 0.5, 'loop': 0, 'fps': None, ...}
        """
        return {
            "duration": self.duration,
            "loop": self.loop,
            "fps": self.fps,
            "quality": self.quality,
            "optimize": self.optimize,
            "width": self.width,
            "height": self.height,
            "maintain_aspect_ratio": self.maintain_aspect_ratio,
        }


def create_config(**kwargs: object) -> GifConfig:
    """
    🏭 Factory function to create a GifConfig with custom parameters.

    Args:
        **kwargs: Configuration parameters to override defaults

    Returns:
        Configured GifConfig instance

    Raises:
        InvalidConfigurationError: If any parameter is invalid

    Example:
        >>> config = create_config(duration=0.5, optimize=True)
        >>> config.optimize
        True
    """
    return GifConfig(**kwargs)  # type: ignore
