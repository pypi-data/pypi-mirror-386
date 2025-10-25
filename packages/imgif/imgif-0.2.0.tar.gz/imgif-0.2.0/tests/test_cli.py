"""
🧪 Unit tests for the CLI

This module tests the command-line interface functionality,
including argument parsing and option handling.
"""

from pathlib import Path

from click.testing import CliRunner

from img2gif.cli import main


class TestCLI:
    """Test suite for CLI 💻"""

    def test_cli_basic_conversion(self, sample_images_dir: Path, temp_dir: Path) -> None:
        """✅ Test basic CLI conversion."""
        runner = CliRunner()
        output_path = temp_dir / "cli_output.gif"

        result = runner.invoke(main, [str(sample_images_dir), str(output_path)])

        assert result.exit_code == 0
        assert output_path.exists()

    def test_cli_with_duration(self, sample_images_dir: Path, temp_dir: Path) -> None:
        """✅ Test CLI with custom duration."""
        runner = CliRunner()
        output_path = temp_dir / "cli_duration.gif"

        result = runner.invoke(
            main, [str(sample_images_dir), str(output_path), "--duration", "0.5"]
        )

        assert result.exit_code == 0
        assert output_path.exists()

    def test_cli_with_fps(self, sample_images_dir: Path, temp_dir: Path) -> None:
        """✅ Test CLI with FPS option."""
        runner = CliRunner()
        output_path = temp_dir / "cli_fps.gif"

        result = runner.invoke(main, [str(sample_images_dir), str(output_path), "--fps", "10"])

        assert result.exit_code == 0
        assert output_path.exists()

    def test_cli_with_loop(self, sample_images_dir: Path, temp_dir: Path) -> None:
        """✅ Test CLI with loop count."""
        runner = CliRunner()
        output_path = temp_dir / "cli_loop.gif"

        result = runner.invoke(main, [str(sample_images_dir), str(output_path), "--loop", "3"])

        assert result.exit_code == 0
        assert output_path.exists()

    def test_cli_with_quality(self, sample_images_dir: Path, temp_dir: Path) -> None:
        """✅ Test CLI with quality option."""
        runner = CliRunner()
        output_path = temp_dir / "cli_quality.gif"

        result = runner.invoke(main, [str(sample_images_dir), str(output_path), "--quality", "95"])

        assert result.exit_code == 0
        assert output_path.exists()

    def test_cli_with_optimize(self, sample_images_dir: Path, temp_dir: Path) -> None:
        """✅ Test CLI with optimize flag."""
        runner = CliRunner()
        output_path = temp_dir / "cli_optimize.gif"

        result = runner.invoke(main, [str(sample_images_dir), str(output_path), "--optimize"])

        assert result.exit_code == 0
        assert output_path.exists()

    def test_cli_with_width(self, sample_images_dir: Path, temp_dir: Path) -> None:
        """✅ Test CLI with width option."""
        runner = CliRunner()
        output_path = temp_dir / "cli_width.gif"

        result = runner.invoke(main, [str(sample_images_dir), str(output_path), "--width", "50"])

        assert result.exit_code == 0
        assert output_path.exists()

    def test_cli_with_height(self, sample_images_dir: Path, temp_dir: Path) -> None:
        """✅ Test CLI with height option."""
        runner = CliRunner()
        output_path = temp_dir / "cli_height.gif"

        result = runner.invoke(main, [str(sample_images_dir), str(output_path), "--height", "50"])

        assert result.exit_code == 0
        assert output_path.exists()

    def test_cli_with_multiple_options(self, sample_images_dir: Path, temp_dir: Path) -> None:
        """✅ Test CLI with multiple options combined."""
        runner = CliRunner()
        output_path = temp_dir / "cli_combined.gif"

        result = runner.invoke(
            main,
            [
                str(sample_images_dir),
                str(output_path),
                "--fps",
                "10",
                "--loop",
                "3",
                "--width",
                "50",
                "--optimize",
            ],
        )

        assert result.exit_code == 0
        assert output_path.exists()

    def test_cli_with_verbose(self, sample_images_dir: Path, temp_dir: Path) -> None:
        """✅ Test CLI with verbose flag."""
        runner = CliRunner()
        output_path = temp_dir / "cli_verbose.gif"

        result = runner.invoke(main, [str(sample_images_dir), str(output_path), "--verbose"])

        assert result.exit_code == 0
        assert output_path.exists()
        assert "Configuration" in result.output

    def test_cli_nonexistent_input(self, temp_dir: Path) -> None:
        """❌ Test CLI with nonexistent input path."""
        runner = CliRunner()
        output_path = temp_dir / "output.gif"
        nonexistent = temp_dir / "nonexistent"

        result = runner.invoke(main, [str(nonexistent), str(output_path)])

        assert result.exit_code != 0

    def test_cli_help(self) -> None:
        """✅ Test CLI help message."""
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])

        assert result.exit_code == 0
        assert "Convert a sequence of images" in result.output
        assert "INPUT_PATH" in result.output
        assert "OUTPUT_PATH" in result.output
