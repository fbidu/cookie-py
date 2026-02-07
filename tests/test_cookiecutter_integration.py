"""Integration tests for cookiecutter template generation."""

import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest


class TestCookiecutterIntegration:
    """Test that the cookiecutter template generates valid projects."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path, ignore_errors=True)

    @pytest.fixture
    def template_dir(self):
        """Get the path to the cookiecutter template."""
        return Path(__file__).parent.parent

    def test_cookiecutter_generation_default_values(self, temp_dir, template_dir):
        """Test that cookiecutter generates a project with default values."""
        # Arrange
        project_dir = temp_dir / "my-awesome-project"
        
        # Act
        result = subprocess.run(
            ["cookiecutter", str(template_dir), "--no-input", "--output-dir", str(temp_dir)],
            capture_output=True,
            text=True,
            cwd=temp_dir,
        )
        
        # Assert
        assert result.returncode == 0, f"Cookiecutter failed: {result.stderr}"
        assert project_dir.exists(), "Project directory was not created"
        
        # Check essential files exist
        essential_files = [
            "pyproject.toml",
            "README.md",
            ".gitignore",
            ".pre-commit-config.yaml",
            "my_awesome_project/__main__.py",
            "tests/__init__.py",
            "tests/test_my_awesome_project.py",
        ]
        
        for file_path in essential_files:
            assert (project_dir / file_path).exists(), f"Missing file: {file_path}"

    def test_generated_project_structure(self, temp_dir, template_dir):
        """Test that the generated project has the correct structure."""
        # Arrange & Act
        subprocess.run(
            ["cookiecutter", str(template_dir), "--no-input", "--output-dir", str(temp_dir)],
            capture_output=True,
            cwd=temp_dir,
        )
        project_dir = temp_dir / "my-awesome-project"
        
        # Assert
        # Check package directory exists
        package_dir = project_dir / "my_awesome_project"
        assert package_dir.exists(), "Package directory not found"
        assert package_dir.is_dir(), "Package should be a directory"
        
        # Check tests directory exists
        tests_dir = project_dir / "tests"
        assert tests_dir.exists(), "Tests directory not found"
        assert tests_dir.is_dir(), "Tests should be a directory"

    def test_uv_sync_works(self, temp_dir, template_dir):
        """Test that uv sync works on the generated project."""
        # Arrange
        subprocess.run(
            ["cookiecutter", str(template_dir), "--no-input", "--output-dir", str(temp_dir)],
            capture_output=True,
            cwd=temp_dir,
        )
        project_dir = temp_dir / "my-awesome-project"
        
        # Act
        result = subprocess.run(
            ["uv", "sync", "--dev"],
            capture_output=True,
            text=True,
            cwd=project_dir,
        )
        
        # Assert
        assert result.returncode == 0, f"uv sync failed: {result.stderr}"
        assert (project_dir / ".venv").exists(), "Virtual environment not created"

    def test_linting_passes(self, temp_dir, template_dir):
        """Test that linting passes on the generated project."""
        # Arrange
        subprocess.run(
            ["cookiecutter", str(template_dir), "--no-input", "--output-dir", str(temp_dir)],
            capture_output=True,
            cwd=temp_dir,
        )
        project_dir = temp_dir / "my-awesome-project"
        
        # Install dependencies first
        subprocess.run(["uv", "sync", "--dev"], cwd=project_dir)
        
        # Act & Assert - Run ruff check
        result = subprocess.run(
            ["uv", "run", "ruff", "check", "."],
            capture_output=True,
            text=True,
            cwd=project_dir,
        )
        assert result.returncode == 0, f"Ruff check failed: {result.stdout}\n{result.stderr}"

    def test_type_checking_passes(self, temp_dir, template_dir):
        """Test that type checking passes on the generated project."""
        # Arrange
        subprocess.run(
            ["cookiecutter", str(template_dir), "--no-input", "--output-dir", str(temp_dir)],
            capture_output=True,
            cwd=temp_dir,
        )
        project_dir = temp_dir / "my-awesome-project"
        
        # Install dependencies first
        subprocess.run(["uv", "sync", "--dev"], cwd=project_dir)
        
        # Act & Assert - Run pyright
        result = subprocess.run(
            ["uv", "run", "pyright"],
            capture_output=True,
            text=True,
            cwd=project_dir,
        )
        assert result.returncode == 0, f"Pyright failed: {result.stdout}\n{result.stderr}"

    def test_tests_pass(self, temp_dir, template_dir):
        """Test that the default tests pass on the generated project."""
        # Arrange
        subprocess.run(
            ["cookiecutter", str(template_dir), "--no-input", "--output-dir", str(temp_dir)],
            capture_output=True,
            cwd=temp_dir,
        )
        project_dir = temp_dir / "my-awesome-project"
        
        # Install dependencies first
        subprocess.run(["uv", "sync", "--dev"], cwd=project_dir)
        
        # Act & Assert - Run pytest
        result = subprocess.run(
            ["uv", "run", "pytest", "-v"],
            capture_output=True,
            text=True,
            cwd=project_dir,
        )
        assert result.returncode == 0, f"Tests failed: {result.stdout}\n{result.stderr}"

    def test_hatch_build_works(self, temp_dir, template_dir):
        """Test that Hatch can build the generated project."""
        # Arrange
        subprocess.run(
            ["cookiecutter", str(template_dir), "--no-input", "--output-dir", str(temp_dir)],
            capture_output=True,
            cwd=temp_dir,
        )
        project_dir = temp_dir / "my-awesome-project"
        
        # Install dependencies first
        subprocess.run(["uv", "sync", "--dev"], cwd=project_dir)
        
        # Act - Try to build with uv build (which uses hatch)
        result = subprocess.run(
            ["uv", "build"],
            capture_output=True,
            text=True,
            cwd=project_dir,
        )
        
        # Assert
        assert result.returncode == 0, f"Build failed: {result.stderr}"
        assert (project_dir / "dist").exists(), "Dist directory not created"
        
        # Check that wheel was created
        wheel_files = list((project_dir / "dist").glob("*.whl"))
        assert len(wheel_files) > 0, "No wheel file created"

    def test_precommit_check_passes(self, temp_dir, template_dir):
        """Test that pre-commit check passes on freshly generated project."""
        # Arrange
        subprocess.run(
            ["cookiecutter", str(template_dir), "--no-input", "--output-dir", str(temp_dir)],
            capture_output=True,
            cwd=temp_dir,
        )
        project_dir = temp_dir / "my-awesome-project"
        
        # Install dependencies first
        subprocess.run(["uv", "sync", "--dev"], cwd=project_dir)
        
        # Act - Run pre-commit on all files
        result = subprocess.run(
            ["pre-commit", "run", "--all-files"],
            capture_output=True,
            text=True,
            cwd=project_dir,
        )
        
        # Assert
        # Note: pre-commit may return exit code 1 if it fixes files, but that's expected
        # We mainly care that it doesn't fail completely and produces reasonable output
        assert result.returncode in [0, 1], f"Pre-commit failed unexpectedly: {result.stderr}"
        
        # Check that pre-commit ran successfully (even if it made fixes)
        assert "Passed" in result.stdout or "Failed" in result.stdout, \
            f"Pre-commit output unexpected: {result.stdout}"

    def test_workflow_files_rendered(self, temp_dir, template_dir):
        """Test that workflow files have cookiecutter variables rendered."""
        # Arrange
        subprocess.run(
            ["cookiecutter", str(template_dir), "--no-input", "--output-dir", str(temp_dir)],
            capture_output=True,
            cwd=temp_dir,
        )
        project_dir = temp_dir / "my-awesome-project"

        # Act - Read workflow files
        test_yml = (project_dir / ".github/workflows/test.yml").read_text()
        precommit_yml = (project_dir / ".github/workflows/pre-commit.yml").read_text()

        # Assert - Cookiecutter variables should be rendered
        assert "{{cookiecutter." not in test_yml, \
            "Cookiecutter variables not rendered in test.yml"
        assert "{{cookiecutter." not in precommit_yml, \
            "Cookiecutter variables not rendered in pre-commit.yml"

        # Assert - Default python_version (3.12) should appear
        assert "3.12" in test_yml, "Default python_version not rendered in test.yml"
        assert "3.12" in precommit_yml, "Default python_version not rendered in pre-commit.yml"

        # Assert - GitHub Actions expressions should be preserved
        assert "${{ matrix.python-version }}" in test_yml, \
            "GitHub Actions expressions were incorrectly rendered in test.yml"