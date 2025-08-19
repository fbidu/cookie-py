"""Test cookiecutter template generation and validation."""

import json
import subprocess
import tempfile
from pathlib import Path

import pytest


def test_cookiecutter_generation_default():
    """Test that cookiecutter generates project with default values."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Generate project
        result = subprocess.run([
            "cookiecutter", ".", "--no-input", "--output-dir", str(temp_path)
        ], capture_output=True, text=True, cwd=Path(__file__).parent.parent)
        
        assert result.returncode == 0, f"Cookiecutter failed: {result.stderr}"
        
        # Check generated project exists
        project_dir = temp_path / "my-awesome-project"
        assert project_dir.exists()
        
        # Check essential files exist
        essential_files = [
            "pyproject.toml",
            "README.md",
            ".pre-commit-config.yaml",
            "tests/__init__.py",
            "tests/test_my_awesome_project.py",
            "my_awesome_project/__main__.py",
            "conftest.py",
        ]
        
        for file_path in essential_files:
            assert (project_dir / file_path).exists(), f"Missing file: {file_path}"


def test_cookiecutter_generation_custom_values():
    """Test cookiecutter generation with custom values."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create config with custom values
        config = {
            "project_name": "Test Custom Project",
            "description": "This is a test project",
            "python_version": "3.13"
        }
        
        config_file = temp_path / "config.json"
        with config_file.open("w") as f:
            json.dump(config, f)
        
        # Generate project
        result = subprocess.run([
            "cookiecutter", ".", "--no-input", 
            "--config-file", str(config_file),
            "--output-dir", str(temp_path)
        ], capture_output=True, text=True, cwd=Path(__file__).parent.parent)
        
        assert result.returncode == 0, f"Cookiecutter failed: {result.stderr}"
        
        project_dir = temp_path / "test-custom-project"
        assert project_dir.exists()
        
        # Check pyproject.toml has custom values
        pyproject = project_dir / "pyproject.toml"
        content = pyproject.read_text()
        assert 'name = "test-custom-project"' in content
        assert 'description = "This is a test project"' in content
        assert 'requires-python = ">=3.13"' in content
        assert 'target-version = "py313"' in content


def test_generated_project_structure():
    """Test that generated project has correct structure."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        result = subprocess.run([
            "cookiecutter", ".", "--no-input", "--output-dir", str(temp_path)
        ], capture_output=True, text=True, cwd=Path(__file__).parent.parent)
        
        assert result.returncode == 0
        
        project_dir = temp_path / "my-awesome-project"
        
        # Check directory structure
        assert (project_dir / "my_awesome_project").is_dir()
        assert (project_dir / "tests").is_dir()
        assert (project_dir / ".github" / "workflows").is_dir()
        
        # Check workflow files
        workflows = list((project_dir / ".github" / "workflows").glob("*.yml"))
        workflow_names = [w.name for w in workflows]
        assert "test.yml" in workflow_names
        assert "pre-commit.yml" in workflow_names


def test_generated_pyproject_toml_valid():
    """Test that generated pyproject.toml is valid TOML."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        result = subprocess.run([
            "cookiecutter", ".", "--no-input", "--output-dir", str(temp_path)
        ], capture_output=True, text=True, cwd=Path(__file__).parent.parent)
        
        assert result.returncode == 0
        
        project_dir = temp_path / "my-awesome-project"
        pyproject_file = project_dir / "pyproject.toml"
        
        # Try to parse as TOML
        import tomllib
        with pyproject_file.open("rb") as f:
            config = tomllib.load(f)
        
        # Check essential sections exist
        assert "project" in config
        assert "build-system" in config
        assert "tool" in config
        assert "ruff" in config["tool"]
        assert "pytest" in config["tool"]
        assert "pyright" in config["tool"]


def test_generated_project_dependencies_install():
    """Test that generated project dependencies can be installed."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        result = subprocess.run([
            "cookiecutter", ".", "--no-input", "--output-dir", str(temp_path)
        ], capture_output=True, text=True, cwd=Path(__file__).parent.parent)
        
        assert result.returncode == 0
        
        project_dir = temp_path / "my-awesome-project"
        
        # Try to install dependencies
        result = subprocess.run([
            "uv", "sync", "--dev"
        ], capture_output=True, text=True, cwd=project_dir)
        
        assert result.returncode == 0, f"uv sync failed: {result.stderr}"
        
        # Check that uv.lock was created
        assert (project_dir / "uv.lock").exists()


@pytest.mark.slow
def test_generated_project_quality_checks():
    """Test that generated project passes quality checks."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        result = subprocess.run([
            "cookiecutter", ".", "--no-input", "--output-dir", str(temp_path)
        ], capture_output=True, text=True, cwd=Path(__file__).parent.parent)
        
        assert result.returncode == 0
        
        project_dir = temp_path / "my-awesome-project"
        
        # Install dependencies
        subprocess.run(["uv", "sync", "--dev"], cwd=project_dir, check=True)
        
        # Run ruff check
        result = subprocess.run([
            "uv", "run", "ruff", "check", "."
        ], capture_output=True, text=True, cwd=project_dir)
        assert result.returncode == 0, f"Ruff check failed: {result.stdout}\n{result.stderr}"
        
        # Run ruff format check
        result = subprocess.run([
            "uv", "run", "ruff", "format", "--check", "."
        ], capture_output=True, text=True, cwd=project_dir)
        assert result.returncode == 0, f"Ruff format check failed: {result.stdout}\n{result.stderr}"
        
        # Run pyright
        result = subprocess.run([
            "uv", "run", "pyright"
        ], capture_output=True, text=True, cwd=project_dir)
        assert result.returncode == 0, f"Pyright failed: {result.stdout}\n{result.stderr}"
        
        # Run pytest
        result = subprocess.run([
            "uv", "run", "pytest", "-v"
        ], capture_output=True, text=True, cwd=project_dir)
        assert result.returncode == 0, f"Pytest failed: {result.stdout}\n{result.stderr}"