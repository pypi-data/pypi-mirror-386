"""
🧪 Unit tests for the ImageToGifConverter class

This module contains comprehensive tests for the core converter functionality,
including image loading, validation, error handling, and GIF generation.
"""

from pathlib import Path

import pytest

from img2gif import ImageToGifConverter
from img2gif.exceptions import (
    ConversionError,
    ImageLoadError,
    InvalidInputError,
    NoImagesFoundError,
)


class TestImageToGifConverter:
    """Test suite for ImageToGifConverter class 🧪"""

    def test_converter_initialization(self) -> None:
        """✅ Test that converter can be initialized."""
        converter = ImageToGifConverter()
        assert converter is not None
        assert converter.console is not None

    def test_get_supported_formats(self) -> None:
        """✅ Test that supported formats are returned correctly."""
        converter = ImageToGifConverter()
        formats = converter.get_supported_formats()

        # Check common formats are included
        assert ".png" in formats
        assert ".jpg" in formats
        assert ".jpeg" in formats
        assert ".gif" in formats
        assert ".bmp" in formats

        # Check it's a set (no duplicates)
        assert isinstance(formats, set)

    def test_convert_directory_basic(self, sample_images_dir: Path, output_path: Path) -> None:
        """✅ Test basic conversion from directory of images."""
        converter = ImageToGifConverter()
        converter.convert(sample_images_dir, output_path)

        # Check output file was created
        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_convert_single_file(self, single_image: Path, output_path: Path) -> None:
        """✅ Test conversion from single image file."""
        converter = ImageToGifConverter()
        converter.convert(single_image, output_path)

        # Check output file was created
        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_convert_with_custom_duration(self, sample_images_dir: Path, output_path: Path) -> None:
        """✅ Test conversion with custom duration parameter."""
        converter = ImageToGifConverter()
        converter.convert(sample_images_dir, output_path, duration=0.5)

        assert output_path.exists()

    def test_convert_with_duration_list(self, sample_images_dir: Path, output_path: Path) -> None:
        """✅ Test conversion with list of durations per frame."""
        converter = ImageToGifConverter()
        # Different duration for each frame
        converter.convert(sample_images_dir, output_path, duration=[0.5, 1.0, 0.3])

        assert output_path.exists()

    def test_convert_with_loop_count(self, sample_images_dir: Path, output_path: Path) -> None:
        """✅ Test conversion with specific loop count."""
        converter = ImageToGifConverter()
        converter.convert(sample_images_dir, output_path, loop=3)

        assert output_path.exists()

    def test_convert_creates_output_directory(
        self, sample_images_dir: Path, temp_dir: Path
    ) -> None:
        """✅ Test that output directory is created if it doesn't exist."""
        converter = ImageToGifConverter()
        nested_output = temp_dir / "nested" / "output" / "test.gif"

        converter.convert(sample_images_dir, nested_output)

        assert nested_output.exists()
        assert nested_output.parent.exists()

    def test_convert_mixed_files_directory(self, mixed_files_dir: Path, output_path: Path) -> None:
        """✅ Test conversion from directory with mixed file types."""
        converter = ImageToGifConverter()
        converter.convert(mixed_files_dir, output_path)

        # Should only process image files
        assert output_path.exists()

    def test_convert_various_formats(self, various_formats_dir: Path, output_path: Path) -> None:
        """✅ Test conversion with various image formats."""
        converter = ImageToGifConverter()
        converter.convert(various_formats_dir, output_path)

        assert output_path.exists()

    def test_invalid_input_path(self, output_path: Path) -> None:
        """❌ Test that invalid input path raises InvalidInputError."""
        converter = ImageToGifConverter()
        nonexistent_path = Path("/nonexistent/path/to/images")

        with pytest.raises(InvalidInputError) as exc_info:
            converter.convert(nonexistent_path, output_path)

        assert "does not exist" in str(exc_info.value).lower()

    def test_empty_directory(self, empty_dir: Path, output_path: Path) -> None:
        """❌ Test that empty directory raises NoImagesFoundError."""
        converter = ImageToGifConverter()

        with pytest.raises(NoImagesFoundError) as exc_info:
            converter.convert(empty_dir, output_path)

        assert "no valid images" in str(exc_info.value).lower()

    def test_unsupported_file_format(self, temp_dir: Path, output_path: Path) -> None:
        """❌ Test that unsupported file format raises InvalidInputError."""
        converter = ImageToGifConverter()
        text_file = temp_dir / "test.txt"
        text_file.write_text("Not an image")

        with pytest.raises(InvalidInputError) as exc_info:
            converter.convert(text_file, output_path)

        assert "not a supported image format" in str(exc_info.value).lower()

    def test_corrupted_image(self, corrupted_image_dir: Path, output_path: Path) -> None:
        """❌ Test that corrupted image raises ImageLoadError."""
        converter = ImageToGifConverter()

        with pytest.raises(ImageLoadError) as exc_info:
            converter.convert(corrupted_image_dir, output_path)

        assert "failed to load" in str(exc_info.value).lower()

    def test_get_image_files_sorting(self, sample_images_dir: Path) -> None:
        """✅ Test that image files are returned in sorted order."""
        converter = ImageToGifConverter()
        files = converter._get_image_files(sample_images_dir)

        # Files should be sorted
        file_names = [f.name for f in files]
        assert file_names == sorted(file_names)

    def test_get_image_files_single_file(self, single_image: Path) -> None:
        """✅ Test getting image files from single file path."""
        converter = ImageToGifConverter()
        files = converter._get_image_files(single_image)

        assert len(files) == 1
        assert files[0] == single_image

    def test_load_images(self, sample_images_dir: Path) -> None:
        """✅ Test that images are loaded correctly."""
        converter = ImageToGifConverter()
        files = converter._get_image_files(sample_images_dir)
        images = converter._load_images(files)

        # Should have loaded 3 images
        assert len(images) == 3

        # Each should be a PIL Image object
        for img in images:
            assert img is not None
            assert hasattr(img, "size")  # PIL Image has .size attribute
            assert img.mode in ("RGB", "P")  # Should be converted to RGB or P mode


@pytest.mark.unit
class TestExceptions:
    """Test suite for custom exceptions 🚨"""

    def test_invalid_input_error(self) -> None:
        """✅ Test InvalidInputError can be raised and caught."""
        with pytest.raises(InvalidInputError):
            raise InvalidInputError("Test error")

    def test_no_images_found_error(self) -> None:
        """✅ Test NoImagesFoundError can be raised and caught."""
        with pytest.raises(NoImagesFoundError):
            raise NoImagesFoundError("Test error")

    def test_image_load_error(self) -> None:
        """✅ Test ImageLoadError can be raised and caught."""
        with pytest.raises(ImageLoadError):
            raise ImageLoadError("Test error")

    def test_conversion_error(self) -> None:
        """✅ Test ConversionError can be raised and caught."""
        with pytest.raises(ConversionError):
            raise ConversionError("Test error")
