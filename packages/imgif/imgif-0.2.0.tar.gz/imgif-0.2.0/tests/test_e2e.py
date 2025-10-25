"""
🧪 End-to-end integration tests

This module contains tests for complete workflows, testing
the entire pipeline from image loading to GIF creation.
"""

from pathlib import Path

import pytest
from PIL import Image

from img2gif import GifConfig, ImageToGifConverter


@pytest.mark.e2e
class TestE2EWorkflows:
    """End-to-end test suite 🎬"""

    def test_directory_to_gif_workflow(self, sample_images_dir: Path, output_path: Path) -> None:
        """🎬 Test complete workflow: directory of images to GIF."""
        converter = ImageToGifConverter()
        converter.convert(sample_images_dir, output_path, duration=0.5)

        # Verify GIF was created and is valid
        assert output_path.exists()
        assert output_path.stat().st_size > 0

        # Verify we can read the GIF back
        with Image.open(output_path) as gif:
            assert gif is not None
            assert gif.size[0] > 0 and gif.size[1] > 0  # Has dimensions

    def test_single_image_to_gif_workflow(self, single_image: Path, output_path: Path) -> None:
        """🎬 Test complete workflow: single image to GIF."""
        converter = ImageToGifConverter()
        converter.convert(single_image, output_path)

        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_various_formats_to_gif_workflow(
        self, various_formats_dir: Path, output_path: Path
    ) -> None:
        """🎬 Test workflow with various image formats."""
        converter = ImageToGifConverter()
        converter.convert(various_formats_dir, output_path, duration=0.3)

        assert output_path.exists()
        assert output_path.stat().st_size > 0

        # Verify GIF contains multiple frames
        with Image.open(output_path) as gif:
            assert gif is not None

    def test_config_based_workflow_with_resize(
        self, sample_images_dir: Path, output_path: Path
    ) -> None:
        """🎬 Test config-based workflow with resizing."""
        config = GifConfig(
            duration=0.5,
            loop=3,
            width=50,
            height=50,
            maintain_aspect_ratio=False,
        )

        converter = ImageToGifConverter()
        converter.convert_with_config(sample_images_dir, output_path, config)

        assert output_path.exists()
        assert output_path.stat().st_size > 0

        # Verify the GIF has the expected dimensions
        with Image.open(output_path) as gif:
            width, height = gif.size
            assert width == 50
            assert height == 50

    def test_config_based_workflow_with_fps(
        self, sample_images_dir: Path, output_path: Path
    ) -> None:
        """🎬 Test config-based workflow using FPS."""
        config = GifConfig(fps=10, loop=0, quality=90)

        converter = ImageToGifConverter()
        converter.convert_with_config(sample_images_dir, output_path, config)

        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_optimized_gif_workflow(self, sample_images_dir: Path, output_path: Path) -> None:
        """🎬 Test workflow with optimization enabled."""
        config = GifConfig(duration=0.5, optimize=True, quality=75)

        converter = ImageToGifConverter()
        converter.convert_with_config(sample_images_dir, output_path, config)

        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_resize_with_aspect_ratio_workflow(
        self, sample_images_dir: Path, output_path: Path
    ) -> None:
        """🎬 Test workflow with aspect ratio-preserving resize."""
        config = GifConfig(width=80, maintain_aspect_ratio=True)

        converter = ImageToGifConverter()
        converter.convert_with_config(sample_images_dir, output_path, config)

        assert output_path.exists()
        assert output_path.stat().st_size > 0

        # Verify dimensions
        with Image.open(output_path) as gif:
            width, height = gif.size
            assert width == 80
            # Height should be scaled proportionally (original is 100x100)
            assert height == 80

    def test_nested_output_directory_workflow(
        self, sample_images_dir: Path, temp_dir: Path
    ) -> None:
        """🎬 Test workflow with nested output directory creation."""
        nested_output = temp_dir / "level1" / "level2" / "output.gif"

        converter = ImageToGifConverter()
        converter.convert(sample_images_dir, nested_output)

        assert nested_output.exists()
        assert nested_output.parent.exists()

    def test_mixed_files_directory_workflow(self, mixed_files_dir: Path, output_path: Path) -> None:
        """🎬 Test workflow with directory containing mixed file types."""
        converter = ImageToGifConverter()
        converter.convert(mixed_files_dir, output_path)

        # Should successfully create GIF ignoring non-image files
        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_duration_list_workflow(self, sample_images_dir: Path, output_path: Path) -> None:
        """🎬 Test workflow with different duration per frame."""
        converter = ImageToGifConverter()
        # Different duration for each of the 3 frames
        converter.convert(sample_images_dir, output_path, duration=[0.5, 1.0, 0.3])

        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_high_quality_large_gif_workflow(
        self, sample_images_dir: Path, output_path: Path
    ) -> None:
        """🎬 Test workflow with high quality settings."""
        config = GifConfig(
            duration=0.1,
            quality=100,
            width=200,
            height=200,
            loop=1,
        )

        converter = ImageToGifConverter()
        converter.convert_with_config(sample_images_dir, output_path, config)

        assert output_path.exists()
        # High quality should result in larger file
        assert output_path.stat().st_size > 1000
