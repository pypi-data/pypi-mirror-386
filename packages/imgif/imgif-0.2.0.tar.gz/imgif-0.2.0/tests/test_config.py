"""
🧪 Unit tests for the GifConfig class

This module tests the configuration system, including validation,
parameter handling, and helper methods.
"""

import pytest

from img2gif import GifConfig, create_config
from img2gif.exceptions import InvalidConfigurationError


class TestGifConfig:
    """Test suite for GifConfig class ⚙️"""

    def test_default_config(self) -> None:
        """✅ Test that default configuration works."""
        config = GifConfig()

        assert config.duration == 1.0
        assert config.loop == 0
        assert config.fps is None
        assert config.quality == 85
        assert config.optimize is False
        assert config.width is None
        assert config.height is None
        assert config.maintain_aspect_ratio is True

    def test_custom_duration(self) -> None:
        """✅ Test custom duration configuration."""
        config = GifConfig(duration=0.5)
        assert config.duration == 0.5

    def test_custom_duration_list(self) -> None:
        """✅ Test duration as list of values."""
        config = GifConfig(duration=[0.5, 1.0, 0.3])
        assert config.duration == [0.5, 1.0, 0.3]

    def test_custom_fps(self) -> None:
        """✅ Test FPS-based configuration."""
        config = GifConfig(fps=10)
        assert config.fps == 10

    def test_get_duration_from_fps(self) -> None:
        """✅ Test that duration is calculated from FPS."""
        config = GifConfig(fps=10)
        assert config.get_duration() == 0.1

    def test_get_duration_direct(self) -> None:
        """✅ Test that duration is returned directly when no FPS."""
        config = GifConfig(duration=0.5)
        assert config.get_duration() == 0.5

    def test_custom_loop(self) -> None:
        """✅ Test custom loop count."""
        config = GifConfig(loop=5)
        assert config.loop == 5

    def test_quality_setting(self) -> None:
        """✅ Test quality configuration."""
        config = GifConfig(quality=95)
        assert config.quality == 95

    def test_optimize_flag(self) -> None:
        """✅ Test optimize flag."""
        config = GifConfig(optimize=True)
        assert config.optimize is True

    def test_resize_width_only(self) -> None:
        """✅ Test resize with width only."""
        config = GifConfig(width=800)
        assert config.width == 800
        assert config.should_resize() is True

    def test_resize_height_only(self) -> None:
        """✅ Test resize with height only."""
        config = GifConfig(height=600)
        assert config.height == 600
        assert config.should_resize() is True

    def test_resize_both_dimensions(self) -> None:
        """✅ Test resize with both dimensions."""
        config = GifConfig(width=800, height=600)
        assert config.width == 800
        assert config.height == 600
        assert config.should_resize() is True

    def test_no_resize(self) -> None:
        """✅ Test that should_resize returns False when no dimensions set."""
        config = GifConfig()
        assert config.should_resize() is False

    def test_get_target_size_width_only_with_aspect_ratio(self) -> None:
        """✅ Test target size calculation with width only."""
        config = GifConfig(width=800, maintain_aspect_ratio=True)
        target_w, target_h = config.get_target_size(1600, 1200)

        assert target_w == 800
        assert target_h == 600  # Maintains 4:3 ratio

    def test_get_target_size_height_only_with_aspect_ratio(self) -> None:
        """✅ Test target size calculation with height only."""
        config = GifConfig(height=600, maintain_aspect_ratio=True)
        target_w, target_h = config.get_target_size(1600, 1200)

        assert target_w == 800  # Maintains 4:3 ratio
        assert target_h == 600

    def test_get_target_size_both_with_aspect_ratio(self) -> None:
        """✅ Test target size with both dimensions and aspect ratio."""
        config = GifConfig(width=1000, height=1000, maintain_aspect_ratio=True)
        target_w, target_h = config.get_target_size(1600, 1200)

        # Should scale to fit within 1000x1000 while maintaining ratio
        assert target_w == 1000
        assert target_h == 750  # Maintains 4:3 ratio

    def test_get_target_size_both_without_aspect_ratio(self) -> None:
        """✅ Test target size ignoring aspect ratio."""
        config = GifConfig(width=800, height=600, maintain_aspect_ratio=False)
        target_w, target_h = config.get_target_size(1600, 1200)

        assert target_w == 800
        assert target_h == 600

    def test_get_target_size_no_resize(self) -> None:
        """✅ Test that original size is returned when no resize."""
        config = GifConfig()
        target_w, target_h = config.get_target_size(1600, 1200)

        assert target_w == 1600
        assert target_h == 1200

    def test_to_dict(self) -> None:
        """✅ Test conversion to dictionary."""
        config = GifConfig(duration=0.5, loop=3, optimize=True)
        config_dict = config.to_dict()

        assert isinstance(config_dict, dict)
        assert config_dict["duration"] == 0.5
        assert config_dict["loop"] == 3
        assert config_dict["optimize"] is True

    def test_create_config_factory(self) -> None:
        """✅ Test create_config factory function."""
        config = create_config(duration=0.5, loop=3)

        assert isinstance(config, GifConfig)
        assert config.duration == 0.5
        assert config.loop == 3

    # Validation tests ❌

    def test_negative_loop_raises_error(self) -> None:
        """❌ Test that negative loop count raises error."""
        with pytest.raises(InvalidConfigurationError) as exc_info:
            GifConfig(loop=-1)

        assert "loop count" in str(exc_info.value).lower()

    def test_zero_duration_raises_error(self) -> None:
        """❌ Test that zero duration raises error."""
        with pytest.raises(InvalidConfigurationError) as exc_info:
            GifConfig(duration=0)

        assert "duration" in str(exc_info.value).lower()

    def test_negative_duration_raises_error(self) -> None:
        """❌ Test that negative duration raises error."""
        with pytest.raises(InvalidConfigurationError) as exc_info:
            GifConfig(duration=-0.5)

        assert "duration" in str(exc_info.value).lower()

    def test_empty_duration_list_raises_error(self) -> None:
        """❌ Test that empty duration list raises error."""
        with pytest.raises(InvalidConfigurationError) as exc_info:
            GifConfig(duration=[])

        assert "duration" in str(exc_info.value).lower()

    def test_invalid_duration_in_list_raises_error(self) -> None:
        """❌ Test that invalid value in duration list raises error."""
        with pytest.raises(InvalidConfigurationError) as exc_info:
            GifConfig(duration=[0.5, 0, 0.3])

        assert "duration" in str(exc_info.value).lower()

    def test_zero_fps_raises_error(self) -> None:
        """❌ Test that zero FPS raises error."""
        with pytest.raises(InvalidConfigurationError) as exc_info:
            GifConfig(fps=0)

        assert "fps" in str(exc_info.value).lower()

    def test_negative_fps_raises_error(self) -> None:
        """❌ Test that negative FPS raises error."""
        with pytest.raises(InvalidConfigurationError) as exc_info:
            GifConfig(fps=-10)

        assert "fps" in str(exc_info.value).lower()

    def test_quality_too_low_raises_error(self) -> None:
        """❌ Test that quality < 1 raises error."""
        with pytest.raises(InvalidConfigurationError) as exc_info:
            GifConfig(quality=0)

        assert "quality" in str(exc_info.value).lower()

    def test_quality_too_high_raises_error(self) -> None:
        """❌ Test that quality > 100 raises error."""
        with pytest.raises(InvalidConfigurationError) as exc_info:
            GifConfig(quality=101)

        assert "quality" in str(exc_info.value).lower()

    def test_negative_width_raises_error(self) -> None:
        """❌ Test that negative width raises error."""
        with pytest.raises(InvalidConfigurationError) as exc_info:
            GifConfig(width=-100)

        assert "width" in str(exc_info.value).lower()

    def test_zero_width_raises_error(self) -> None:
        """❌ Test that zero width raises error."""
        with pytest.raises(InvalidConfigurationError) as exc_info:
            GifConfig(width=0)

        assert "width" in str(exc_info.value).lower()

    def test_negative_height_raises_error(self) -> None:
        """❌ Test that negative height raises error."""
        with pytest.raises(InvalidConfigurationError) as exc_info:
            GifConfig(height=-100)

        assert "height" in str(exc_info.value).lower()

    def test_zero_height_raises_error(self) -> None:
        """❌ Test that zero height raises error."""
        with pytest.raises(InvalidConfigurationError) as exc_info:
            GifConfig(height=0)

        assert "height" in str(exc_info.value).lower()
